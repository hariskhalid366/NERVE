import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from nerve.mcp_stdio import TOOLS, handle

class BuiltinMCPTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
    def tearDown(self): self.temp.cleanup()
    def request(self, method, params=None, ident=1):
        return handle(self.root, {'jsonrpc':'2.0','id':ident,'method':method,'params':params or {}})
    def test_initialize_and_tool_discovery(self):
        v=self.request('initialize',{'protocolVersion':'2025-06-18'})
        self.assertEqual(v['result']['protocolVersion'],'2025-06-18')
        names={x['name'] for x in self.request('tools/list')['result']['tools']}
        self.assertIn('get_project_brief',names)
        self.assertEqual(len(names),len(TOOLS))
    def test_observe_remember_resolve_across_calls(self):
        def call(name,kw):
            return self.request('tools/call',{'name':name,'arguments':kw})['result']
        self.assertFalse(call('observe_target',{'target_id':'panel:sign-in','label':'Sign in panel'})['isError'])
        self.assertFalse(call('remember_context',{'target_id':'panel:sign-in','text':'Avoid retries after login validation'})['isError'])
        result=call('resolve_target',{'query':'Sign in panel'})
        self.assertIn('panel:sign-in',result['content'][0]['text'])
        ctx=call('get_target_context',{'target_id':'panel:sign-in'})
        self.assertIn('Avoid retries',ctx['content'][0]['text'])
    def test_invalid_args_fail_closed(self):
        res=self.request('tools/call',{'name':'scan_project','arguments':{'path':'/etc'}})
        self.assertTrue(res['result']['isError'])
    def test_stdio_subprocess_roundtrip(self):
        messages=[
            {'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'test','version':'0'}}},
            {'jsonrpc':'2.0','method':'notifications/initialized'},
            {'jsonrpc':'2.0','id':2,'method':'tools/list'},
            {'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'get_project_brief','arguments':{}}},
        ]
        p=subprocess.run([sys.executable,'-m','nerve','--project',str(self.root),'mcp'],
                         input=''.join(json.dumps(x)+'\n' for x in messages),text=True,
                         capture_output=True,timeout=10, env={**os.environ,'NERVE_MCP_BACKEND':'builtin'})
        self.assertEqual(p.returncode,0,p.stderr)
        frames=[json.loads(x) for x in p.stdout.splitlines()]
        self.assertEqual([f['id'] for f in frames],[1,2,3])
        self.assertIn('tools',frames[1]['result'])
        self.assertFalse(frames[2]['result']['isError'])

if __name__=='__main__': unittest.main()
