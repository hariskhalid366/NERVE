"""Neutral recorder/evaluator for REAL agent runs; no model invoked by this script.

Export blind questions and answer keys. Agent harnesses submit JSONL run logs with
actual input/output token usage supplied by their provider. Score paired arms.

Usage:
 python -m benchmark.agent_eval export --dir benchmark/results/agent_trials
 python -m benchmark.agent_eval score --runs benchmark/results/agent_trials/runs.jsonl
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
from statistics import median
from .smoke import HERE

ARMS={'no_memory','flat_notes','nerve'}

def gold_cases():
    items=json.loads((HERE/'scenarios.json').read_text())
    answers={}
    for i,item in enumerate(items):
        for n,query in enumerate(item['queries']):
            key=f'T{i:02d}Q{n}'
            answers[key]={'case_id':key,'query':query,'kind':['label','alias','incident','paraphrase'][n],
                          'target_id':item['id'],'answer':item['fact']}
    return answers

def export(out_dir):
    out_dir.mkdir(parents=True,exist_ok=True)
    gold=gold_cases()
    public=[{'case_id':v['case_id'],'query':v['query'],'kind':v['kind']} for v in gold.values()]
    (out_dir/'agent_prompts.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in public))
    # Keys must not be shown to the agent being evaluated.
    (out_dir/'gold_private.json').write_text(json.dumps(gold,indent=2,ensure_ascii=False)+'\n')
    (out_dir/'runs.example.jsonl').write_text(json.dumps({
        'case_id':'T00Q0', 'arm':'nerve','model':'example-model','seed':0,
        'target_id':'billing:settlement','answer':'We settled on a 47-second retry window after replay tests.',
        'input_tokens':500,'output_tokens':75,'latency_ms':1200,
        'agent_a':'model-a','agent_b':'model-b','handoff_completed':True,
        'source':'EXAMPLE_DO_NOT_SCORE_AS_REAL'
    })+'\n')
    return len(public)

def wilson(k,n,z=1.96):
    if n==0:return [None,None]
    p=k/n
    mid=(p+z*z/(2*n))/(1+z*z/n)
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return [round(max(0,mid-half),4),round(min(1,mid+half),4)]

def norm(text):
    return ' '.join(str(text or '').casefold().strip().split())

def evaluate(path):
    gold=gold_cases()
    lines=[json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]
    seen=set(); enriched=[]
    for line in lines:
        if line.get('source')=='EXAMPLE_DO_NOT_SCORE_AS_REAL':
            raise ValueError('Example placeholder run is not evidence. Record actual agent results.')
        if line.get('case_id') not in gold:raise ValueError(f"Unknown case_id: {line.get('case_id')}")
        if line.get('arm') not in ARMS:raise ValueError(f"Unknown arm: {line.get('arm')}")
        for key in ('model','seed','input_tokens','output_tokens','latency_ms','target_id','answer'):
            if key not in line:raise ValueError(f"Missing actual trial field: {key}")
        for key in ('input_tokens','output_tokens','latency_ms'):
            if not isinstance(line[key],(int,float)) or isinstance(line[key],bool) or line[key]<0:
                raise ValueError(f'Invalid measured field {key}')
        scenario=gold[line['case_id']]
        group=(line['model'],line['seed'],line['case_id'],line['arm'])
        if group in seen:raise ValueError('Duplicate agent trial for model/seed/case/arm')
        seen.add(group)
        target_ok=line['target_id']==scenario['target_id']
        fact_ok=norm(line['answer'])==norm(scenario['answer'])
        enriched.append({**line,'kind':scenario['kind'],'target_correct':target_ok,
                         'context_recovery_correct':target_ok and fact_ok,
                         'cross_agent_correct':(target_ok and fact_ok and line.get('handoff_completed') is True
                                                and bool(line.get('agent_a')) and bool(line.get('agent_b'))
                                                and line['agent_a']!=line['agent_b'])})
    grouped=defaultdict(list)
    for r in enriched:grouped[(r['model'],r['arm'])].append(r)
    stats={}
    for (model,arm), rows in sorted(grouped.items()):
        n=len(rows)
        successes=sum(r['context_recovery_correct'] for r in rows)
        handed=[r for r in rows if r.get('handoff_completed') is True]
        cross=sum(r['cross_agent_correct'] for r in handed)
        stats[f'{model}|{arm}']={
            'trials':n,
            'target_top1':round(sum(r['target_correct'] for r in rows)/n,4),
            'target_95pct_wilson':wilson(sum(r['target_correct'] for r in rows),n),
            'context_recovery_accuracy_strict':round(successes/n,4),
            'recovery_95pct_wilson':wilson(successes,n),
            'cross_agent_strict_accuracy':round(cross/len(handed),4) if handed else None,
            'cross_agent_trials':len(handed),
            'total_input_tokens':sum(r['input_tokens'] for r in rows),
            'total_output_tokens':sum(r['output_tokens'] for r in rows),
            'input_tokens_per_successful_task':round(sum(r['input_tokens'] for r in rows)/successes,2) if successes else None,
            'median_input_tokens':median(r['input_tokens'] for r in rows),
            'median_latency_ms':median(r['latency_ms'] for r in rows),
            'cases':sorted(r['case_id'] for r in rows),
        }
    # Paired comparisons require identical model+seed+case tuples.
    paired={}
    for model in sorted({r['model'] for r in enriched}):
        control=next((a for a in ('flat_notes','no_memory') if (model,a) in grouped),None)
        if not control or (model,'nerve') not in grouped: continue
        ctrl={(r['seed'],r['case_id']):r for r in grouped[(model,control)]}
        enabled={(r['seed'],r['case_id']):r for r in grouped[(model,'nerve')]}
        overlap=sorted(ctrl.keys() & enabled.keys())
        if not overlap:continue
        paired_ctrl=[ctrl[k] for k in overlap]
        paired_enabled=[enabled[k] for k in overlap]
        count=lambda rs:sum(r['context_recovery_correct'] for r in rs)
        ctrl_ok=count(paired_ctrl); enabled_ok=count(paired_enabled)
        control_tokens=sum(r['input_tokens'] for r in paired_ctrl)
        enabled_tokens=sum(r['input_tokens'] for r in paired_enabled)
        paired[model]={
            'control_arm':control,'n_paired':len(overlap),
            'control_recovery':round(ctrl_ok/len(overlap),4),
            'nerve_recovery':round(enabled_ok/len(overlap),4),
            'recovery_gain_pp':round(100*(enabled_ok-ctrl_ok)/len(overlap),2),
            'control_total_input_tokens':control_tokens,
            'nerve_total_input_tokens':enabled_tokens,
            'token_reduction_at_paired_task_count':round(1-enabled_tokens/control_tokens,4) if control_tokens else None,
            'control_input_tokens_per_success':round(control_tokens/ctrl_ok,2) if ctrl_ok else None,
            'nerve_input_tokens_per_success':round(enabled_tokens/enabled_ok,2) if enabled_ok else None,
            'caveat':'Token reduction is not efficiency improvement if quality is lower. Require quality parity/gain and coverage of all intended scenarios.'
        }
    return {'evaluation_type':'REAL_AGENTS_IF_AND_ONLY_IF_RUN_LOG_IS_GENUINE',
            'grading':'Exact canonical fact matching; semantically equivalent answers may score wrong; target ID must match.',
            'model_arm_stats':stats,'paired_comparisons':paired,
            'warning':'No LLM or provider usage collected by this evaluator. Caller is responsible for truthful run logs and blinding.'}

def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest='action',required=True)
    e=sub.add_parser('export');e.add_argument('--dir',default='benchmark/results/agent_trials')
    s=sub.add_parser('score');s.add_argument('--runs',required=True);s.add_argument('--output')
    a=p.parse_args()
    if a.action=='export':
        n=export(Path(a.dir))
        print(f'Exported {n} blind agent prompts and separate gold keys into {a.dir}')
    else:
        result=evaluate(Path(a.runs))
        print(json.dumps(result,indent=2))
        if a.output:Path(a.output).write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
