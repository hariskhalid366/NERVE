# NERVE v0.6 release QA — 2026-10-22

Tested in this environment (Python 3.13, Node 22):

- `PYTHONPATH="$(pwd)" python -m unittest discover -s tests -q` → **35/35 PASS**.
- `cd examples/chess-mini && node --test tests/*.test.mjs` → **16/16 PASS**.
- `python -m benchmark.chess.run --output benchmark/results/CHESS_DOGFOOD.json` → completed; 48 known references plus 10 negatives (see report).
- Local HTTP server GET `/` and `/chess.mjs` → returned expected content. This is **not** automated visual UI testing.
- Installed v0.5 wheel in a fresh Python virtual environment with `pip install --no-index --no-deps` → PASS.
- In that environment, initialized two distinct projects; notes in project A were not present in project B → PASS.
- Offline MCP JSON-RPC subprocess initialized, listed 8 tools, resolved a chess target and recovered a seeded earlier note → PASS.

Not tested: full interactive browser clicking in a real browser; a live Cursor/Claude session; real cross-LLM continuation, token costs, data sizes over time, sustained load, network services or production security boundaries. No claim of model-level improvement is made.
