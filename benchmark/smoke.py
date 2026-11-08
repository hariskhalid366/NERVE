"""Synthetic deterministic diagnostics of NERVE's retrieval and persistence.

Not an LLM benchmark. Does not prove end-to-end reasoning or token savings.
Run: python -m benchmark.smoke --output benchmark/results/smoke.json
"""
from __future__ import annotations
import argparse
import json
import re
import statistics
import tempfile
from pathlib import Path
from nerve.core import Nerve, tokens

HERE=Path(__file__).resolve().parent


def tokenize_proxy(text):
    """Word/punctuation pieces, NOT an LLM token count."""
    return len(re.findall(r'\w+|[^\w\s]', text, re.UNICODE))


def flat_rank(query, data):
    """Same information, naive bag-of-words over concatenated record (baseline)."""
    q=tokens(query)
    scores=[]
    for item in data:
        evidence=' '.join([item['label'], item['description'], *item['aliases'],item['incident'], item['fact']])
        score=len(q & tokens(evidence))
        if score:
            scores.append((score,item['id']))
    return [ident for _,ident in sorted(scores,key=lambda x:(-x[0],x[1]))]


def run():
    data=json.loads((HERE/'scenarios.json').read_text())
    unknown_queries=['copper asteroid telescope calibration','lunar beetles spectrogram','unidentified coral migration',
                      'quantum orchard pollen','glacier nitrogen microscope','peripheral telescope beacon',
                      'nebula gravity oven','submarine rainfall simulator','orphaned astronomy telescope','zirconium comet engine']
    # Near-misses deliberately overlap a known component but describe an unobserved issue.
    unsupported_queries=['refund tax exemption certificate','dashboard heatmap legend',
                         'transcript language translation errors','stock expiry barcode scanning',
                         'calendar holiday import','avatar background blur',
                         'signature biometric pressure levels','quiet hours calendar synchronization',
                         'feature flags billing subscription','thumbnail OCR invoice extraction']
    assert len({x['id'] for x in data})==len(data)
    cases=[]
    for i,item in enumerate(data):
        assert len(item['queries'])==4
        for n,q in enumerate(item['queries']):
            cases.append({'id':f'T{i:02d}Q{n}','query':q,'expected_id':item['id'],'expected_fact':item['fact'],
                          'kind': ['label','alias','incident','paraphrase'][n]})
    for i,q in enumerate(unknown_queries):
        cases.append({'id':f'NEG{i:02d}','query':q,'expected_id':None,'expected_fact':None,'kind':'unknown'})
    for i,q in enumerate(unsupported_queries):
        cases.append({'id':f'UNS{i:02d}','query':q,'expected_id':None,'expected_fact':None,'kind':'unsupported'})
    with tempfile.TemporaryDirectory(prefix='nerve-bench-') as root:
        with Nerve(root) as agent_a:
            for item in data:
                agent_a.observe(item['id'], item['label'], 'component', item['description'], item['aliases'], origin='fixture')
                agent_a.event(item['id'],'incident',item['incident'],{'source':'synthetic-fixture'})
                agent_a.event(item['id'],'investigation',f"Investigation recorded for {item['label']}; regression test proposed.")
                agent_a.remember(item['fact'],item['id'],category='verified_decision',author='agent-a')
                agent_a.remember(f"Review regression coverage for {item['label']} next sprint.",item['id'],category='follow_up',author='agent-a')
            agent_a.remember('Fixture created by Agent A before session boundary','project',author='agent-a')
        # Agent A is explicitly disconnected. Agent B is a completely fresh connection.
        with Nerve(root) as agent_b:
            persisted=0
            for item in data:
                exact=agent_b.context(item['id'])
                persisted += int(exact['found'] and item['fact'] in [m['text'] for m in exact['memories']])
            rows=[]
            # Both arms see identical underlying stored evidence. Flat arm simply
            # receives every record, while NERVE selects one object's evidence.
            full_recent=agent_b.recent(limit=100)
            flat_context=json.dumps({'targets':[agent_b.context(item['id'],include_history=False)
                                 for item in data],'events':full_recent['events'],
                                 'memories':full_recent['memories']},ensure_ascii=False,separators=(',',':'))
            raw_size=tokenize_proxy(flat_context)
            for c in cases:
                result=agent_b.resolve(c['query'],limit=3)
                picks=[x['target_id'] for x in result['candidates']]
                status=result.get('decision', 'unknown')
                flat=flat_rank(c['query'],data)[:3]
                expected=c['expected_id']
                # Context recovery is a fact + correct target present, NOT an agent answer.
                candidate_context=None
                retrieved_payload=None
                if picks:
                    candidate_context=agent_b.context(picks[0],limit=5)
                    retrieved_payload=json.dumps({'retrieval':result,'context':candidate_context},ensure_ascii=False,separators=(',',':'))
                coverage=(expected is not None and picks and picks[0]==expected and
                          c['expected_fact'] in (retrieved_payload or ''))
                # Flat full-history context includes all gold facts, but has a much larger payload.
                rows.append({'case_id':c['id'],'kind':c['kind'],'expected_id':expected,'query':c['query'],
                    'nerve_top1':picks[0] if picks else None,'nerve_top3':picks,
                    'nerve_candidate_decision':status,
                    'nerve_confident_top1_correct':status=='supported_candidate' and (picks[0] if picks else None)==expected,
                    'flat_top1':flat[0] if flat else None,'flat_top3':flat,
                    'nerve_top1_correct':(picks[0] if picks else None)==expected,
                    'flat_top1_correct':(flat[0] if flat else None)==expected,
                    'nerve_recall3':expected in picks if expected else (not picks),
                    'flat_recall3':expected in flat if expected else (not flat),
                    'fact_evidence_found':bool(coverage),
                    'retrieved_context_proxy_pieces':tokenize_proxy(retrieved_payload) if retrieved_payload else 0,
                    'full_history_proxy_pieces':raw_size})
    positive=[r for r in rows if r['expected_id'] is not None]
    neg=[r for r in rows if r['expected_id'] is None]
    unknown=[r for r in rows if r['kind']=='unknown']
    unsupported=[r for r in rows if r['kind']=='unsupported']
    by_kind={k:{'n':len([r for r in positive if r['kind']==k]),
                'nerve_top1':round(sum(r['nerve_top1_correct'] for r in positive if r['kind']==k)/len([r for r in positive if r['kind']==k]),4),
                'flat_top1':round(sum(r['flat_top1_correct'] for r in positive if r['kind']==k)/len([r for r in positive if r['kind']==k]),4)}
             for k in ['label','alias','incident','paraphrase']}
    score=lambda cases,field: round(sum(bool(r[field]) for r in cases)/len(cases),4) if cases else None
    summary={
        'evaluation_type':'DETERMINISTIC_SYNTHETIC_RETRIEVAL_DIAGNOSTIC_NOT_LLM_EVALUATION',
        'dataset':'20 hand-authored artificial objects, 4 query styles each, 10 unknown and 10 unsupported queries',
        'n_positive':len(positive),'n_negative':len(neg),'agent_sessions':'A writes, closes; B reopens SQLite',
        'target_accuracy_top1':score(positive,'nerve_top1_correct'),
        'target_recall_at3':score(positive,'nerve_recall3'),
        'flat_target_top1':score(positive,'flat_top1_correct'),
        'flat_target_recall_at3':score(positive,'flat_recall3'),
        'candidate_advisory_supported_fraction':round(sum(r['nerve_candidate_decision']=='supported_candidate' for r in positive)/len(positive),4),
        'candidate_advisory_correct_among_supported':round(
            sum(r['nerve_confident_top1_correct'] for r in positive) /
            max(1,sum(r['nerve_candidate_decision']=='supported_candidate' for r in positive)),4),
        'unsupported_candidate_advisory_flagged_for_confirmation':round(
            sum(r['nerve_candidate_decision']!='supported_candidate' for r in unsupported)/len(unsupported),4),
        'unknown_no_candidate_rate':score(unknown,'nerve_top1_correct'),
        'unsupported_no_candidate_rate':score(unsupported,'nerve_top1_correct'),
        'negative_abstention_rate':score(neg,'nerve_top1_correct'),
        'flat_negative_abstention_rate':score(neg,'flat_top1_correct'),
        'target_accuracy_by_query_kind':by_kind,
        'context_evidence_recovered_top1':score(positive,'fact_evidence_found'),
        'cross_session_exact_id_persistence':round(persisted/len(data),4),
        'cross_session_discovery_plus_fact_top1':score(positive,'fact_evidence_found'),
        'full_history_context_proxy_pieces':raw_size,
        'avg_nerve_context_proxy_pieces':round(statistics.mean(r['retrieved_context_proxy_pieces'] for r in positive),1),
        'context_payload_proxy_reduction':round(1-statistics.mean(r['retrieved_context_proxy_pieces'] for r in positive)/raw_size,4),
        'actual_llm_token_efficiency':'NOT_MEASURED',
        'context_payload_proxy_units':'word_and_punctuation_pieces_not_model_tokens',
        'actual_llm_context_recovery_accuracy':'NOT_MEASURED',
        'actual_llm_cross_agent_task_success':'NOT_MEASURED',
        'interpretation':'Measures exact evidence availability and heuristic retrieval on known synthetic fixtures; NOT real-model understanding, actual token consumption or true agent task success. Candidates are not model assertions; near-miss no-candidate rate measures over-retrieval, not hallucination.'
    }
    return {'summary':summary,'cases':rows}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--output',default='benchmark/results/smoke.json')
    args=p.parse_args()
    res=run()
    path=Path(args.output)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(res,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(res['summary'],indent=2))
    print(f'Written to {path}')

if __name__=='__main__':main()
