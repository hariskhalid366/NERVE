"""Local-first ergonomic and safety contract checks (no external LLM calls)."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from nerve.core import Nerve
from nerve.brief import project_brief
from nerve.onboarding import cursor_config, save_cursor_config
from nerve.git_observer import capture_commit, install_post_commit_hook


class LocalWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory(prefix='nerve-local-')
        self.root = Path(self.t.name)

    def tearDown(self):
        self.t.cleanup()

    def _git(self, *args):
        return subprocess.run(['git', '-C', str(self.root), *args], capture_output=True,
                              text=True, check=True).stdout.strip()

    def test_cursor_host_config_is_scoped_to_explicit_project(self):
        conf = cursor_config(self.root)
        command = conf['mcpServers']['nerve-local']
        self.assertEqual(Path(command['args'][3]).resolve(), self.root.resolve())
        self.assertIn('stdio', command['type'])

    def test_cursor_merge_preserves_existing_servers(self):
        folder = self.root / '.cursor'; folder.mkdir()
        path = folder / 'mcp.json'
        path.write_text(json.dumps({'mcpServers': {'existing': {'command': 'python'}}}))
        self.assertEqual(save_cursor_config(self.root).resolve(), path.resolve())
        combined = json.loads(path.read_text())
        self.assertIn('existing', combined['mcpServers'])
        self.assertIn('nerve-local', combined['mcpServers'])
        with self.assertRaisesRegex(ValueError, 'already exists'):
            save_cursor_config(self.root)

    def test_cursor_never_overwrites_invalid_json(self):
        folder = self.root / '.cursor'; folder.mkdir()
        path = folder / 'mcp.json'; path.write_text('{broken')
        with self.assertRaises(ValueError): save_cursor_config(self.root)
        self.assertEqual(path.read_text(), '{broken')

    def test_brief_after_database_reopen(self):
        with Nerve(self.root) as agent_a:
            agent_a.observe('feature:login','Login screen', 'ui')
            agent_a.event('feature:login','fix','Resolved duplicated requests')
            agent_a.remember('Keep the retry interval at five seconds','feature:login',author='agent-a')
        with Nerve(self.root) as agent_b:
            summary = project_brief(agent_b)
            self.assertEqual(summary['identity_count'], 1)
            self.assertIn('five seconds', summary['recent_memories'][0]['text'])
            self.assertEqual(summary['recent_events'][0]['event_type'], 'fix')

    def test_query_with_only_incidental_overlap_requires_confirmation(self):
        with Nerve(self.root) as n:
            n.observe('customer:billing','Billing history','panel')
            out = n.resolve('billing related asteroid coordinates')
            self.assertEqual(out['decision'], 'needs_confirmation')
            self.assertFalse(out['may_act_without_verification'])

    def test_git_capture_is_metadata_only_and_no_secret_file_paths(self):
        self._git('init', '-q'); self._git('config','user.email','test@example.com'); self._git('config','user.name','Test')
        (self.root/'file.py').write_text('def demo(): return 1\n')
        (self.root/'.env').write_text('SECRET=do_not_store')
        self._git('add','file.py','.env'); self._git('commit','-qm','do_not_store-in-message')
        result = capture_commit(self.root)
        self.assertEqual(result['source_files'], ['file.py'])
        with Nerve(self.root) as n:
            data = n.context('git:repository')
            self.assertTrue(data['found'])
            stored = json.dumps(data)
            self.assertNotIn('do_not_store', stored)
            self.assertNotIn('.env', stored)
            self.assertIn('file.py', stored)

    def test_hook_refuses_to_overwrite_existing(self):
        self._git('init','-q')
        path = install_post_commit_hook(self.root)
        self.assertTrue(path.is_file())
        if sys.platform != 'win32':
            self.assertTrue(path.stat().st_mode & 0o100)
        with self.assertRaises(ValueError): install_post_commit_hook(self.root)

    def test_multiple_agent_connections_can_write_shared_notes(self):
        from concurrent.futures import ThreadPoolExecutor
        with Nerve(self.root) as n: n.observe('feature:upload', 'Upload process')
        def worker(i):
            with Nerve(self.root) as n:
                for k in range(5):
                    n.remember(f'Worker {i}, note {k}',target_id='feature:upload',author=f'agent-{i}')
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(worker, range(4)))
        with Nerve(self.root) as n:
            count=n.conn.execute("SELECT COUNT(*) FROM memories WHERE target_id='feature:upload'").fetchone()[0]
            self.assertEqual(count,20)

    def test_installed_hook_records_real_post_commit(self):
        self._git('init','-q')
        self._git('config','user.email','test@example.com')
        self._git('config','user.name','Test')
        hook=install_post_commit_hook(self.root)
        (self.root/'hello.py').write_text('def hello(): return True\n')
        self._git('add','hello.py')
        self._git('commit','-qm','first commit')
        with Nerve(self.root) as n:
            self.assertTrue(n.context('git:repository')['found'])
            self.assertEqual(n.context('git:repository')['state']['changed_source_files'], ['hello.py'])
        self.assertTrue(hook.exists())

    def test_process_boundary_local_cli(self):
        with Nerve(self.root) as n:
            n.remember('A changed the offline mode requirements',category='decision',author='agent-a')
        p = subprocess.run([sys.executable,'-m','nerve','--project',str(self.root),'brief'],
                           capture_output=True,text=True,check=True)
        res = json.loads(p.stdout)
        self.assertIn('offline mode', res['recent_memories'][0]['text'])

if __name__ == '__main__': unittest.main()
