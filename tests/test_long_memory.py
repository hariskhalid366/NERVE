"""Long-lived project retrieval and migration regressions."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from nerve.core import Nerve

class LongMemoryRegression(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
    def tearDown(self):
        self.tmp.cleanup()

    def test_global_memories_cannot_hide_target_history(self):
        with Nerve(self.root) as n:
            n.observe('old','target')
            n.remember('target only regression fix',target_id='old')
            for i in range(120):n.remember(f'unrelated project note {i}')
            target=n.context('old',limit=8)
            self.assertTrue(any(x['text']=='target only regression fix' for x in target['memories']))
            self.assertLessEqual(len(target['memories']),8)

    def test_old_events_retrievable_after_1000_newer_events(self):
        with Nerve(self.root) as n:
            n.observe('old','OldComponent')
            n.event('old','bug','redbishop zigzag yellowdrum fixture')
            n.observe('other','NewComponent')
            for i in range(1000):n.event('other','unrelated',f'unrelated update {i}')
            self.assertEqual(n.resolve('redbishop zigzag yellowdrum')['candidates'][0]['target_id'],'old')

    def test_old_memories_retrievable_after_1000_newer_memories(self):
        with Nerve(self.root) as n:
            n.observe('old','OldComponent')
            n.remember('rustyknight riverglass maplewing regression',target_id='old')
            n.observe('other','NewComponent')
            for i in range(1000):n.remember(f'unrelated note {i}',target_id='other')
            self.assertEqual(n.resolve('rustyknight riverglass maplewing')['candidates'][0]['target_id'],'old')

    def test_forget_removes_search_index_evidence(self):
        with Nerve(self.root) as n:
            n.observe('old','OldComponent')
            n.event('old','bug','coralbreeze zigzag memory')
            n.remember('coralbreeze unique note',target_id='old')
            self.assertTrue(n.resolve('coralbreeze')['candidates'])
            n.forget('old')
            self.assertFalse(n.resolve('coralbreeze')['candidates'])
            self.assertEqual(n.conn.execute('PRAGMA integrity_check').fetchone()[0], 'ok')

    def test_old_database_migrates_and_is_searchable(self):
        with Nerve(self.root) as n:
            n.observe('old','OldComponent')
            n.event('old','bug','lavenderlute ancient incident')
            n.remember('clockworkstar ancient decision',target_id='old')
        db=self.root/'.nerve'/'memory.sqlite3'
        with sqlite3.connect(db) as c:
            for name in ('nerve_events_fts','nerve_memories_fts'):
                c.execute('DROP TABLE IF EXISTS '+name)
            for name in ('nerve_events_fts_ins','nerve_events_fts_del','nerve_memories_fts_ins','nerve_memories_fts_del'):
                c.execute('DROP TRIGGER IF EXISTS '+name)
        with Nerve(self.root) as n:
            self.assertEqual(n.resolve('lavenderlute ancient')['candidates'][0]['target_id'],'old')
            self.assertEqual(n.resolve('clockworkstar ancient')['candidates'][0]['target_id'],'old')

    def test_partial_fts_migration_rebuilds_missing_memory_index(self):
        with Nerve(self.root) as n:
            n.observe('old','OldComponent')
            n.event('old','issue','lemondusk old event')
            n.remember('nightharbor old memory',target_id='old')
        db=self.root/'.nerve'/'memory.sqlite3'
        with sqlite3.connect(db) as c:
            c.execute('DROP TRIGGER IF EXISTS nerve_memories_fts_ins')
            c.execute('DROP TRIGGER IF EXISTS nerve_memories_fts_del')
            c.execute('DROP TABLE nerve_memories_fts')
        with Nerve(self.root) as n:
            self.assertEqual(n.resolve('lemondusk')['candidates'][0]['target_id'],'old')
            self.assertEqual(n.resolve('nightharbor')['candidates'][0]['target_id'],'old')

    def test_fts_unavailable_fallback_preserves_old_event(self):
        with Nerve(self.root) as n:
            n.observe('old','LegacyComponent')
            n.event('old','issue','autumnday special incident')
            n.observe('other','NewComponent')
            for i in range(350):n.event('other','other',f'recent new event {i}')
            n._fts_ready=False
            self.assertEqual(n.resolve('autumnday special')['candidates'][0]['target_id'],'old')

    def test_fts_user_query_syntax_cannot_trigger_query_error(self):
        with Nerve(self.root) as n:
            n.observe('old','CustomComponent')
            n.event('old','issue','evergreenphantom unique incident')
            for query in ('evergreenphantom " OR *', 'evergreenphantom ( AND )', 'evergreenphantom NEAR/3'):
                self.assertEqual(n.resolve(query)['candidates'][0]['target_id'],'old')

    def test_distinct_old_incident_survives_flood_of_common_fts_matches(self):
        with Nerve(self.root) as n:
            n.observe('common','Generic')
            for i in range(3100):n.event('common','update',f'castle common move {i}')
            n.observe('old','Specific')
            n.event('old','incident','neonfire castle regression')
            for i in range(3100):n.event('common','update',f'castle later event {i}')
            result=n.resolve('neonfire castle')
            self.assertEqual(result['candidates'][0]['target_id'],'old')

    def test_context_preserves_project_notes_when_space(self):
        with Nerve(self.root) as n:
            n.observe('t','T')
            n.remember('project decision',target_id='project')
            n.remember('target decision',target_id='t')
            notes=n.context('t',limit=2)['memories']
            self.assertEqual({x['target_id'] for x in notes},{'t','project'})

    def test_persisted_full_history_after_reopen(self):
        with Nerve(self.root) as n:
            n.observe('target','Original')
            n.event('target','regression','marigoldturbo previous failure')
            n.remember('persistent detail',target_id='target')
        with Nerve(self.root) as n:
            self.assertTrue(n._fts_ready)
            self.assertEqual(n.resolve('marigoldturbo previous')['candidates'][0]['target_id'],'target')
            self.assertTrue(any(x['text']=='persistent detail' for x in n.context('target')['memories']))

if __name__=='__main__':unittest.main()
