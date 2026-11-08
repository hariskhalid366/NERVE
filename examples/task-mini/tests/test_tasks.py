from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tasks import Task, validate_deadline, parse_task, save_tasks, load_tasks, filter_tasks, delete_task, render_list, mark_complete

class TaskTests(unittest.TestCase):
    def test_deadline_validation(self):
        self.assertEqual(validate_deadline('2026-11-15'),'2026-11-15')
        with self.assertRaises(ValueError): validate_deadline('tomorrow')
    def test_parser_rejects_missing_title(self):
        with self.assertRaises(ValueError): parse_task('{"task_id":"x"}')
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'tasks.json'; items=[Task('a','Write docs')]
            save_tasks(p,items)
            self.assertEqual(load_tasks(p),items)
    def test_filters(self):
        tasks=[Task('a','One'),Task('b','Two','done')]
        self.assertEqual([t.task_id for t in filter_tasks(tasks,'done')],['b'])
        self.assertEqual([t.task_id for t in delete_task(tasks,'a')],['b'])
    def test_mark_and_render(self):
        changed=mark_complete([Task('a','Write docs')],'a')
        self.assertEqual(changed[0].status,'done')
        self.assertIn('Write docs [done]',render_list(changed))
if __name__=='__main__': unittest.main()
