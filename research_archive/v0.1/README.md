# NERVE — project-local memory and observation for AI agents

**Prototype v0.1, October 2026.** An open, model-independent 'nervous system' that combines source metadata, **stable object identities**, opt-in runtime observations, events, and explicit decisions. AI hosts can retrieve this information through a Model Context Protocol (MCP) server.

> This does not change an AI model's internal weights or give it ambient senses or personal autonomy. It makes *user-authorized observations* accessible through a connected tool. Without observation instrumentation, live state is **unknown**.

## What works now

- Persistent **per-project SQLite** memory at `PROJECT/.nerve/memory.sqlite3`; no cloud or embedding API.
- **Static index** of source filenames and declared symbols. Skips common build directories and secret-file types; stores names and symbols, **not full source files**. Heuristic indexing is not a language server or AST parser.
- **Runtime object registry** with stable IDs, names, synonyms, source paths, locators, and most-recent reported state.
- **Event timeline** and project/target-scoped decisions.
- **Natural-language candidate lookup** using labels, aliases, paths, descriptions, and recent history. Returns ranked evidence, never makes claims of certainty.
- **Opt-in localhost HTTP collector** secured by a project-unique bearer token. Receives observations and events only; cannot execute commands.
- **MCP 2.x stdio server** exposing discovery, evidence, observations, and decisions to an MCP-compatible AI host.
- **Explicit target deletion**, basic sensitive field redaction, project-scoped source boundaries.

## Quickstart (no dependencies for core CLI)

Requires Python **3.11+**.

```bash
# Unzip NERVE and enter the nerve-prototype directory.
cd nerve-prototype

# Here we use a separate project directory for the demo.
mkdir -p ./demo-project
python -m nerve --project ./demo-project init

# Register a known object from a sample observation.
python -m nerve --project ./demo-project observe examples/observation.json

# Ask for the object without screenshots.
python -m nerve --project ./demo-project resolve "the settings save button"
python -m nerve --project ./demo-project context "ui:settings:save-button"

# Record evidence that the object failed.
python -m nerve --project ./demo-project event "ui:settings:save-button" error "Save action timed out"
python -m nerve --project ./demo-project remember "Retry logic was requested after the timeout" --target "ui:settings:save-button"
python -m nerve --project ./demo-project resolve "the button with timeout yesterday"
```

For an existing project (any supported language), point `--project` at its root and call `scan`:

```bash
python -m nerve --project /absolute/path/to/your-project scan
python -m nerve --project /absolute/path/to/your-project resolve "settings screen"
```

### Connect a running application automatically (explicit opt-in)

Start the local listener in terminal A:

```bash
python -m nerve --project ./demo-project listen --port 8765
```

The first run creates `./demo-project/.nerve/collector-token` (owner-only permissions on POSIX). Provide that token to a **trusted local adapter** only. Run the example in terminal B:

```bash
python examples/send_observation.py ./demo-project
python -m nerve --project ./demo-project resolve "preferences save"
```

The adapter POSTs the **structured object identity and state**, not any screenshot. This first version includes the receiver and example sender; integrations with browsers, desktop apps, IDEs, or devices must be written explicitly for those environments. No observer starts on its own.

HTTP collector contract:

- `POST http://127.0.0.1:8765/v1/observe` with `Authorization: Bearer <token>` and `Content-Type: application/json`.
- `POST http://127.0.0.1:8765/v1/event` with `{"target_id":"ui:preferences:save","event_type":"click","message":"Button pressed","payload":{...}}`.
- Maximum request body: 32 KiB.
- No endpoints for arbitrary code execution, internet access, scraping, system microphone, camera, or editing files.

## MCP connection: ChatGPT-compatible hosts, Claude, and other agents

MCP is the transport/contract; the actual AI **host must support and permit MCP tools**. AI models do not automatically discover this server merely because it is installed.

Install the official MCP Python SDK v2:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
pip install -e '.[mcp]'
```

Configure your MCP host to launch NERVE via stdio (edit placeholders to absolute paths):

```json
{
  "mcpServers": {
    "nerve": {
      "command": "/ABS/PATH/nerve-prototype/.venv/bin/python",
      "args": ["-m", "nerve", "--project", "/ABS/PATH/your-project", "mcp"]
    }
  }
}
```

This is an **illustrative MCP server entry**, not a universal client settings filename. Each host uses its own configuration format and support level. The project argument is fixed by the user/host configuration, not arbitrarily chosen by the model.

Published tools:

| Tool | Intent |
| --- | --- |
| `scan_project` | Index static source metadata in permitted directories |
| `resolve_target(query)` | Find ranked object candidates with evidence |
| `get_target_context(target_id)` | Read identity, latest reported state, history, and decisions |
| `get_recent_activity(limit)` | Retrieve recent event and decision history |
| `observe_target(...)` | Write structured observation from an authorized source |
| `record_event(...)` | Attach telemetry to an existing target |
| `remember_context(...)` | Persist an explicit project/target-scoped decision or fact |

Target deletion is deliberately a **local CLI-only action** (`nerve forget`), not an MCP tool, until explicit host/user approval can be enforced reliably.

Example agent workflow:

1. User: "The save thing we discussed yesterday is failing again."
2. Agent calls `resolve_target("save thing failing")`.
3. NERVE returns candidates and **matching evidence**; agent asks for clarification if ambiguous.
4. Agent calls `get_target_context("ui:preferences:save")`.
5. It now sees that object's identity, last observation (timestamp), events, and recorded decisions. If fresh observation is missing, it says so.
6. If the host also provides an authorized **action tool**, the agent may attempt a change and then verify the outcome using new events. NERVE itself does not grant action permissions.

## Structure

```text
nerve/
  core.py          SQLite storage, source indexing, target discovery, evidence
  cli.py           Local command-line interface
  collector.py     Bearer-token-protected loopback observation receiver
  mcp_server.py    Official MCP Python SDK v2 stdio tool adapter
  __main__.py      python -m nerve entry
examples/
  observation.json
  send_observation.py
 tests/
  test_core.py
```

## Tests

```bash
python -m unittest discover -s tests -v
```

These test the offline core, project boundaries, redaction examples, identity lookup, histories, deletion, and live collector authorization. The MCP adapter requires the separate SDK installation and has not been integration-tested against every AI host.

## Security and limitations

- NERVE is **local-only by default**. It makes no outbound requests. The project folder, token, observation feeds and host-tool permissions should be under the user's control.
- An application's observation adapter **must be installed and enabled with user consent**. This prototype does not capture screens, keystrokes, ambient audio, or other personal information covertly.
- The collector uses a single shared project token, **not** per-user identity/role scopes. Do not expose it to the public internet; localhost alone does not justify trusting arbitrary callers. Production multi-user deployment needs a real authorization model.
- Redaction is **best-effort**, not a complete DLP/PII system. Avoid submitting credentials, personal data, proprietary content or other secrets. The example receiver accepts arbitrary descriptive text. Decide what your adapter is permitted to collect.
- Source indexing is heuristic. It does not reliably identify dynamic runtime objects or all language constructs; it never validates application behavior.
- A live observation describes **the state reported at its timestamp**, not necessarily the state right now. High confidence requires fresh source-specific telemetry.
- Tool outputs can contain malicious instructions embedded in code comments/observations. Treat them as *data*, not higher-priority prompts.
- Database is not encrypted at rest. Keep `.nerve/` out of version control; use operating-system filesystem access controls and disk encryption.
- There are no background OS daemons, auto-sync connectors, screenshot analysis, full text vector search, semantic embeddings, or hardware sensor integration in v0.1.

## Where to go next

**Phase 1 (here):** Local project identity registry + source hints + explicit memory + telemetry ingest + MCP queries.

**Phase 2:** Browser/desktop/mobile/device adapters, object-identity reconciliation, subscriptions, event schemas, source provenance, deletion policy and observation permissions.

**Phase 3:** Temporal reasoning over changes, embeddings/local reranking, uncertain reference clarification, verification plans, multi-agent handoffs, audit trail, and per-agent read/write scopes.

**Phase 4:** Optional physical sensors (camera, microphone, environmental sensors) with informed consent, device-level isolation, and strict lifecycle controls. These expose observations, **not subjective experience or free-ranging access**.

### Design principle

**Every claim should have a chain of evidence**: object ID → source/observation → timestamp → state/transition → verification. When evidence is absent, the system should report uncertainty rather than fabricate awareness.

MIT licensed; ready to prototype with any developer or AI host that can connect an MCP server.
