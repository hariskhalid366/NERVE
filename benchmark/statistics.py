"""Small exact, dependency-free statistical summaries of paired retrieval outcomes."""
from __future__ import annotations
import json
from pathlib import Path
from math import comb, sqrt

ROOT=Path(__file__).resolve().parents[1]


def wilson(k:int,n:int,z:float=1.9599639845)->list[float]:
    if n==0:return [0,0]
    p=k/n; d=1+z*z/n
    m=(p+z*z/(2*n))/d
    h=z*sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [round(100*(m-h),2),round(100*(m+h),2)]


def paired(a:list[bool],b:list[bool])->dict:
    n=len(a);nerve_only=sum(x and not y for x,y in zip(a,b));flat_only=sum(not x and y for x,y in zip(a,b));discordant=nerve_only+flat_only
    pval=min(1.0,2*sum(comb(discordant,i) for i in range(min(nerve_only,flat_only)+1))/2**discordant) if discordant else 1.0
    return {'cases':n,'nerve_correct':sum(a),'flat_correct':sum(b),
            'nerve_accuracy_pct':round(100*sum(a)/n,2),
            'flat_accuracy_pct':round(100*sum(b)/n,2),
            'nerve_wilson_95pct':wilson(sum(a),n),
            'flat_wilson_95pct':wilson(sum(b),n),
            'nerve_only_correct':nerve_only,'flat_only_correct':flat_only,
            'paired_exact_two_sided_p':round(pval,6),
            'caveat':'Repeated questions per target and hand-authored fixtures; significance does not imply generalization.'}


def main():
    chess=json.loads((ROOT/'benchmark/results/CHESS_PUBLIC_AUDIT.json').read_text())
    stress=json.loads((ROOT/'benchmark/results/CHESS_STRESS_V0_6.json').read_text())
    task=json.loads((ROOT/'benchmark/results/PUBLIC_RELEASE_AUDIT.json').read_text())['task_mini']
    out={
      'chess_original':paired([x['nerve_correct'] for x in chess['per_case']],[x['flat_correct'] for x in chess['per_case']]),
      'chess_stress':paired([x['nerve_correct'] for x in stress['positive']],[x['baseline_correct'] for x in stress['positive']]),
      'task_mini':paired([x['nerve_correct'] for x in task['queries']],[x['flat_correct'] for x in task['queries']]),
      'notes':['Wilson interval treats questions as independent and is optimistic when examples share targets.',
               'Chess original was used to tune earlier NERVE versions; not held out.',
               'Task mini is a separate code domain but is small and hand-authored.',
               'All are deterministic software retrieval tests, not end-to-end LLM agent benchmarks.']}
    path=ROOT/'benchmark/results/PAIRED_METRICS.json';path.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':main()
