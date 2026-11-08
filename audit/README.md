# Extended audit harness

This directory contains deterministic scripts and their raw outputs used in the **November 8, 2026** capability audit.

- `run_extended.py`: chess retrieval and paired statistics, global-note crowding, old-history eviction, freshness, redaction smoke, ambiguous requests, unseeded source lookup, storage/latency sweeps (100/500/1500/3000 targets), 8-worker SQLite writes, crash restart and project isolation.
- `payload_bytes.py`: JSON payload size versus full-history dump (not billed provider tokens).
- `self_dogfood.py`: stores and retrieves NERVE regression results in a new MCP subprocess as a local self-use demonstration.
- `results-v0.6.json` and `results-v0.7.json`: archived version-specific outputs. Hardware and filesystem timings will vary. The older version's results were collected with its original source, not by changing a version label.

Run from the repository root with Python 3.11+:

```bash
PYTHONPATH=. python audit/run_extended.py
PYTHONPATH=. python audit/payload_bytes.py
PYTHONPATH=. python audit/self_dogfood.py
```

The original and stress chess cases were authored around specific seeded targets. Do not call them a representative sample of all developer tasks, and do not claim any measurements of LLM model-token usage or true cross-model task completion.
