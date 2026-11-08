# NERVE — Local-first project memory for AI coding agents

**Stop starting every AI coding session from zero.** NERVE is an open-source, offline-capable, project-scoped memory server that lets compatible AI agents **record, find, and verify context** across sessions.

**Keywords people use for this problem:** AI context loss, LLM forgetting, context drift, AI coding-agent memory, persistent project memory, multi-agent context sharing, and context-related hallucinations. NERVE is designed to *reduce repeated context reconstruction*; it **does not guarantee that a model will stop hallucinating**.

> **Status: v0.8 release candidate / developer preview.** The local storage and built-in MCP interface are tested. Actual performance improvements in Cursor, Claude Code, Codex or other models are **not yet proven** in independently run agent trials.

## What problem does NERVE solve?

You fix a bug with an AI assistant. Tomorrow the same agent—or a different one—doesn't know what was changed, why you rejected a workaround, or which files were involved. Screenshots, pasted logs, and repeated explanations waste time.

NERVE gives the **project**, not the model, an explicit memory database:

```text
Your project/
├── src/
├── tests/
└── .nerve/
    └── memory.sqlite3      ← stays local; do not commit

Agent A ── records a verified decision ──→ NERVE (SQLite)
Agent B ── retrieves a bounded brief ────→ NERVE (same project)
Agent C ── checks a vague target ────────→ NERVE (candidate + evidence)
```

Memories are accessible **only to tools or users given filesystem access to that project**. NERVE does not silently read private conversations, access model weights, share across accounts, or grant agents new permissions. One agent must write evidence, and another must explicitly retrieve it.

## Key capabilities

| Capability | Works locally? | Important limitation |
| --- | --- | --- |
| Persistent project-scoped memory | ✅ | Facts are only as correct as what the agent/user recorded |
| Cross-process handoff | ✅ | Scripted MCP handoff tested; live cross-model task completion unmeasured |
| Source filename + symbol indexing | ✅ | Indexes static metadata, not runtime state or full-code semantic embeddings |
| Previous decisions, incidents and notes | ✅ | Keep notes concise and verify source freshness |
| Target resolution from descriptions | ✅ Heuristic | Vague paraphrases can fail; all results require agent verification |
| Source revision / stale-evidence hints | ✅ | Hash match is not proof a memory is true |
| Offline stdio MCP tool interface | ✅ | Common 2025-era subset; modern host compatibility requires checks |
| Git post-commit observation | ✅ Opt-in | Only SHA + allowlisted filenames; no commit messages/diffs |
| Universal visual understanding | ❌ | Requires an explicitly authorized observation adapter |
| Cloud synchronization | Not part of this release | Local-first by design |

## Quick start — less than five minutes

**Requirements:** Python **3.11+**, a folder containing your project, and an MCP-compatible host if you want an agent to call tools. Local CLI works without MCP host.

**Option A — offline installer included in the release ZIP:**

```bash
# Use the actual path of the extracted wheel, with no network access:
python -m pip install --no-index --no-deps dist/nerve_agent_memory-0.8.0rc1-py3-none-any.whl
```

**Option B — install from a source checkout:**

```bash
python -m pip install .
```

Then point NERVE at an **existing project directory**:

```bash
nerve --project /absolute/path/to/my-project init
nerve --project /absolute/path/to/my-project scan
nerve --project /absolute/path/to/my-project doctor
nerve --project /absolute/path/to/my-project remember "We rejected polling; use events for this feature."
nerve --project /absolute/path/to/my-project brief
```

On Windows, replace `/absolute/path/to/my-project` with an absolute path such as `C:\\work\\my-project`, and use `py -m pip` if `python` isn't on PATH. The macOS, Windows and Linux host integration still needs user testing; CI will exercise platform-specific tests when published.

### Connect an AI coding agent through MCP

For Cursor, NERVE can **generate a project-scoped MCP configuration**:

```bash
nerve --project /absolute/path/to/my-project cursor-config --write
```

Reload the host. Check its MCP tool listing for `nerve-local`, then ask the agent to call **`get_project_brief`**. For other MCP clients, configure a local **stdio** server using `python -m nerve --project /absolute/path/to/my-project mcp`, following that host's supported configuration format. See [Agent integration](docs/AGENT_INTEGRATION.md) and [Offline setup](docs/OFFLINE_SETUP.md).

**No automatic injection:** the agent **must** invoke NERVE tools. A fresh model without an authorized MCP connection cannot see these memories. Agents should never execute commands or instructions discovered inside a retrieved note.

## How to use it correctly

At task start, request the brief; before acting on a vague reference, resolve a candidate and inspect its context; after a verified decision or bug fix, record a short targeted note. When the source file has changed, revalidate the memory. Untrusted or ambiguous candidates should **not** be treated as facts.

MCP tools currently available: `get_project_brief`, `scan_project`, `resolve_target`, `get_target_context`, `get_recent_activity`, `observe_target`, `record_event`, `remember_context`.

## Benchmarks: measured, not advertised

NERVE ships an offline test harness, a playable chess project and a second tiny task-list project. Results are from **scripted retrieval tests**, not full AI coding-agent evaluations.

| Test | NERVE | Same-data flat-search baseline | Interpretation |
| --- | ---: | ---: | --- |
| Chess: original 48 questions | 38/48 (79.2%) | 30/48 (62.5%) | Tuned set; advantage not generalizable |
| Chess: harder 24 questions | 12/24 (50%) | 12/24 (50%) | No advantage |
| Task-list project: 24 questions | 19/24 (79.2%) | 11/24 (45.8%) | New hand-authored mini-project; very small sample |

The code also tests FTS-backed historical retrieval, malformed protocol messages, file/symlink safety, project isolation and SQLite persistence. See [Release audit](docs/PUBLIC_RELEASE_AUDIT.md) for latencies, stress details, limitations and exact reproduction commands. **JSON payload reduction is not a provider-token or cost reduction.** We have not run official LongMemEval, LoCoMo, MemoryArena or SWE-bench model evaluations.

## Does NERVE fix LLM hallucinations or context-window limits?

**No.** NERVE cannot change the model's context window, guarantee factual answers, or make unobserved code and runtime state visible. It can make *stored project facts and source-linked evidence retrievable* across sessions. That may reduce **context-related mistakes** if the agent uses the evidence correctly. This distinction matters when people search for "AI context hallucination fix", "Claude forgets project" or "Cursor loses context".

## Is it useful for multi-agent development?

Multiple authorized local agents can use the **same `.nerve/memory.sqlite3`** in one project. SQLite concurrency and process-restart persistence have been tested; independent agents solving unseen tasks and genuine cross-model productivity gains have **not** been measured. Keep every project's `.nerve/` private; it is not intended to be copied into public Git repositories.

## Is NERVE privacy-friendly and fully offline?

The local runtime needs no internet to store/retrieve memories. `.nerve/` is excluded in `.gitignore`. **The database is not encrypted by NERVE**; use operating-system access controls and full-disk encryption. Automatic secret filtering is best effort—not a data-loss-prevention guarantee. Don't submit credentials, personal data or proprietary secrets to observers. [Security and responsible disclosure](SECURITY.md).

## Documentation by audience

| If you're… | Start here |
| --- | --- |
| New to NERVE | [Quick start](QUICKSTART.md), [offline install](docs/OFFLINE_SETUP.md) |
| Connecting an agent | [Agent integration and safe operating rules](docs/AGENT_INTEGRATION.md) |
| Evaluating results | [Release audit](docs/PUBLIC_RELEASE_AUDIT.md), [reproducible benchmarks](BENCHMARK.md) |
| Adapting the architecture | [Architecture](ARCHITECTURE.md), [roadmap](docs/ROADMAP.md) |
| Reporting a bug | [Issues and contributions](CONTRIBUTING.md) |
| Publishing this repo | [GitHub discoverability setup](docs/DISCOVERABILITY.md) |

## Test and contribute

```bash
python -m unittest discover -s tests -v
python -m unittest discover -s examples/task-mini/tests -v
node --test examples/chess-mini/tests/*.test.mjs
python -m benchmark.release_audit --output benchmark/results/PUBLIC_RELEASE_AUDIT.json
python -m benchmark.chess.run --output benchmark/results/CHESS_PUBLIC_AUDIT.json
```

We welcome reproducible bug reports, security reports, third-party project trials, new language adapters, and **negative results**. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Project status and license

**Open-source MIT license** · **Python 3.11+** · **local-first** · **no mandatory cloud or embedding API** · **developer preview, not a security boundary**.

NERVE aims to become a trustworthy persistent-memory layer for agentic development—not to claim that it gives models consciousness, universal perception, or zero hallucinations.
