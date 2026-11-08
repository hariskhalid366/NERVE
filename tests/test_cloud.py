"""Single-instance Cloud REST contract tests; require pip install .[cloud]."""
import os
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from nerve.cloud_api import app
from nerve.cloud_client import NerveCloudClient

AGENT = "a" * 48
OBSERVER = "o" * 48


class CloudContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.config = patch.dict(os.environ, {
            "NERVE_DATA_DIR": self.temp.name,
            "NERVE_AGENT_TOKEN": AGENT,
            "NERVE_OBSERVER_TOKEN": OBSERVER,
        })
        self.config.start()
        self.client = TestClient(app)
        self.agent = {"Authorization": "Bearer " + AGENT}
        self.observer = {"Authorization": "Bearer " + OBSERVER}

    def tearDown(self):
        self.client.close()
        self.config.stop()
        self.temp.cleanup()

    def post(self, path, data, headers):
        return self.client.post(path, json=data, headers=headers)

    def test_observe_resolve_and_context_persist(self):
        sample = {"target_id": "ui:save", "label": "Save settings", "kind": "button", "aliases": ["apply preferences"], "state": {"enabled": True, "api_token": "do-not-store"}}
        self.assertEqual(self.post("/v1/observe", sample, self.observer).status_code, 200)
        self.assertEqual(self.post("/v1/event", {"target_id": "ui:save", "event_type": "error", "message": "Timeout on save"}, self.observer).status_code, 200)
        self.assertEqual(self.post("/v1/remember", {"text": "Investigate timeout", "target_id": "ui:save"}, self.agent).status_code, 200)
        result = self.post("/v1/resolve", {"query": "preferences save timeout"}, self.agent)
        self.assertEqual(result.status_code, 200)
        self.assertTrue(any(x["target_id"] == "ui:save" for x in result.json()["candidates"]))
        context = self.post("/v1/context", {"target_id": "ui:save"}, self.agent).json()
        self.assertTrue(context["found"])
        self.assertEqual(context["state"]["api_token"], "[REDACTED]")
        self.assertEqual(context["origin"], "remote-observer")
        self.assertTrue(context["events"])
        self.assertTrue(context["memories"])
        with TestClient(app) as another_process_like_client:
            reread = another_process_like_client.post("/v1/context", json={"target_id": "ui:save"}, headers=self.agent).json()
            self.assertEqual(reread["target_id"], "ui:save")

    def test_no_auth_and_role_isolation(self):
        self.assertEqual(self.post("/v1/recent", {}, {}).status_code, 401)
        self.assertEqual(self.post("/v1/recent", {}, self.observer).status_code, 401)
        self.assertEqual(self.post("/v1/observe", {"target_id": "x", "label": "x"}, self.agent).status_code, 401)
        self.assertEqual(self.post("/v1/recent", {}, self.agent).status_code, 200)

    def test_secret_misconfiguration_fails_closed(self):
        with patch.dict(os.environ, {"NERVE_AGENT_TOKEN": "short"}):
            self.assertEqual(self.post("/v1/recent", {}, self.agent).status_code, 503)

    def test_rejects_oversized_json_and_unrecognized_fields(self):
        r = self.post("/v1/remember", {"text": "x" * 33000}, self.agent)
        self.assertEqual(r.status_code, 413)
        r = self.post("/v1/observe", {"target_id": "x", "label": "x", "origin": "forged"}, self.observer)
        self.assertEqual(r.status_code, 400)
        r = self.post("/v1/resolve", {"query": "x", "limit": 100}, self.agent)
        self.assertEqual(r.status_code, 400)

    def test_client_https_default_with_loopback_exception(self):
        self.assertRaises(ValueError, NerveCloudClient, url="http://example.com", token=AGENT)
        self.assertRaises(ValueError, NerveCloudClient, url="https://example.com/v1", token=AGENT)
        n = NerveCloudClient(url="http://127.0.0.1:8000", token=AGENT)
        self.assertEqual(n.url, "http://127.0.0.1:8000")


if __name__ == "__main__":
    unittest.main()
