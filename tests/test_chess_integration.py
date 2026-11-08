"""Regression for a real-world Node.js ESM project. No cloud or LLM needed."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from nerve.core import Nerve

CHESS = Path(__file__).resolve().parents[1]/'examples'/'chess-mini'


class ChessIntegration(unittest.TestCase):
    def test_esm_files_are_indexed_and_searchable(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            for name in ('chess.mjs','app.mjs','index.html','style.css'):
                (target/name).write_bytes((CHESS/name).read_bytes())
            with Nerve(target) as nerve:
                result=nerve.scan()
                self.assertEqual(result['files_indexed'],4)
                self.assertGreater(result['symbols_indexed'],10)
                self.assertTrue(nerve.context('symbol:chess.mjs:legalMoves')['found'])
                self.assertTrue(nerve.context('symbol:app.mjs:render')['found'])
                self.assertEqual(nerve.resolve('legalMoves')['candidates'][0]['target_id'],'symbol:chess.mjs:legalMoves')

    @unittest.skipUnless(subprocess.run(['which','node'],capture_output=True).returncode==0,'requires Node.js')
    def test_chess_engine_regressions(self):
        run=subprocess.run(['node','--test','tests/rules.test.mjs'], cwd=CHESS,
                           text=True,capture_output=True,timeout=20)
        self.assertEqual(run.returncode,0,run.stdout+'\n'+run.stderr)
        self.assertIn('# pass 16',run.stdout)

    def test_history_uses_descriptive_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            with Nerve(d) as n:
                n.observe('symbol:target', 'sanitizeInput', aliases=['input guard'])
                n.event('symbol:target','bug','Payment calculation overflow after negative discount input')
                n.observe('symbol:noise','discount',description='Some unrelated display element')
                out=n.resolve('the payment calculation overflow after a negative discount')
                self.assertEqual(out['candidates'][0]['target_id'],'symbol:target')
                self.assertFalse(out['may_act_without_verification'])

    def test_unrelated_question_does_not_fabricate_target(self):
        with tempfile.TemporaryDirectory() as d:
            with Nerve(d) as n:
                n.observe('symbol:move','legalMoves',description='Chess game legal move generator')
                result=n.resolve('where is the satellite tracking module')
                self.assertEqual(result['candidates'],[])
                self.assertEqual(result['decision'],'no_match')

if __name__=='__main__':unittest.main()
