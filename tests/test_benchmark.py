import json
from pathlib import Path
import tempfile
import unittest
from benchmark.smoke import run
from benchmark.agent_eval import evaluate,export,gold_cases,wilson

class BenchmarkTests(unittest.TestCase):
    def test_smoke_summary(self):
        result=run()
        self.assertEqual(result['summary']['n_positive'],80)
        self.assertEqual(result['summary']['n_negative'],20)
        self.assertEqual(result['summary']['cross_session_exact_id_persistence'],1)
        self.assertEqual(len(result['cases']),100)
        self.assertEqual(result['summary']['actual_llm_token_efficiency'],'NOT_MEASURED')
    def test_export_blinded(self):
        with tempfile.TemporaryDirectory() as root:
            export(Path(root))
            public=(Path(root)/'agent_prompts.jsonl').read_text()
            self.assertNotIn('47-second',public)
            self.assertEqual(len(public.splitlines()),80)
            self.assertIn('47-second',(Path(root)/'gold_private.json').read_text())
    def test_score_real_runs_but_not_mock_as_real(self):
        with tempfile.TemporaryDirectory() as root:
            file=Path(root)/'runs.jsonl'
            good=gold_cases()['T00Q0']
            line={'case_id':'T00Q0','arm':'nerve','model':'example','seed':0,
                  'target_id':good['target_id'],'answer':good['answer'],
                  'input_tokens':412,'output_tokens':60,'latency_ms':1500,
                  'agent_a':'A','agent_b':'B','handoff_completed':True}
            file.write_text(json.dumps(line)+'\n')
            score=evaluate(file)
            self.assertEqual(score['model_arm_stats']['example|nerve']['cross_agent_strict_accuracy'],1)
            file.write_text(json.dumps({**line,'source':'EXAMPLE_DO_NOT_SCORE_AS_REAL'})+'\n')
            with self.assertRaises(ValueError):evaluate(file)
    def test_wilson(self):
        self.assertEqual(wilson(0,0),[None,None])
        self.assertTrue(wilson(9,10)[0]<0.9)

if __name__=='__main__':unittest.main()
