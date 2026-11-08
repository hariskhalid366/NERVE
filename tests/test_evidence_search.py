import tempfile
import unittest
from pathlib import Path
from nerve.core import Nerve
from nerve.mcp_stdio import TOOLS,call_tool

class EvidenceSearchTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.n=Nerve(self.root)
        self.n.observe('t','Target')

    def tearDown(self):
        self.n.close()
        self.temp.cleanup()

    def test_old_note_visible_via_focused_search(self):
        self.n.remember('Old rare octopuscopper investigation','t')
        for i in range(160):self.n.remember(f'new project note {i}','t')
        self.assertNotIn('octopuscopper',str(self.n.context('t')))
        result=self.n.search_evidence('octopuscopper','t')
        self.assertEqual(len(result['results']),1)
        self.assertIn('octopuscopper',result['results'][0]['text'])

    def test_deletion_removes_searchable_entries(self):
        self.n.remember('unique squidrose case','t')
        self.n.event('t','issue','rare squidrose conflict')
        self.assertEqual(len(self.n.search_evidence('squidrose')['results']),2)
        self.n.forget('t')
        self.assertEqual(self.n.search_evidence('squidrose')['results'],[])

    def test_empty_query_invalid_target_and_sql_injection_safe(self):
        self.assertEqual(self.n.search_evidence('and the')['results'],[])
        self.assertTrue(self.n.search_evidence('case','nonexistent')['unknown_target'])
        self.assertEqual(self.n.search_evidence('" OR *')['results'],[])

    def test_project_isolation(self):
        self.n.remember('special durable marbleanchor evidence','t')
        other=self.root/'different';other.mkdir()
        with Nerve(other) as m:
            self.assertEqual(m.search_evidence('marbleanchor')['results'],[])

    def test_fallback_without_fts(self):
        self.n.remember('old unusual wisteriamoon incident','t')
        self.n._fts_ready=False
        result=self.n.search_evidence('wisteriamoon','t')
        self.assertEqual(len(result['results']),1)

    def test_evidence_freshness_after_file_change(self):
        (self.root/'component.py').write_text('def func(): return 1')
        self.n.observe('source','Source function',source_path='component.py')
        self.n.remember('prismgarnet old behavior','source')
        self.assertEqual(self.n.search_evidence('prismgarnet','source')['results'][0]['freshness'],'source_unchanged')
        (self.root/'component.py').write_text('def func(): return 2')
        self.assertEqual(self.n.search_evidence('prismgarnet','source')['results'][0]['freshness'],'source_changed')

    def test_builtin_mcp_exposes_evidence_search(self):
        self.n.remember('past cloverpearl evidence','t')
        self.assertIn('search_evidence',{t['name'] for t in TOOLS})
        results=call_tool(self.root,'search_evidence',{'query':'cloverpearl','target_id':'t'})
        self.assertEqual(len(results['results']),1)

if __name__=='__main__':unittest.main()
