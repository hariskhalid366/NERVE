"""Example adapter: authorized telemetry from an app running on this machine.

Run: python examples/send_observation.py /path/to/project
Requires an active `nerve --project /path/to/project listen` process.
"""
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen

project = Path(sys.argv[1]).expanduser().resolve()
token = (project / ".nerve" / "collector-token").read_text().strip()

observation = {
    "target_id": "ui:preferences:save",
    "label": "Save preferences",
    "kind": "ui-element",
    "aliases": ["save changes", "save button", "apply preferences"],
    "description": "Primary save action in Preferences panel",
    "locator": "test-id:preferences-save",
    "state": {"visible": True, "enabled": False, "reason": "Validation is pending"}
}
request = Request(
    "http://127.0.0.1:8765/v1/observe",
    method="POST", data=json.dumps(observation).encode(),
    headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"}
)
with urlopen(request, timeout=5) as response:
    print(response.read().decode())
