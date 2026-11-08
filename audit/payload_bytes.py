"""Context payload bytes (not provider token counts)."""
import json, shutil, tempfile, statistics, random
from pathlib import Path
from nerve.core import Nerve
from benchmark.chess.run import CHESS, TARGETS, seed
out=Path(__file__).resolve().parent/'payload_bytes.json'
with tempfile.TemporaryDirectory(prefix='nerve-payload-bytes-') as td:
    root=Path(td)/'chess';shutil.copytree(CHESS,root)
    with Nerve(root) as n:
        seed(n)
        full={'targets':[dict(x) for x in n.conn.execute('SELECT * FROM targets')],
              'events':[dict(x) for x in n.conn.execute('SELECT * FROM events')],
              'memories':[dict(x) for x in n.conn.execute('SELECT * FROM memories')]}
        full_bytes=len(json.dumps(full,ensure_ascii=False,separators=(',',':')).encode())
        samples=[]
        for entry in TARGETS:
            for query in entry['queries']:
                resolved=n.resolve(query)
                target_id=resolved['candidates'][0]['target_id'] if resolved['candidates'] else None
                payload={'resolved':resolved,'context':n.context(target_id) if target_id else None}
                nbytes=len(json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode())
                samples.append({'query':query,'bytes':nbytes,'correct':target_id==entry['id']})
        sizes=sorted(x['bytes'] for x in samples)
        result={'full_history_bytes':full_bytes,'query_count':len(samples),
            'avg_retrieved_bytes':round(statistics.mean(sizes),1),'median_retrieved_bytes':statistics.median(sizes),
            'max_retrieved_bytes':max(sizes),'min_retrieved_bytes':min(sizes),
            'avg_byte_reduction_percent':round(100*(1-statistics.mean(sizes)/full_bytes),2),
            'correct_retrievals':sum(x['correct'] for x in samples),
            'qualification':'This is only serialization size, not actual provider token counts. The all-history baseline is intentionally naive and context-only retrieval may omit useful information.'}
out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
