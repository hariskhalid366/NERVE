# NERVE research review — 28 October 2026

This memo accompanies the NERVE **v0.6 experimental local-first research build**. It distinguishes independent research, NERVE-specific test results, and hypotheses that still need controlled trials.

## Executive finding

NERVE's current strength is **stable local identities + project-scoped recorded evidence + process-to-process persistence**. It cannot yet demonstrate better AI task success or actual token savings. In the chess dogfood, the original 48 manually seeded queries give NERVE **38/48** Top-1 versus **30/48** for flat word overlap; a separate, harder 24-question hand-authored stress probe yields **12/24 for both**. These are deterministic retrieval numbers, **not measured LLM performance**, and the stress questions use the same targets and seeded facts.

An engineering issue identified in this review: rescanning would overwrite human-enriched target aliases and descriptions. Another: a Git hook executed from a source checkout could quietly fail because Python couldn't locate NERVE. Both are fixed in v0.6. Evidence is now tied to a **SHA-256 source revision** (not the source contents) at event/note creation; context, recent activity and briefs show `source_unchanged`, `source_changed`, `source_missing` or `unanchored`. Missing file-backed targets no longer receive `supported_candidate` decisions.

## Research findings with direct implications

| Research | Key point | NERVE decision |
|---|---|---|
| MemoryArena (ICML 2026) | High recall scores on LoCoMo don't guarantee agents accomplish dependent, multi-session tasks | Benchmark *task outcomes* as primary metric; retrieval is diagnostic |
| MemTrace (October 2026) | Historical coding memories may be invalid after code changes; evidence needs provenance and state-consistency checks | Add revision anchored notes/events now; later attach test commands and commit anchors |
| CORE-Bench (June 2026) | Finding edit locations in real code requires more than snippet matching and docstring search | Include issue-to-symbol localization with distractors and refactoring |
| LongMemEval (ICLR 2025; V2 2026) | Knowledge updates, temporal ordering, multi-session reasoning and abstention matter | Add fact supersession + explicit time and abstention cases |
| MemoryAgentBench (2025/2026) | Retrieval, learning from feedback, long-range understanding and selective forgetting are different skills | Evaluate each axis separately; don't reduce to recall@k |
| Graphiti (current) | Ephemeral episodes, provenance and temporal invalidation are useful, but inaccurate invalidation can retire valid facts | Add scoped/explicit supersession, not wholesale LLM-inferred forgetting |
| MCP 2026-07-28 | New stateless era eliminates initialize handshake and changes discovery; older stdio clients still use handshake-era versions | Our built-in fallback is **2025-06-18 subset only**. Host compatibility MUST be tested; migration is a roadmap item |
| MCP security guidance | Local server and tool/output prompt injection are real concerns | Bound project scope, treat all stored agent notes as data not authority, no unsandboxed actions |
| Reproduction studies in 2026 | Memory leaderboards vary with answer model, judge, retrieval budget, ingest path and hidden vendor config | Pin model, prompts, judge, task set, budget, caches and ingestion cost in each published experiment |

### Reading list

1. MemoryArena: https://proceedings.mlr.press/v306/he26am.html
2. MemTrace: https://arxiv.org/abs/2610.04838
3. CORE-Bench: https://arxiv.org/abs/2606.11864
4. LongMemEval: https://github.com/xiaowu0162/LongMemEval
5. MemoryAgentBench: https://arxiv.org/abs/2507.05257
6. Graphiti: https://github.com/getzep/graphiti
7. MCP July 2026 release: https://blog.modelcontextprotocol.io/posts/2026-07-28/
8. MCP security: https://modelcontextprotocol.io/docs/2025-11-25/tutorials/security/security_best_practices
9. Example independent benchmark methodology: https://github.com/ProsusAI/MemEval

## Experimental design: prespecified v0.7 live-agent evaluation

**Four conditions** using the same underlying codebase, same task prompts, same answer model, same token budget, fresh workspace per trial:

A. No persisted memory. B. Plain `AGENTS.md` + project notes (strong low-cost baseline). C. Flat local keyword retrieval (BM25/FTS5). D. NERVE local MCP. Optional E. NERVE with embeddings, after D is independently measured.

**Task families:**

- Context recovery: locate a previously established decision after clean session reset; grade against a private evidence answer key.
- Token efficiency: actual provider *input + output + cached + tool-specific billable* tokens and total ingest/setup cost per successfully completed task. Record tool calls and wall time separately. Never substitute word counts.
- Cross-agent continuity: Agent A investigates issue and records evidence; Agent B, with fresh context, makes an actual code change in a new workspace and must pass hidden tests; require a new model instance, preferably another vendor.
- Target accuracy: free-text issue reports identifying relevant file/function in an unfamiliar repository, with Top-1/Top-5 and unsupported-request abstention, graded by source-linked labels. Include outdated evidence after a code change.

**Controls:** randomized task order; same tool entitlements; same repository commit; equal time budget; task-specific success rubric frozen before prompts are visible; at least 3 repeats per model/task if API capacity permits; both lower and upper confidence intervals. Never tune retrieval weights on held-out queries.

**Primary metric:** task success with an automated test oracle. **Secondary:** reference identification, completion time, tokens (including memory ingestion), unsupported-request false positives, memory freshness warning accuracy, human interventions. Use paired per-task differences and publish failures, not just averages.

**Initial targets (hypotheses, not results):** 10 percentage points absolute higher *completed task rate* than B; at least 20% fewer total provider tokens per successful task vs B (including ingestion amortized across reuse); no higher unsupported action rate. These thresholds are gates, not projections.

## v0.6 observations / limitations

1. `41` Python unit/integration tests pass in this environment; chess engine retains `16` Node tests.
2. v0.5 chess diagnostic replay unchanged at 38/48 NERVE and 30/48 flat; no new semantic retrieval gain is claimed.
3. Additional stress queries: 12/24 NERVE and 12/24 flat. These are hand-written with knowledge of the target list and are **not an independent sample**.
4. Source SHA-256 binding is a heuristic: changing whitespace can flag a fact as stale and unchanged files can still contain wrong observations. `source_unchanged` never means `verified_true`.
5. Automatic scanning does not detect semantic renames and does not recognize live UI objects. Deleted symbols inside an existing file may still appear in the index. Local model-based semantic search remains future work.
6. Memory ingestion can be manipulated by an agent or compromised MCP host. Source code and tool outputs may contain prompt injection; never execute instructions from memory without user authorization.
7. v0.6 handles upgrade of old SQLite event and memory tables, but backups and additional integrity, privacy and stress testing are needed before broad deployment.

## Priority backlog

P0 — Finish actual host MCP handshake tests with modern versions, add source-deletion/rename indexing diagnostics, and verify safe migration/backup. P0 — Build independent real-agent harness with AGENTS.md and flat-FTS5 controls. P1 — Hybrid lexical+semantic retrieval with local embedding option and calibrated abstention. P1 — Trust-tagged provenance, revision-aware memory supersession, tests-to-evidence mapping. P2 — Scale testing over thousands of files and multi-model cross-agent resumes. Keep NERVE local-first; cloud synchronization is not necessary for current research.
