# NERVE v0.5 — install in your own project

A private, **local-first context database** for AI agents. No server, network access or API key needed. Python 3.11+.

## 1. Install the included wheel

Unzip the release first. Use a Python environment available to your AI editor:

```bash
python -m pip install --no-index --no-deps ./dist/nerve_agent_memory-0.5.0-py3-none-any.whl
```

`--no-index` guarantees no package-index downloads. If you use a virtual environment, point your editor's MCP config to that environment's Python. No `npm install` is needed to use NERVE.

## 2. Initialize a project

```bash
nerve --project /absolute/path/to/your-project init
nerve --project /absolute/path/to/your-project scan
nerve --project /absolute/path/to/your-project remember "We decided to use offline mode"
nerve --project /absolute/path/to/your-project brief
nerve --project /absolute/path/to/your-project doctor
```

The DB is kept at `/absolute/path/to/your-project/.nerve/memory.sqlite3`. Add `.nerve/` to **that project's** `.gitignore` to keep private memories out of Git.

## 3. Connect an AI editor with MCP

For Cursor, run:

```bash
nerve --project /absolute/path/to/your-project cursor-config --write
```

That creates or safely merges `.cursor/mcp.json`. Restart your MCP host. Ask the agent: *“List available NERVE tools, call get_project_brief, and summarize earlier verified decisions.”*

For another local MCP host, configure a stdio server with the absolute Python path:

```json
{"mcpServers":{"nerve-local":{"command":"/absolute/path/to/python","args":["-m","nerve","--project","/absolute/path/to/your-project","mcp"]}}}
```

Different hosts have different configuration formats and permission prompts. Their live interoperability has not been verified in this release. NERVE only remembers what was indexed, explicitly recorded, or observed by authorized adapters.

## 4. Test it on the included chess game

```bash
cd examples/chess-mini
node --test tests/*.test.mjs
python -m http.server 8000
```

Open `http://localhost:8000`. It's a two-person chess demo with a rule-checking engine, not a computer opponent.

From NERVE's root, run the self-contained memory evaluation:

```bash
PYTHONPATH="$(pwd)" python -m benchmark.chess.run --output benchmark/results/CHESS_DOGFOOD.json
```

On Windows PowerShell, use `$env:PYTHONPATH = (Get-Location).Path` before the Python command.

## Honest status

- 35 Python tests + 16 chess-engine tests passed in the release environment.
- On 48 **in-sample scripted** chess reference questions, NERVE got 38 correct Top-1 IDs; a simplistic flat matching baseline got 30.
- Only 4/12 paraphrases were correct. The ranker needs semantic retrieval and held-out tests.
- A fresh MCP process read previous persisted notes successfully; **no cross-model LLM benchmark** has been run.
- The ~91% smaller retrieval payload versus dumping all history is a **word/punctuation proxy**, not billing-token savings.

Read [the full benchmark report](benchmark/results/CHESS_REPORT.md), [security notes](docs/SECURITY.md), and [README](README.md) before relying on it for critical changes.
