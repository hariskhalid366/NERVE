"""Regression tests for evidence revision binding and repeat scans."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from nerve.core import Nerve


class EvidenceFreshnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='nerve-evidence-')
        self.root = Path(self.tmp.name)
        self.src = self.root/'engine.mjs'
        self.src.write_text('export function legalMoves() { return []; }\n')

    def tearDown(self):
        self.tmp.cleanup()

    def test_source_revision_tracks_events_and_memories_across_reopen(self):
        with Nerve(self.root) as a:
            a.scan()
            a.event('symbol:engine.mjs:legalMoves', 'test', 'passed old revision')
            a.remember('Pinned rook test passed','symbol:engine.mjs:legalMoves')
            initial=a.context('symbol:engine.mjs:legalMoves')
            self.assertEqual(initial['events'][0]['freshness'],'source_unchanged')
            self.assertEqual(initial['memories'][0]['freshness'],'source_unchanged')
        self.src.write_text('export function legalMoves() { return ["changed"]; }\n')
        with Nerve(self.root) as b:
            before=b.context('symbol:engine.mjs:legalMoves')
            self.assertEqual(before['events'][0]['freshness'],'source_changed')
            self.assertEqual(before['memories'][0]['freshness'],'source_changed')
            b.scan()
            after=b.context('symbol:engine.mjs:legalMoves')
            self.assertEqual(after['events'][0]['freshness'],'source_changed',
                             'Re-scanning must not launder old evidence into current evidence')
            b.remember('New regression passed','symbol:engine.mjs:legalMoves')
            final=b.context('symbol:engine.mjs:legalMoves')
            self.assertEqual(final['memories'][0]['freshness'],'source_unchanged')
            self.assertEqual(final['memories'][1]['freshness'],'source_changed')

    def test_missing_file_does_not_erase_past_memories(self):
        with Nerve(self.root) as a:
            a.scan()
            a.remember('Past implementation verified','file:engine.mjs')
        self.src.unlink()
        with Nerve(self.root) as b:
            data=b.context('file:engine.mjs')
            self.assertTrue(data['found'])
            self.assertEqual(data['memories'][0]['freshness'],'source_missing')

    def test_rescan_preserves_human_curated_metadata(self):
        with Nerve(self.root) as n:
            n.scan()
            n.observe('symbol:engine.mjs:legalMoves','legalMoves','source-symbol',
                      'Important pin safety checker',['king pinned on back rank'],
                      'engine.mjs',origin='human-reviewed')
            n.scan()
            item=n.context('symbol:engine.mjs:legalMoves')
            self.assertEqual(item['origin'],'human-reviewed')
            self.assertIn('king pinned',item['aliases'][0])
            self.assertIn('Important pin',item['description'])

    def test_old_sqlite_schema_is_upgraded_without_dropping_data(self):
        folder=self.root/'.nerve';folder.mkdir()
        conn=sqlite3.connect(folder/'memory.sqlite3')
        conn.execute('CREATE TABLE events (id INTEGER PRIMARY KEY, target_id TEXT, event_type TEXT, message TEXT, payload TEXT, created_at TEXT)')
        conn.execute('CREATE TABLE memories (id INTEGER PRIMARY KEY, target_id TEXT, category TEXT, text TEXT, author TEXT, created_at TEXT)')
        conn.execute('INSERT INTO memories VALUES (1,\'project\',\'decision\',\'legacy decision\',\'human\',\'2026-01-01\')')
        conn.commit();conn.close()
        with Nerve(self.root) as n:
            self.assertEqual(n.conn.execute('SELECT text FROM memories').fetchone()[0],'legacy decision')
            self.assertIn('source_digest',[x[1] for x in n.conn.execute('PRAGMA table_info(memories)')])
            self.assertEqual(n.conn.execute('SELECT source_digest FROM memories').fetchone()[0],'')

    def test_unanchored_memory_is_not_falsely_verified(self):
        with Nerve(self.root) as n:
            n.observe('feature:theme','Theme feature',origin='user')
            n.remember('I think it works','feature:theme')
            out=n.context('feature:theme')
            self.assertEqual(out['memories'][0]['freshness'],'unanchored')

if __name__ == '__main__': unittest.main()

class MissingSourceCandidateTests(unittest.TestCase):
    def test_removed_file_requires_confirmation(self):
        with tempfile.TemporaryDirectory(prefix='nerve-missing-') as td:
            root=Path(td)
            src=root/'plugin.py'
            src.write_text('def cache_expiry(): return True\n')
            with Nerve(root) as n:
                n.scan()
                known=n.resolve('cache_expiry')
                self.assertEqual(known['decision'],'supported_candidate')
                src.unlink()
                after=n.resolve('cache_expiry')
                self.assertEqual(after['candidates'][0]['source_status'],'missing')
                self.assertEqual(after['decision'],'needs_confirmation')
