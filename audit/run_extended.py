"""Deterministic NERVE v0.6 pressure audit. Uses only local fixture data and no LLM.
Run: PYTHONPATH=../NERVE-v0.6 python run_extended.py
"""
from __future__ import annotations
import json, os, tempfile, time, math, statistics, random, shutil, subprocess, sys, sqlite3, hashlib
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from collections import defaultdict, Counter
from nerve.core import Nerve
from benchmark.chess.run import run as chess_run, CHESS, seed, TARGETS, flat_rank, approx_pieces
from benchmark.chess.stress import evaluate as chess_stress

SEED=20261108
OUT=Path(__file__).resolve().parent
rng=random.Random(SEED)

def summary_times(times):
    s=sorted(times)
    return {'n':len(s),'p50_ms':round(statistics.median(s),3),'p95_ms':round(s[min(len(s)-1, math.ceil(.95*len(s))-1)],3),'p99_ms':round(s[min(len(s)-1, math.ceil(.99*len(s))-1)],3),'max_ms':round(max(s),3)}

def bootstrap_difference(rows,seed=SEED,reps=5000):
    r=random.Random(seed)
    n=len(rows)
    observed=sum(a-b for a,b in rows)/n
    trials=sorted(sum((lambda pair: pair[0]-pair[1])(rows[r.randrange(n)]) for _ in range(n))/n for k in range(reps))
    return {'difference_pp':round(100*observed,2),'paired_bootstrap_95pct_interval_pp':[round(100*trials[int(.025*reps)],2),round(100*trials[int(.975*reps)],2)],'repetitions':reps,'caveat':'Confidence interval is descriptive for this nonrandom test sample; it does not establish external generalization.'}

def exact_mcnemar(rows):
    b=sum(a and not v for a,v in rows)
    c=sum(v and not a for a,v in rows)
    n=b+c
    p=min(1.,2*sum(math.comb(n,k) for k in range(min(b,c)+1))/(2**n)) if n else 1.
    return {'nerve_only_correct':b,'baseline_only_correct':c,'discordant':n,'exact_mcnemar_two_sided_p':round(p,6)}

def direct_battery():
    p=OUT/'original_chess.json'; raw=chess_run(p)
    q=OUT/'stress_chess.json'; stress=chess_stress(q)
    groups={}
    for label,cases in [('original',raw['per_case']),('stress',stress['positive'])]:
        pairs=[(int(x['nerve_correct']),int(x['flat_correct'] if label=='original' else x['baseline_correct'])) for x in cases]
        groups[label]={'n':len(pairs),'nerve_correct':sum(x[0] for x in pairs),'baseline_correct':sum(x[1] for x in pairs),'paired':exact_mcnemar(pairs),'delta':bootstrap_difference(pairs)}
    return {'groups':groups,'negative_original':raw['overall']['negative_no_supported_candidate'],'negative_original_n':raw['overall']['negative_queries'],'negative_stress':stress['negative_needs_confirmation_or_no_match'],'negative_stress_n':stress['negative_count'],'context_facts_recovered':raw['overall']['explicit_id_context_facts'],'context_facts_total':raw['overall']['explicit_id_context_total'],'mcp_handoff':raw['mcp_handoff'],'approx_payload_reduction_percent':raw['overall']['payload_reduction_vs_full_history_percent']}

def global_crowding():
    with tempfile.TemporaryDirectory(prefix='nerve-crowding-') as td:
        root=Path(td)
        with Nerve(root) as n:
            n.observe('target','Rules engine')
            n.remember('CRITICAL: en passant validator checks actual pawn existence',target_id='target')
            n.remember('Other project note 0',target_id='project')
            prior=n.context('target',limit=12)
            for i in range(25):n.remember(f'Unrelated recent project note {i}',target_id='project')
            after=n.context('target',limit=12)
            return {'target_memory_pre_global_spam':sum(m['target_id']=='target' for m in prior['memories']),'target_memory_post_25_global_notes':sum(m['target_id']=='target' for m in after['memories']),'stored_target_note_still_in_database':n.conn.execute('SELECT COUNT(*) FROM memories WHERE target_id=?',('target',)).fetchone()[0]==1}

def history_eviction():
    with tempfile.TemporaryDirectory(prefix='nerve-eviction-') as td:
        root=Path(td)
        with Nerve(root) as n:
            n.observe('target-old','UnrelatedName','function')
            n.event('target-old','bug','ziggurat unicorn checksum failed')
            before=n.resolve('ziggurat unicorn checksum')
            n.observe('target-new','OtherName','function')
            for i in range(325):n.event('target-new','update',f'ordinary update cycle {i}')
            after=n.resolve('ziggurat unicorn checksum')
            return {'matched_before_325_newer_events':bool(before['candidates']) and before['candidates'][0]['target_id']=='target-old','matched_after_325_newer_events':bool(after['candidates']) and after['candidates'][0]['target_id']=='target-old','old_event_present_in_db':n.conn.execute('SELECT COUNT(*) FROM events WHERE target_id=?',('target-old',)).fetchone()[0]==1}

def stale_tests():
    with tempfile.TemporaryDirectory(prefix='nerve-stale-') as td:
        root=Path(td)
        file=root/'engine.py'
        file.write_text('def check_legal_moves():\n    return True\n')
        with Nerve(root) as n:
            n.observe('checker','legal move validator',source_path='engine.py')
            n.remember('A test verified this source snapshot',target_id='checker')
            u=n.context('checker')['memories'][0]['freshness']
            file.write_text('def check_legal_moves():\n    return False\n')
            v=n.context('checker')['memories'][0]['freshness']
            file.unlink()
            w=n.context('checker')['memories'][0]['freshness']
            r=n.resolve('legal move validator')
            return {'freshness_sequence':[u,v,w],'missing_source_decision':r['decision']}

def redaction_tests():
    with tempfile.TemporaryDirectory(prefix='nerve-sec-') as td:
        root=Path(td)
        (root/'.env').write_text('SECRET_REAL=must-not-be-indexed')
        (root/'engine.py').write_text('def calculate():\n    return 42\n')
        with Nerve(root) as n:
            scan=n.scan()
            n.observe('t','test','component',state={'api_key':'illustrative-sensitive-value','note':'password:examplepassword'})
            n.event('t','error','token=illustrative-token',payload={'authorization':'auth-opaque'})
            data=n.context('t')
            text=json.dumps(data)
            return {'env_file_not_indexed':'.env' not in text,'api_key_redacted':'illustrative-sensitive-value' not in text,'inline_password_redacted':'examplepassword' not in text,'inline_token_redacted':'illustrative-token' not in text,'authorization_redacted':'auth-opaque' not in text,'files_indexed':scan['files_indexed']}

def noisy_ambiguity():
    with tempfile.TemporaryDirectory(prefix='nerve-ambig-') as td:
        with Nerve(td) as n:
            for i in range(5):n.observe(f'obj-{i}','move handler',kind='component',aliases=['turn handler'],description='Update chess position for move')
            exact=n.resolve('obj-3'); vague=n.resolve('move handler'); out=n.resolve('unknownzerowordzz')
            return {'exact_top1':exact['candidates'][0]['target_id'],'ambiguous_decision':vague['decision'],'ambiguous_candidate_count':len(vague['candidates']),'unknown_decision':out['decision'],'unknown_candidate_count':len(out['candidates'])}

def scale_battery():
    outputs=[]
    for size in [100,500,1500,3000]:
        with tempfile.TemporaryDirectory(prefix='nerve-scale-') as td:
            root=Path(td)
            with Nerve(root) as n:
                t0=time.perf_counter()
                for i in range(size):
                    n.observe(f'symbol:{i:05d}',f'UniqueModule{i:05d}',kind='symbol',description=f'Static function unit {i:05d} chess alternate path',aliases=[f'exactalias{i:05d}'])
                    n.event(f'symbol:{i:05d}','test',f'Checked synthetic event phase {i:05d} engine')
                    n.remember(f'Explicit synthetic note about module {i:05d}',target_id=f'symbol:{i:05d}')
                write_s=time.perf_counter()-t0
                times=[]; correct=0; matched=0; candidates_bytes=[]
                for j in range(120):
                    i=(j*1013+size//3)%size
                    query=f'exactalias{i:05d}'
                    t1=time.perf_counter(); ans=n.resolve(query); times.append((time.perf_counter()-t1)*1000)
                    if ans['candidates']:
                        matched+=1
                        correct+=ans['candidates'][0]['target_id']==f'symbol:{i:05d}'
                    candidates_bytes.append(len(json.dumps(ans).encode()))
                n.conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')
                dbbytes=n.db_path.stat().st_size
                outputs.append({'targets':size,'events':size,'memories':size,'creation_seconds':round(write_s,3),'resolve':summary_times(times),'exact_alias_accuracy':f'{correct}/120','db_bytes':dbbytes,'db_bytes_per_target_record_triplet':round(dbbytes/size,1),'avg_resolve_response_bytes':round(statistics.mean(candidates_bytes))})
    return outputs

def worker_write(args):
    td,worker,k=args
    with Nerve(td) as n:
        for i in range(k):
            n.event('shared','parallel',f'worker-{worker}: event {i}')
            n.remember(f'worker-{worker}: decision {i}',target_id='shared')
    return k

def concurrency_battery():
    with tempfile.TemporaryDirectory(prefix='nerve-concurrent-') as td:
        with Nerve(td) as n:n.observe('shared','Concurrent record')
        jobs=[(td,w,75) for w in range(8)]
        failures=[]; got=[]
        t=time.perf_counter()
        with ProcessPoolExecutor(max_workers=8) as ex:
            fs=[ex.submit(worker_write,j) for j in jobs]
            for f in fs:
                try:got.append(f.result(timeout=35))
                except Exception as e:failures.append(type(e).__name__+':'+str(e)[:90])
        elapsed=time.perf_counter()-t
        with Nerve(td) as n:
            counts=(n.conn.execute('SELECT COUNT(*) FROM events').fetchone()[0],n.conn.execute('SELECT COUNT(*) FROM memories').fetchone()[0])
            integrity=n.conn.execute('PRAGMA integrity_check').fetchone()[0]
        return {'workers':8,'events_attempted':600,'memories_attempted':600,'events_persisted':counts[0],'memories_persisted':counts[1],'worker_failures':failures,'duration_seconds':round(elapsed,3),'sqlite_integrity':integrity}

def process_recovery():
    with tempfile.TemporaryDirectory(prefix='nerve-crash-') as td:
        with Nerve(td) as n:n.observe('crash','Persisted target')
        code='from nerve.core import Nerve; import os; n=Nerve('+repr(td)+'); n.remember("written before abrupt exit",target_id="crash"); os._exit(0)'
        subprocess.run([sys.executable,'-c',code],check=True,env=os.environ.copy(),timeout=20)
        with Nerve(td) as n:
            found=any('written before abrupt exit' in m['text'] for m in n.context('crash')['memories'])
            status=n.conn.execute('PRAGMA integrity_check').fetchone()[0]
        return {'committed_note_survives_abrupt_process_exit':found,'sqlite_integrity':status}

def isolated_projects():
    with tempfile.TemporaryDirectory(prefix='nerve-isolation-') as td:
        a=Path(td)/'A';b=Path(td)/'B';a.mkdir();b.mkdir()
        with Nerve(a) as n:n.observe('a','PrivateA');n.remember('project A',target_id='a')
        with Nerve(b) as n:
            return {'A_target_not_visible_in_B':not n.context('a')['found'],'B_recent_has_no_A_memory':not n.recent()['memories']}

def own_code_battery():
    # Unseeded deployment-like code index: no human memory enrichment.
    project=Path(__file__).resolve().parents[1]
    cases=[
       ('resolve_target','resolve','nerve/core.py'),('observe','observe','nerve/core.py'),('read project recent','recent','nerve/core.py'),
       ('source file scanner','scan','nerve/core.py'),('record a decision','remember','nerve/core.py'),('remove a target','forget','nerve/core.py'),
       ('redact a key','redact','nerve/core.py'),('file revision digest','_source_digest','nerve/core.py'),
       ('get revision status','_evidence_freshness','nerve/core.py'),('validate relative file path','_allowed_relative_path','nerve/core.py'),
       ('build a project brief','project_brief','nerve/brief.py'),('install Git hook','install_post_commit_hook','nerve/git_observer.py'),
       ('capture latest commit','capture_commit','nerve/git_observer.py'),('save Cursor config','save_cursor_config','nerve/onboarding.py'),
       ('run command line','main','nerve/cli.py'),('serve builtin MCP stdio','serve','nerve/mcp_stdio.py'),
       ('parse MCP JSONRPC request','handle','nerve/mcp_stdio.py'),('route MCP invocation','call_tool','nerve/mcp_stdio.py')]
    with tempfile.TemporaryDirectory(prefix='nerve-own-') as td:
        root=Path(td);shutil.copytree(project/'nerve',root/'nerve')
        with Nerve(root) as n:
            indexed=n.scan()
            rows=[]
            for query,symbol,path in cases:
                gold=f'symbol:{path}:{symbol}'
                exists=n.context(gold,False)['found']
                a=n.resolve(query)
                p=a['candidates'][0]['target_id'] if a['candidates'] else None
                flat=flat_rank(n,query)
                rows.append({'query':query,'gold':gold,'exists':exists,'nerve':p,'baseline':flat,'nerve_correct':p==gold,'flat_correct':flat==gold})
            return {'index':indexed,'n':len(rows),'gold_ids_exist':sum(r['exists'] for r in rows),'nerve_correct':sum(r['nerve_correct'] for r in rows),'baseline_correct':sum(r['flat_correct'] for r in rows),'individual':rows}

def main():
    t=time.perf_counter()
    data={}
    for label, fn in [('chess_baselines',direct_battery),('global_note_crowding',global_crowding),('historical_eviction',history_eviction),('freshness',stale_tests),('privacy',redaction_tests),('ambiguous_and_unknown',noisy_ambiguity),('own_source_unseeded',own_code_battery),('scale',scale_battery),('concurrent_writes',concurrency_battery),('crash_recovery',process_recovery),('project_isolation',isolated_projects)]:
        try:
            s=time.perf_counter();data[label]=fn(); print(label,round(time.perf_counter()-s,2),'s',flush=True)
        except Exception as e:
            data[label]={'ERROR':type(e).__name__+':'+str(e)};print(label,'ERROR',e,flush=True)
    data['elapsed_seconds']=round(time.perf_counter()-t,3)
    data['code_version']=os.getenv('NERVE_AUDIT_VERSION','source-under-test')
    (OUT/'results.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in data.items() if k not in ('own_source_unseeded','scale')},indent=2,ensure_ascii=False))

if __name__=='__main__':main()
