"""Use NERVE as an actual external memory during its own assessment."""
import json, os, subprocess, sys
from pathlib import Path
from nerve.core import Nerve
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(__file__).resolve().parent/'self_dogfood.json'
with Nerve(ROOT) as n:
    scan=n.scan()
    n.observe('audit:long-term-recall','Long-term event retrieval',kind='verified-test',
              description='Old incident remained searchable after more than 325 unrelated newer events',
              aliases=['history eviction fix','ancient incident retrieval'],source_path='nerve/core.py',origin='audit')
    n.remember('Verified by regression test: historical evidence from source-backed events survives unrelated newer events.',
               target_id='audit:long-term-recall',category='test-result',author='assistant-audit')
    n.event('audit:long-term-recall','test-pass','1000 newer unrelated events did not evict searchability of the old target')
    n.observe('audit:scoped-context','Target memory priority',kind='verified-test',
              description='Explicit target notes are not crowded out by project-global notes',
              aliases=['global note crowding'],source_path='nerve/core.py',origin='audit')
    n.remember('Verified by regression test: 120 more recent project notes did not hide the target-specific note.',
               target_id='audit:scoped-context',category='test-result',author='assistant-audit')
messages=[
  {'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'self-dogfood','version':'1'}}},
  {'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'resolve_target','arguments':{'query':'history eviction fix'}}},
  {'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'get_target_context','arguments':{'target_id':'audit:long-term-recall'}}},
  {'jsonrpc':'2.0','id':4,'method':'tools/call','params':{'name':'resolve_target','arguments':{'query':'global note crowding'}}}
]
run=subprocess.run([sys.executable,'-m','nerve','--project',str(ROOT),'mcp'],input='\n'.join(map(json.dumps,messages))+'\n',text=True,capture_output=True,timeout=30,check=True,env={**os.environ,'PYTHONPATH':str(ROOT),'NERVE_MCP_BACKEND':'builtin'})
returns=[json.loads(l) for l in run.stdout.splitlines()]
resolve=json.loads(returns[1]['result']['content'][0]['text'])
context=json.loads(returns[2]['result']['content'][0]['text'])
resolve2=json.loads(returns[3]['result']['content'][0]['text'])
report={
    'host':'separate local MCP Python subprocess, not global ChatGPT runtime',
    'project':str(ROOT),
    'scan_files':scan['files_indexed'],'scan_symbols':scan['symbols_indexed'],
    'mcp_initialize':returns[0]['result']['serverInfo'],
    'history_alias_resolves':bool(resolve['candidates']) and resolve['candidates'][0]['target_id']=='audit:long-term-recall',
    'retrieved_saved_note':any('historical evidence' in x['text'] for x in context.get('memories',[])),
    'retrieved_saved_test_event':any('1000 newer unrelated events' in x['message'] for x in context.get('events',[])),
    'second_alias_resolves':bool(resolve2['candidates']) and resolve2['candidates'][0]['target_id']=='audit:scoped-context',
    'not_a_live_llm_cross_agent_trial':True
}
OUT.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
