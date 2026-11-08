"""Seeded, offline, repeated NERVE diagnostics.

This is a *retrieval-system* audit, not proof of agent understanding or 100%
accuracy.  Every trial uses a newly created SQLite database and fresh random
labels.  No network, model provider, or hidden answer data is used by NERVE.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import subprocess
import sys
import tempfile
from time import perf_counter

from nerve.core import Nerve
from nerve.core import tokens

ROOT = Path(__file__).resolve().parents[1]


def wilson(success: int, trials: int, z: float = 1.9599639845) -> list[float]:
    if not trials: return [0.0, 0.0]
    p = success/trials
    d=1+z*z/trials
    mid=(p+z*z/(2*trials))/d
    delta=z*math.sqrt(p*(1-p)/trials+z*z/(4*trials*trials))/d
    return [round(100*(mid-delta),2),round(100*(mid+delta),2)]


def percentile(a: list[float], pct: float) -> float:
    if not a: return 0.0
    a=sorted(a)
    return round(a[min(len(a)-1, math.ceil((pct/100)*len(a))-1)],3)


def sample(rng: random.Random, used: set[str], prefix: str) -> str:
    while True:
        key=prefix+''.join(rng.choice('abcdefghjkmnpqrstuvwxyz') for _ in range(12))
        if key not in used:
            used.add(key)
            return key


def setup_project(n: Nerve, rng: random.Random, n_targets: int) -> dict[str,dict]:
    used=set()
    items={}
    for i in range(n_targets):
        label=sample(rng,used,'module')
        alias=sample(rng,used,'nickname')
        marker=sample(rng,used,'incident')
        tid=f'object-{i:05d}'
        items[tid]={'label':label,'alias':alias,'marker':marker}
    order=list(items);rng.shuffle(order)
    for tid in order:
        v=items[tid]
        n.observe(tid,v['label'],kind='function',description='Internal stable component.',aliases=[v['alias']])
        n.event(tid,'verified-incident',f'The {v["marker"]} regression was diagnosed and fixed after an earlier failure.')
        n.remember(f'Source evidence named {v["marker"]}.',target_id=tid)
    return items


def fair_flat_rank(n: Nerve, query: str) -> str | None:
    """Simple full-record text search; includes IDs and exact keys fairly."""
    norm=query.strip().casefold()
    q=tokens(query)
    if not q:return None
    ranking=[]
    for r in n.conn.execute('SELECT * FROM targets'):
        alias_list=json.loads(r['aliases'])
        exact=norm in [r['target_id'].casefold(),r['label'].casefold(),*[x.casefold() for x in alias_list]]
        history=[e[0] for e in n.conn.execute('SELECT message FROM events WHERE target_id=?',(r['target_id'],))]
        history += [m[0] for m in n.conn.execute('SELECT text FROM memories WHERE target_id=?',(r['target_id'],))]
        combined=' '.join([r['target_id'],r['label'],r['source_path'],r['description'],r['aliases'],*history])
        overlap=len(q & tokens(combined))
        if exact or overlap: ranking.append((int(exact),overlap,r['target_id']))
    return sorted(ranking,key=lambda x:(-x[0],-x[1],x[2]))[0][2] if ranking else None


def run_retrieval_round(seed:int, n_targets:int) -> dict:
    rng=random.Random(seed)
    counts=Counter()
    errors=[]
    latencies=[]
    with tempfile.TemporaryDirectory(prefix='nerve-repeated-') as directory:
        with Nerve(directory) as n:
            items=setup_project(n,rng,n_targets)
            cases=[]
            for tid,v in items.items():
                cases.extend([
                    (tid,'exact_label',v['label']),
                    (tid,'exact_id',tid),
                    (tid,'alias',v['alias']),
                    (tid,'historical',f'Where was {v["marker"]} fixed?'),
                ])
            rng.shuffle(cases)
            for expected,kind,q in cases:
                t=perf_counter()
                pred=n.resolve(q)
                latencies.append((perf_counter()-t)*1000)
                top=pred['candidates'][0]['target_id'] if pred['candidates'] else None
                flat=fair_flat_rank(n,q)
                counts[kind+'_total']+=1
                counts[kind+'_nerve_correct']+=top==expected
                counts[kind+'_flat_correct']+=flat==expected
                if top != expected and len(errors)<15:
                    errors.append({'kind':kind,'query':q,'expected':expected,'predicted':top,'decision':pred['decision']})
            for i in range(max(10,n_targets//4)):
                q=sample(rng,set(),'phantom')+' '+sample(rng,set(),'unrelated')
                pred=n.resolve(q)
                counts['unsupported_total']+=1
                counts['unsupported_no_candidate']+=not bool(pred['candidates'])
                counts['unsupported_no_supported_decision']+=pred['decision']!='supported_candidate'
            # Collision: no candidate should be automatically considered safe to act upon.
            n.observe('collision-A','shared_collision','function',description='cache buffer conflict',aliases=['conflict handler'])
            n.observe('collision-B','shared_collision','function',description='cache buffer conflict',aliases=['conflict handler'])
            ambiguous=n.resolve('shared_collision')
            counts['ambiguous_total']+=1
            counts['ambiguous_flagged']+=ambiguous['decision']=='needs_confirmation'
            counts['unsafe_auto_actions']+=ambiguous['may_act_without_verification'] is True
            # Distinctive old incident after unrelated observations, still findable.
            older_tid=list(items)[0]
            marker=items[older_tid]['marker']
            n.observe('noise','noisy events')
            for j in range(250):
                n.event('noise','noise',f'New unrelated event {j}')
            after_noise=n.resolve(marker)
            counts['historical_after_noise_total']+=1
            counts['historical_after_noise_correct']+=bool(after_noise['candidates'] and after_noise['candidates'][0]['target_id']==older_tid)
            db_integrity=n.conn.execute('PRAGMA integrity_check').fetchone()[0]
            counts['sqlite_integrity_total']+=1
            counts['sqlite_integrity_ok']+=db_integrity=='ok'
        # Fresh process, not just another handle.
        code='import json,sys;from nerve.core import Nerve;from pathlib import Path\nwith Nerve(Path(sys.argv[1])) as n: print(json.dumps(n.resolve(sys.argv[2])))'
        sub=subprocess.run([sys.executable,'-c',code,directory,marker],cwd=ROOT,env=None,capture_output=True,text=True,timeout=12)
        ok=False
        if sub.returncode==0:
            p=json.loads(sub.stdout)
            ok=bool(p['candidates'] and p['candidates'][0]['target_id']==older_tid)
        counts['new_process_total']+=1
        counts['new_process_success']+=ok
        if not ok and len(errors)<15:errors.append({'kind':'new_process','stderr':sub.stderr[:250]})
    return {'seed':seed,'targets':n_targets,'counters':dict(counts),
            'latency_ms':{'p50':percentile(latencies,50),'p95':percentile(latencies,95),'p99':percentile(latencies,99)},
            'errors':errors}


def context_depth_probe(notes: int=160) -> dict:
    with tempfile.TemporaryDirectory(prefix='nerve-depth-') as td:
        with Nerve(td) as n:
            n.observe('target','Complicated subsystem')
            n.remember('unique-old-root-cause-copperoctopus',target_id='target')
            for i in range(notes): n.remember(f'New context note {i}',target_id='target')
            ctx=n.context('target',limit=12)
            persisted=n.conn.execute("SELECT COUNT(*) FROM memories WHERE target_id='target'").fetchone()[0]
            old_visible=any('unique-old-root-cause-copperoctopus' in x['text'] for x in ctx['memories'])
            result=n.resolve('copperoctopus')
            searched=n.search_evidence('copperoctopus',target_id='target')
            old_recovered=any('copperoctopus' in m['text'] for m in searched['results'])
            return {'target_id':'target','notes_inserted_after_old':notes,'records_persisted':persisted,
                'old_note_visible_in_default_context':old_visible,
                'old_note_retrieval_via_resolve_correct':bool(result['candidates'] and result['candidates'][0]['target_id']=='target'),
                'old_note_recovered_by_evidence_search':old_recovered,
                'limit':12,'note':'Old record may persist but is not present in bounded recent context; retrieval is a separate capability.'}


def semantic_probe() -> dict:
    # Gold mapping deliberately made from different words. This tests ability
    # to understand synonyms, not the mere matching of a unique marker.
    pairs=[
        ('parse','Parse FEN notation and validate board ranks','the routine that reads a compact chess-position string'),
        ('draw','Check game over status and stalemate','how the match knows nobody can make another legal turn'),
        ('save','Persist task records to JSON disk','the helper writing the to-do collection onto the hard drive'),
        ('auth','Authenticate session using credentials','where the system confirms a person is allowed to sign in'),
        ('clock','Calculate elapsed time and move deadline','which component decides how long the timer has left'),
        ('sort','Sort objects by priority and due date','the logic that arranges entries in deadline order'),
        ('cache','Cache recent API responses','where requests avoid repeatedly fetching the same information'),
        ('render','Render interface items to HTML','what draws the screen elements for the browser'),
    ]
    with tempfile.TemporaryDirectory(prefix='nerve-semantic-') as td:
        with Nerve(td) as n:
            for tid,desc,_ in pairs:n.observe(tid,tid,'function',desc)
            out=[]
            for tid,desc,q in pairs:
                p=n.resolve(q)
                candidate=p['candidates'][0]['target_id'] if p['candidates'] else None
                out.append({'query':q,'expected':tid,'predicted':candidate,'correct':candidate==tid})
    return {'total':len(out),'correct':sum(x['correct'] for x in out),'cases':out,
            'limitation':'Small hand-written out-of-vocabulary paraphrases; not an independent model benchmark.'}


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument('--rounds',type=int,default=10)
    ap.add_argument('--targets',type=int,default=40)
    ap.add_argument('--seed',type=int,default=20261108)
    ap.add_argument('--strict',action='store_true',help='Fail on deterministic invariant regressions; does not require semantic 100%%.')
    ap.add_argument('--output',default='benchmark/results/REPEATABILITY.json')
    args=ap.parse_args()
    if not 1 <= args.rounds <= 500:ap.error('rounds must be 1..500')
    if not 4 <= args.targets <= 500:ap.error('targets must be 4..500')
    start=perf_counter()
    results=[run_retrieval_round(args.seed+i*9973,args.targets) for i in range(args.rounds)]
    counters=Counter()
    for result in results:counters.update(result['counters'])
    summary={}
    for metric in ['exact_label','exact_id','alias','historical']:
        total=counters[metric+'_total']
        nerve=counters[metric+'_nerve_correct'];flat=counters[metric+'_flat_correct']
        summary[metric]={'nerve_correct':nerve,'flat_correct':flat,'total':total,'nerve_pct':round(100*nerve/total,2),'flat_pct':round(100*flat/total,2),'wilson_95_pct':wilson(nerve,total)}
    for metric,suffix in [('unsupported_no_candidate','unsupported_total'),('unsupported_no_supported_decision','unsupported_total'),('ambiguous_flagged','ambiguous_total'),('historical_after_noise_correct','historical_after_noise_total'),('new_process_success','new_process_total'),('sqlite_integrity_ok','sqlite_integrity_total')]:
        total=counters[suffix]; success=counters[metric]
        summary[metric]={'correct':success,'total':total,'pct':round(100*success/total,2),'wilson_95_pct':wilson(success,total)}
    report={'method':'Randomized offline retrieval and storage repeats, not actual model/agent performance',
            'configuration':{'rounds':args.rounds,'targets_per_round':args.targets,'seed':args.seed,'python':sys.version.split()[0]},
            'summary':summary,'semantic':semantic_probe(),'context_depth':context_depth_probe(),
            'latency_per_round_ms':[r['latency_ms'] for r in results],
            'elapsed_seconds':round(perf_counter()-start,2),
            'failures':[{'seed':r['seed'],'errors':r['errors']} for r in results if r['errors']],
            'limitations':['Synthetic unique-token retrieval is easier than human descriptions.',
                           'Reused project domain does not support external validity.',
                           'Wilson confidence intervals assume independent queries; this is optimistic for shared targets.',
                           'No model API tokens, real agent handoff tasks, official external benchmark or production security assessment.']}
    dest=Path(args.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['latency_per_round_ms','failures']},indent=2))
    print(f'Report: {dest.resolve()}')
    if args.strict:
        required = ('exact_label','exact_id','alias','historical')
        passed = all(summary[k]['nerve_correct']==summary[k]['total'] for k in required)
        passed &= all(summary[k]['correct']==summary[k]['total'] for k in ('unsupported_no_supported_decision','ambiguous_flagged','historical_after_noise_correct','new_process_success','sqlite_integrity_ok'))
        passed &= report['context_depth']['old_note_recovered_by_evidence_search']
        if not passed: raise SystemExit('Repeated deterministic benchmark gates failed; review report')

if __name__=='__main__': main()
