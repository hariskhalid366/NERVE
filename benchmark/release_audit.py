"""Auditable offline diagnostics for NERVE public developer preview.

Never labels proxy bytes as model tokens or scripted handoff as real-agent success.
No paid models, external datasets or network requests are used.
"""
from __future__ import annotations
import argparse
import json
import os
import platform
from pathlib import Path
import shutil
import sqlite3
import statistics
import tempfile
from time import perf_counter
from typing import Any
from nerve.core import Nerve
from benchmark.chess.run import CHESS, seed, TARGETS, flat_rank
from benchmark.chess.stress import STRESS

ROOT = Path(__file__).resolve().parents[1]
SECOND = ROOT / 'examples' / 'task-mini'

TASK_QUERIES = {
    'validate_deadline': [
        'validate_deadline',
        'Which helper validates a date string?',
        'A human typed tomorrow into the deadline, and it crashed',
    ],
    'parse_task': [
        'parse_task',
        'Where is raw task JSON converted to structured data?',
        'The importer accepted a task without any title',
    ],
    'save_tasks': [
        'save_tasks',
        'Which routine persists the todo collection to disk?',
        'My tasks disappeared after writing the JSON file',
    ],
    'load_tasks': [
        'load_tasks',
        'What reads previously saved tasks?',
        'Starting the program with no data file should return an empty list',
    ],
    'filter_tasks': [
        'filter_tasks',
        'Where do we only show open entries?',
        'The done-only view included incomplete work',
    ],
    'delete_task': [
        'delete_task',
        'Which helper removes an item by its identifier?',
        'Deleting an entry unexpectedly removed the wrong ID',
    ],
    'render_list': [
        'render_list',
        'Who prepares the printable task list?',
        'The completed status did not appear in display text',
    ],
    'mark_complete': [
        'mark_complete',
        'How is an unfinished todo changed to done?',
        'Finishing one job also changed other task states',
    ],
}

TASK_NOTES = {
    'validate_deadline':'A natural phrase such as tomorrow is not accepted as an ISO date.',
    'parse_task':'The importer must reject a task without a title or identifier.',
    'save_tasks':'Saving serializes the task collection to the JSON file.',
    'load_tasks':'Missing data file should result in an empty list.',
    'filter_tasks':'The done-only filter used to include incomplete work.',
    'delete_task':'Deleting an entry must match exactly one ID.',
    'render_list':'Completed status must be visible in display text.',
    'mark_complete':'Finishing one job should not change unrelated task states.'
}


def pct95(values: list[float]) -> float:
    values=sorted(values)
    return values[max(0, int(0.95*len(values) + 0.99999)-1)] if values else 0


def secondary_fixture() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix='nerve-release-task-') as td:
        project=Path(td)/'tasks'
        shutil.copytree(SECOND,project)
        with Nerve(project) as n:
            index=n.scan()
            for symbol,note in TASK_NOTES.items():
                target=f'symbol:tasks.py:{symbol}'
                n.remember(note,target)
            positives=[]
            for symbol,qs in TASK_QUERIES.items():
                expected=f'symbol:tasks.py:{symbol}'
                for i,query in enumerate(qs):
                    out=n.resolve(query)
                    predicted=out['candidates'][0]['target_id'] if out['candidates'] else None
                    base=flat_rank(n,query)
                    positives.append({'expected':expected,'query':query,'type':['exact','description','incident'][i],
                                      'nerve':predicted,'flat':base,'nerve_correct':predicted==expected,'flat_correct':base==expected})
            negative=[
                'Where is the Stripe webhook?',
                'How do I reset the customer OAuth refresh token?',
                'Which model runs the 3D chess engine?',
                'Where is the video transcoding worker?',
            ]
            neg=[{'query':q,'decision':n.resolve(q)['decision'],'no_candidate':not n.resolve(q)['candidates']} for q in negative]
        return {'index_files':index['files_indexed'],'index_symbols':index['symbols_indexed'],
                'positive':len(positives),'nerve_correct':sum(x['nerve_correct'] for x in positives),
                'flat_correct':sum(x['flat_correct'] for x in positives),
                'negative':neg,'queries':positives,
                'notice':'Second small hand-authored code fixture; not an independently sampled public benchmark'}


def scaling(sizes: list[int]) -> list[dict[str,Any]]:
    rows=[]
    for size in sizes:
        with tempfile.TemporaryDirectory(prefix='nerve-release-scale-') as td:
            p=Path(td)
            with Nerve(p) as n:
                start=perf_counter()
                for i in range(size):
                    n.observe(f'obj-{i}',f'UniqueWidget_{i}',description='Synthetic deterministic widget')
                build_seconds=perf_counter()-start
                probes=list(range(0,size,max(1,size//70)))[:70]
                ms=[];correct=0
                for i in probes:
                    start=perf_counter()
                    results=n.resolve(f'UniqueWidget_{i}')
                    ms.append(1000*(perf_counter()-start))
                    if results['candidates'] and results['candidates'][0]['target_id']==f'obj-{i}':
                        correct+=1
                # SQLite page count includes the indexes and WAL, where present.
                db_bytes=n.db_path.stat().st_size
            rows.append({'target_count':size,'probes':len(probes),'correct':correct,
                         'p50_ms':round(statistics.median(ms),3), 'p95_ms':round(pct95(ms),3),
                         'build_seconds':round(build_seconds,2),'sqlite_main_db_bytes':db_bytes})
    return rows


def history_pressure(events: int) -> dict[str,Any]:
    with tempfile.TemporaryDirectory(prefix='nerve-release-history-') as td:
        with Nerve(td) as n:
            n.observe('older','Old incident')
            n.event('older','issue','rare-glimmer-promotion-failure was fixed in the older incident')
            n.observe('newer','Recent events')
            for i in range(events):
                n.event('newer','noise',f'recent unrelated bookkeeping event {i}')
            q=n.resolve('rare glimmer promotion failure')
            recovered=bool(q['candidates'] and q['candidates'][0]['target_id']=='older')
            db_integrity=n.conn.execute('PRAGMA integrity_check').fetchone()[0]
            fts=n._fts_ready
            return {'new_events':events,'older_incident_retrieved':recovered,
                    'sqlite_integrity':db_integrity,'fts5':fts}


def payload_probe() -> dict[str,Any]:
    with tempfile.TemporaryDirectory(prefix='nerve-release-payload-') as td:
        root=Path(td)/'chess'
        shutil.copytree(CHESS,root)
        with Nerve(root) as n:
            seed(n)
            for i in range(150):
                n.remember(f'Project log reminder number {i} that is unrelated to the chess target')
            target=TARGETS[0]['id']
            selected=n.context(target,limit=12)
            all_data={
                'targets':[dict(r) for r in n.conn.execute('SELECT * FROM targets')],
                'memories':[dict(r) for r in n.conn.execute('SELECT * FROM memories')],
                'events':[dict(r) for r in n.conn.execute('SELECT * FROM events')]
            }
            a=len(json.dumps(selected,ensure_ascii=False).encode('utf-8'))
            b=len(json.dumps(all_data,ensure_ascii=False).encode('utf-8'))
            return {'selected_json_bytes':a,'entire_recorded_db_json_bytes':b,
                    'reduction_percent':round(100*(1-a/b),2),
                    'notice':'JSON bytes comparison; excludes tool-call overhead, prompt framing and actual tokenizer counts'}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',default='benchmark/results/PUBLIC_RELEASE_AUDIT.json')
    ap.add_argument('--quick',action='store_true')
    args=ap.parse_args()
    results={
        'evaluation':'NERVE deterministic offline diagnostics; no real AI-agent experiment',
        'python':platform.python_version(),'os':platform.platform(),
        'sqlite_version':sqlite3.sqlite_version,
        'task_mini':secondary_fixture(),
        'scaling':scaling([100,500] if args.quick else [100,500,1500,3000]),
        'long_history':history_pressure(600 if args.quick else 6201),
        'payload_proxy':payload_probe(),
        'not_tested':['LongMemEval official','LoCoMo official','MemoryArena official','SWE-bench live agent tasks',
                      'real provider token counts','actual Cursor/Claude/Codex host interoperability',
                      'real cross-model handoffs','security audit by independent experts'],
    }
    dest=Path(args.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    summary={k:v for k,v in results.items() if k != 'task_mini'}
    summary['task_mini']={k:v for k,v in results['task_mini'].items() if k not in ['queries','negative']}
    summary['task_mini']['negative_no_candidate']=sum(q['no_candidate'] for q in results['task_mini']['negative'])
    print(json.dumps(summary,indent=2,ensure_ascii=False))

if __name__=='__main__':main()
