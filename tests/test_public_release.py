"""Additional safety, discovery and portability invariants for public releases."""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from nerve.core import Nerve
from nerve.mcp_stdio import handle


class PublicReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="nerve-release-test-")
        self.root = Path(self.temp.name) / "demo"
        self.root.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def test_scanner_never_uses_recursive_rglob(self):
        (self.root / 'src').mkdir()
        (self.root / 'src' / 'main.mjs').write_text('export function computeDistance() { return 2; }')
        (self.root / 'node_modules' / 'huge').mkdir(parents=True)
        (self.root / 'node_modules' / 'huge' / 'secret.js').write_text('export function shouldNotIndex() {}')
        with patch.object(Path, 'rglob', side_effect=AssertionError('Scanner must prune directories')):
            with Nerve(self.root) as n:
                out = n.scan()
                self.assertEqual(out['files_indexed'], 1)
                self.assertTrue(n.context('symbol:src/main.mjs:computeDistance')['found'])
                self.assertFalse(n.context('symbol:node_modules/huge/secret.js:shouldNotIndex')['found'])

    def test_scanner_avoids_symlinked_folders_and_external_files(self):
        outside = Path(self.temp.name) / 'elsewhere'
        outside.mkdir()
        (outside / 'data.js').write_text('export function secretNeverIndex() {}')
        (self.root / 'linked').symlink_to(outside, target_is_directory=True)
        (self.root / 'exfiltrate.js').symlink_to(outside / 'data.js')
        with Nerve(self.root) as n:
            self.assertEqual(n.scan()['files_indexed'], 0)

    def test_secret_names_and_escape_paths_blocked(self):
        with Nerve(self.root) as n:
            for p in ('.env', '.env.production', 'nested/../../outside.js', '/tmp/outside.js', 'private.pem'):
                with self.subTest(p=p):
                    with self.assertRaises(ValueError):
                        n.observe('x', 'secret', source_path=p)

    def test_git_style_sensitive_directories_not_indexed(self):
        for folder in ('.git', '.nerve', 'dist', 'build', '.next', 'node_modules', 'vendor'):
            p=self.root / folder
            p.mkdir()
            (p / 'stray.py').write_text('def suppressedSymbol(): return 1')
        (self.root / 'real.py').write_text('def usefulSymbol(): return 1')
        with Nerve(self.root) as n:
            self.assertEqual(n.scan()['files_indexed'], 1)
            self.assertFalse(any('suppressedSymbol' in r['label'] for r in n.conn.execute('SELECT label FROM targets')))

    def test_memory_isolation_between_projects(self):
        b=Path(self.temp.name)/'other';b.mkdir()
        with Nerve(self.root) as a:
            a.remember('site-specific-only')
        with Nerve(b) as other:
            self.assertNotIn('site-specific-only', json.dumps(other.recent()))

    def test_close_reopen_and_record_deletion(self):
        with Nerve(self.root) as n:
            n.observe('stable:target','Old feature')
            n.event('stable:target','bug','red-bishop-promotion-event')
            n.remember('red-bishop-promotion-fix', target_id='stable:target')
        with Nerve(self.root) as n:
            self.assertTrue(n.context('stable:target')['found'])
            self.assertEqual(n.forget('stable:target'),{'targets':1,'events':1,'memories':1})
            self.assertFalse(n.context('stable:target')['found'])
            self.assertFalse(n.resolve('red-bishop-promotion-event')['candidates'])

    def test_source_freshness_changes(self):
        source=self.root/'alpha.py';source.write_text('def alpha(): return True')
        with Nerve(self.root) as n:
            n.observe('symbol:alpha.py:alpha','alpha',source_path='alpha.py')
            n.remember('alpha is true',target_id='symbol:alpha.py:alpha')
            self.assertEqual(n.context('symbol:alpha.py:alpha')['memories'][0]['freshness'],'source_unchanged')
            source.write_text('def alpha(): return False')
            self.assertEqual(n.context('symbol:alpha.py:alpha')['memories'][0]['freshness'],'source_changed')
            source.unlink()
            self.assertEqual(n.context('symbol:alpha.py:alpha')['memories'][0]['freshness'],'source_missing')

    def test_mcp_invalid_tool_args_do_not_execute(self):
        cases = [
            {'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'remember_context','arguments':{'text':'bad','surprise':'yes'}}},
            {'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'unknown','arguments':{}}},
            {'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'resolve_target','arguments':{'query':['not-string']}}},
        ]
        for msg in cases:
            response=handle(self.root,msg)
            self.assertTrue(response['result']['isError'])
        with Nerve(self.root) as n:
            self.assertEqual(len(n.recent()['memories']),0)

    def test_mcp_notification_has_no_response(self):
        response=handle(self.root,{'jsonrpc':'2.0','method':'notifications/initialized','params':{}})
        self.assertIsNone(response)

    def test_mcp_valid_read_and_write(self):
        write=handle(self.root,{'jsonrpc':'2.0','id':7,'method':'tools/call','params':{'name':'remember_context','arguments':{'text':'saved safely'}}})
        self.assertFalse(write['result']['isError'])
        read=handle(self.root,{'jsonrpc':'2.0','id':8,'method':'tools/call','params':{'name':'get_recent_activity','arguments':{}}})
        self.assertIn('saved safely', read['result']['content'][0]['text'])

    def test_sanitizes_known_sensitive_keys(self):
        with Nerve(self.root) as n:
            n.observe('auth','auth', state={'api_key':'please-hide-me','status':'ready'})
            obj=n.context('auth')
            self.assertEqual(obj['state']['api_key'],'[REDACTED]')
            self.assertNotIn('please-hide-me',json.dumps(n.recent())+json.dumps(obj))

    def test_scanner_repeat_does_not_delete_manual_description(self):
        (self.root / 'handler.js').write_text('export function selectSquare() {}')
        with Nerve(self.root) as n:
            n.scan()
            n.observe('symbol:handler.js:selectSquare','selectSquare',description='Validated by owner',aliases=['interaction point'])
            n.scan()
            self.assertEqual(n.context('symbol:handler.js:selectSquare')['description'],'Validated by owner')

    def test_historical_retrieval_works_without_fts5(self):
        with Nerve(self.root) as n:
            n.observe('old', 'Old subsystem')
            n.observe('new', 'New subsystem')
            n.event('old','failure','rare blue-crane callback regression')
            for i in range(40):
                n.event('new','note', f'unrelated routine message {i}')
            n._fts_ready=False
            q=n.resolve('rare blue crane callback regression')
            self.assertEqual(q['candidates'][0]['target_id'],'old')

    def test_ambiguous_objects_not_authorized_for_action(self):
        with Nerve(self.root) as n:
            n.observe('one','Shared dialog')
            n.observe('two','Shared dialog')
            result=n.resolve('Shared dialog')
            self.assertEqual(result['decision'],'needs_confirmation')
            self.assertFalse(result['may_act_without_verification'])

if __name__ == '__main__':
    unittest.main()
