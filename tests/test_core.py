import tempfile
import unittest
from pathlib import Path
from nerve.core import Nerve, redact


class NerveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.n = Nerve(self.root)

    def tearDown(self):
        self.n.close()
        self.temp.cleanup()

    def test_observation_and_resolution(self):
        self.n.observe("ui:save", "Save button", "ui", aliases=["submit changes"],
                       state={"enabled": False, "access_token": "secret"})
        matches = self.n.resolve("submit changes")['candidates']
        self.assertEqual(matches[0]["target_id"], "ui:save")
        context = self.n.context("ui:save")
        self.assertEqual(context["state"]["access_token"], "[REDACTED]")
        self.assertFalse(context["state"]["enabled"])

    def test_event_memory_and_delete(self):
        self.n.observe("service:checkout", "Checkout", "service")
        self.n.event("service:checkout", "error", "Gateway timeout", {"password": "bad"})
        self.n.remember("Retry was agreed for checkout", "service:checkout")
        context = self.n.context("service:checkout")
        self.assertEqual(context["events"][0]["payload"]["password"], "[REDACTED]")
        self.assertEqual(len(context["memories"]), 1)
        deleted = self.n.forget("service:checkout")
        self.assertEqual(deleted["targets"], 1)
        self.assertFalse(self.n.context("service:checkout")["found"])

    def test_static_index_and_exclusions(self):
        (self.root / "public.tsx").write_text("export function SavePanel() {}\nexport const SaveButton = () => null")
        (self.root / ".env").write_text("API_KEY=SECRET")
        (self.root / "node_modules").mkdir()
        (self.root / "node_modules" / "ignore.tsx").write_text("export function IgnoreMe() {}")
        summary = self.n.scan()
        self.assertEqual(summary["files_indexed"], 1)
        self.assertTrue(self.n.context("symbol:public.tsx:SavePanel")["found"])
        self.assertFalse(self.n.context("symbol:node_modules/ignore.tsx:IgnoreMe")["found"])

    def test_events_are_resolvable_without_matching_label(self):
        self.n.observe("service:payments", "Billing gateway", "service")
        self.n.event("service:payments", "error", "Unexpected timeout during payment authorization")
        result = self.n.resolve("unexpected timeout")
        self.assertEqual(result["candidates"][0]["target_id"], "service:payments")
        self.assertIn("history:", " ".join(result["candidates"][0]["evidence"]))

    def test_project_boundary(self):
        with self.assertRaises(ValueError):
            self.n.observe("x", "x", source_path="../../etc/passwd")
        with self.assertRaises(ValueError):
            self.n.observe("x", "x", source_path=".env")

    def test_memory_isolation(self):
        other = self.root / "other"
        other.mkdir()
        self.n.observe("id", "first")
        with Nerve(other) as n2:
            self.assertFalse(n2.context("id")["found"])

    def test_empty_query(self):
        self.assertEqual(self.n.resolve("??")["candidates"], [])
        self.assertIn("[REDACTED]", redact({"Authorization": "Bearer abc"}).values())


if __name__ == "__main__":
    unittest.main()

class CollectorTests(unittest.TestCase):
    def test_collector_requires_token(self):
        from nerve.collector import create_server, collector_token
        import json
        import threading
        from urllib.error import HTTPError
        from urllib.request import Request, urlopen
        with tempfile.TemporaryDirectory() as d:
            srv = create_server(d, 0)
            thread = threading.Thread(target=srv.serve_forever, daemon=True)
            thread.start()
            try:
                url = f"http://127.0.0.1:{srv.server_port}/v1/observe"
                obs = json.dumps({"target_id": "A", "label": "Alpha"}).encode()
                with self.assertRaises(HTTPError) as failure:
                    urlopen(Request(url, data=obs, headers={"Content-Type": "application/json"}), timeout=3)
                self.assertEqual(failure.exception.code, 401)
                headers = {"Content-Type": "application/json", "Authorization": "Bearer " + collector_token(d)}
                with urlopen(Request(url, data=obs, headers=headers), timeout=3) as ok:
                    self.assertEqual(json.loads(ok.read())["target_id"], "A")
                with Nerve(d) as n:
                    self.assertTrue(n.context("A")["found"])
            finally:
                srv.shutdown(); thread.join(2); srv.server_close()
