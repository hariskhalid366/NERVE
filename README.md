# NERVE — Local-first project memory for AI coding agents

**For Codex / project handoff:** begin with [START_HERE_CODEX.md](START_HERE_CODEX.md) and [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md); historical research and benchmark lineage are indexed under [research_archive](research_archive/ARCHIVE_MANIFEST.json).

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

## How it works

NERVE is a small local service around one SQLite database per project. It is deliberately not a general-purpose cloud memory product.

1. **Initialize** creates a private `.nerve/memory.sqlite3` database in the project you explicitly select.
2. **Scan** records safe static source metadata such as supported filenames and symbols. It avoids common private or generated locations including `.git`, `.env*`, `.nerve`, virtual environments, `node_modules`, build output and symlinked folders.
3. **Observe, record, and remember** store concise, user- or tool-supplied facts, incidents, decisions, and source-linked evidence. Known sensitive field names are redacted on a best-effort basis.
4. **Brief, resolve, context, and evidence search** return bounded, inspectable candidates. A candidate is not permission to act: verify the source and ask when a result is ambiguous.
5. **MCP** exposes the same local operations over stdio so an authorized coding-agent host can opt in. It does not inject context into a model automatically.

The data stays on the machine that holds the selected project unless a user deliberately configures a separate optional integration. This release does not configure or deploy any hosted service.

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

### What NERVE stores—and what it does not

| Stored locally in `.nerve/` | Not collected automatically |
| --- | --- |
| Target labels, source references and optional aliases | Private conversations, browser history, model weights or prompts |
| User/tool-supplied observations, events and short memories | Source file contents as a semantic embedding corpus |
| Source digests used to flag stale evidence | Credentials, `.env` files, generated databases and ignored directories |
| Metadata-only Git observations when the user installs the opt-in hook | Commit messages, diffs or arbitrary repository history |

## Quick start — less than five minutes

**Requirements:** Python **3.11+**, a folder containing your project, and an MCP-compatible host if you want an agent to call tools. Local CLI works without MCP host.

**Option A — offline installer included in the release ZIP:**

```bash
# Use the actual path of the extracted wheel, with no network access:
python -m pip install --no-index --no-deps dist/nerve_agent_memory-0.8.0rc2-py3-none-any.whl
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

MCP tools currently available: `get_project_brief`, `scan_project`, `resolve_target`, `get_target_context`, `search_evidence`, `get_recent_activity`, `observe_target`, `record_event`, `remember_context`.

### A practical day-to-day workflow

```bash
# Once for each existing project
nerve --project /absolute/path/to/my-project init
nerve --project /absolute/path/to/my-project scan

# At the start of an agent or human work session
nerve --project /absolute/path/to/my-project brief

# After a confirmed decision or fix
nerve --project /absolute/path/to/my-project remember \
  "Use event delivery rather than polling for the import status." \
  --target feature:import-status

# When a request is vague, retrieve candidates before editing
nerve --project /absolute/path/to/my-project resolve "the import status update"
```

Use `nerve --help` and `nerve --project /path doctor` to inspect the commands and local configuration available in your installed version.

## Benchmarks: measured, not advertised

NERVE ships an offline test harness, a playable chess project and a second tiny task-list project. Results are from **scripted retrieval tests**, not full AI coding-agent evaluations.

| Test | NERVE | Same-data flat-search baseline | Interpretation |
| --- | ---: | ---: | --- |
| Chess: original 48 questions | 38/48 (79.2%) | 30/48 (62.5%) | Tuned set; advantage not generalizable |
| Chess: harder 24 questions | 12/24 (50%) | 12/24 (50%) | No advantage |
| Task-list project: 24 questions | 19/24 (79.2%) | 11/24 (45.8%) | New hand-authored mini-project; very small sample |

### Open the benchmark evidence

The benchmark files are committed to this repository. Use these direct links rather than hunting through the file tree:

- [Benchmark harness and scripts](benchmark/)
- [Input scenarios](benchmark/scenarios.json)
- [Chess public audit: 48 known queries and 10 negative queries](benchmark/results/CHESS_PUBLIC_AUDIT.json)
- [Chess stress result: harder 24-query set](benchmark/results/CHESS_STRESS_V0_6.json)
- [Task-list/chess paired metrics](benchmark/results/PAIRED_METRICS.json)
- [20 × 48 seeded repeatability result](benchmark/results/REPEATABILITY-20x48.json)
- [Public release audit](benchmark/results/PUBLIC_RELEASE_AUDIT.json)
- [Benchmark methodology and caveats](BENCHMARK.md)

To reproduce the visible benchmark outputs from a source checkout:

```bash
python -m benchmark.chess.run --output benchmark/results/CHESS_PUBLIC_AUDIT.json
python -m benchmark.chess.stress
python -m benchmark.statistics
python -m benchmark.release_audit --output benchmark/results/PUBLIC_RELEASE_AUDIT.json
python -m benchmark.repeatability --rounds 20 --targets 48 --strict \
  --output benchmark/results/REPEATABILITY.json
```

The code also tests FTS-backed historical retrieval, malformed protocol messages, file/symlink safety, project isolation and SQLite persistence. See [Release audit](docs/PUBLIC_RELEASE_AUDIT.md) for latencies, stress details, limitations and exact reproduction commands. **JSON payload reduction is not a provider-token or cost reduction.** We have not run official LongMemEval, LoCoMo, MemoryArena or SWE-bench model evaluations.

**How to read these numbers:** the 20 × 48 repeatability result demonstrates deterministic retrieval of seeded identifiers, aliases, historical notes, unsupported queries and persistence under this test fixture. It does not establish meaning-level retrieval, independent model productivity, model-token savings, or general performance on arbitrary projects. The harder chess set is intentionally important: it shows no advantage over the flat-search comparison.

## Does NERVE fix LLM hallucinations or context-window limits?

**No.** NERVE cannot change the model's context window, guarantee factual answers, or make unobserved code and runtime state visible. It can make *stored project facts and source-linked evidence retrievable* across sessions. That may reduce **context-related mistakes** if the agent uses the evidence correctly. This distinction matters when people search for "AI context hallucination fix", "Claude forgets project" or "Cursor loses context".

## Is it useful for multi-agent development?

Multiple authorized local agents can use the **same `.nerve/memory.sqlite3`** in one project. SQLite concurrency and process-restart persistence have been tested; independent agents solving unseen tasks and genuine cross-model productivity gains have **not** been measured. Keep every project's `.nerve/` private; it is not intended to be copied into public Git repositories.

## Is NERVE privacy-friendly and fully offline?

The local runtime needs no internet to store/retrieve memories. `.nerve/` is excluded in `.gitignore`. **The database is not encrypted by NERVE**; use operating-system access controls and full-disk encryption. Automatic secret filtering is best effort—not a data-loss-prevention guarantee. Don't submit credentials, personal data or proprietary secrets to observers. [Security and responsible disclosure](SECURITY.md).

## Testing and continuous integration

The repository's GitHub Actions workflow runs the Python regression suite on Python 3.11, 3.12 and 3.13 for Ubuntu, plus Python 3.12 on macOS and Windows. It also runs the 16 chess-engine checks with Node.js. The latest published run is [green across all jobs](https://github.com/hariskhalid366/NERVE/actions/runs/42473667071).

The nightly repeatability workflow is scheduled separately and can also be started manually from the Actions page. It is deterministic and makes no model API calls.

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

### Known limits and next validation steps

- Retrieval is lexical and heuristic; indirect paraphrases are a known weak point.
- The benchmark fixtures are small and hand-authored. They are not a substitute for independent, held-out real-project studies.
- NERVE does not prove that an agent completed work correctly; humans and ordinary tests must still verify changes.
- MCP host compatibility has scripted coverage, but live validation in each target host remains necessary.
- The local database is not encrypted and the sanitization layer is not a complete secret or PII filter.
- This release has not completed an external security audit or official LongMemEval, LoCoMo, MemoryArena, or SWE-bench evaluation.

See the [release checklist](docs/RELEASE_CHECKLIST.md) and [roadmap](docs/ROADMAP.md) for the detailed follow-up plan.

## Repeated offline benchmarks (release candidate)

NERVE includes a seeded randomized stress harness for exact/alias/historical
retrieval, unsupported queries, ambiguous identities and fresh-process handoff:

```bash
python -m benchmark.repeatability --rounds 20 --targets 48 --strict \
  --output benchmark/results/REPEATABILITY.json
```

A separate GitHub Actions workflow schedules a small nightly run **only after
the repository has been published and Actions is enabled**. There is no model
API cost for the deterministic suite. It is intentionally different from
real cross-agent model benchmarks; see `docs/REPEATABILITY_TESTING.md`.

Historical evidence lookup can recover notes older than the normal context cap:

```bash
nerve --project /path/to/project search-evidence "distinctive incident keywords" --target your-target-id
```

The MCP interface exposes the same function as `search_evidence`. Lexical
search does not understand arbitrary synonyms or guarantee factual truth.
