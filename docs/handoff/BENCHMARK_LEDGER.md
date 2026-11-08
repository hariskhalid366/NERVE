# NERVE benchmark ledger and confidence limits

**The figures below are not a universal accuracy score.** This table separates actual software regressions, deterministic retrieval and approximate payload measures. The current deliverable is a developer preview.

## Verification rerun with this handoff package

| Check | Result | Command | What it proves |
|---|---:|---|---|
| NERVE Python tests | **73/73 passed** | `python -m unittest discover -s tests -q` | Implemented behavior on this Python environment. |
| Chess rules tests | **16/16 passed** | `node --test examples/chess-mini/tests/rules.test.mjs` | Chess engine behavior under its test cases. |
| Task-mini Python tests | **5/5 passed** | `python -m unittest discover -s examples/task-mini/tests -q` | Example app tests. |

**Environment during handoff verification:** Python 3.13.5, Node v22.16.0, Linux container. An isolated Python venv installed the packaged wheel with `--no-index --no-deps`; `init`, `remember`, and `brief` completed successfully in a separate scratch project. macOS/Windows CI and rerunning full randomized benchmarks were **not** performed as part of this handoff build.

## Scripted retrieval and context-recovery tests

| Dataset | NERVE | Fair flat/lexical comparison | Interpretation |
|---|---:|---:|---|
| Original chess set, 48 queries | 38/48 = **79.17%** | 30/48 = 62.50% | Tuning-influenced set, descriptive only. Paired exact test p≈0.0768. |
| Harder chess references, 24 queries | 12/24 = **50%** | 12/24 = 50% | No demonstrated advantage on harder wording. |
| Python task-list set, 24 queries | 19/24 = **79.17%** | 11/24 = 45.83% | Very small hand-authored second code domain; no LLM tested. |
| Out-of-vocabulary synonym paraphrases, 8 queries | **0/8 = 0%** | Not a fair baseline trial | Major unresolved semantic retrieval weakness. |
| 20 randomized DB rounds × 48 targets | **960/960** in each exact key category | 960/960 in each category | Exact labels, IDs, aliases and distinctive historical tokens are easy for both methods. |
| 25 randomized DB rounds × 64 targets | **1600/1600** in each exact key category | 1600/1600 in each category | Same generator, new seed; not independent external validation. |
| Negative unrelated queries | 240/240 and 400/400 rejected | Fair flat comparison not reported | These are easy random negatives, not real false-positive calibration. |
| Context note/event recovered by explicit ID (chess) | 12/12 | Not applicable | Storage and direct retrieval, not LLM answer accuracy. |

**Critical caveat:** The report's statistical confidence intervals are optimistic because queries share generated targets. The chess original was used in earlier tuning. The newer task mini set is too small to establish generalization. Some diagnostics use different query definitions; do not pool percentages as if identical experiments.

## Scale, durability and cost proxies

- Previous v0.7 audit: 8 concurrent processes persisted 600 events and 600 notes (1,200 records) and SQLite integrity passed. This demonstrates one tested local concurrency workload, not cloud multi-agent synchronization.
- Historical retrieval: an old incident remained retrievable after **6,201** newer events under a targeted regression. Retrieving arbitrary old notes from a bounded brief is still not guaranteed; use `search_evidence`.
- Exact-label retrieval p95 at 3,000 indexed targets: about **45.5 ms** in the recorded v0.8 public audit on one local machine. This is hardware/workload specific.
- A previous context selection sent 2,607 JSON bytes versus 25,313 bytes for full history (about **89.7% fewer bytes**) in one fixture; another v0.8 fixture reported **93.17% fewer bytes**. JSON size is **not** provider input tokens, time or billed cost.
- MCP fresh-process handoff and explicit-ID fact recovery passed; this does **not** establish that another independent model successfully completed a code task using that information.

## Why 100% cannot be advertised

An algorithm can score 100% on exact identifiers while failing paraphrases (0/8) and real ambiguous user requests. Correctness in open-ended software development has no finite exhaustive test set. A meaningful launch claim requires pre-registered tasks, unseen repositories, a fair baseline, and repeated independent agent runs. Report distributions and failures, not just a headline score.

## Protocol for next real-agent evaluation

- **Arms:** fresh agent with no session memory; agent with ordinary searchable markdown notes; agent with NERVE using the *same underlying evidence*. Optional fourth arm: full conversation/history with explicit context-budget constraints.
- **Tasks:** at least 100 frozen, unseen questions/tasks across 3+ real projects. Include issue localization, contradictory notes, changed source, unknown features, uncertain targets, historical fixes and actual coding follow-through.
- **Agents:** same models, versions, prompts, time limits, budget and tool permissions per arm; randomize task ordering; avoid gold-answer leakage during memory ingestion.
- **Primary outcome:** successfully completed task / attempted task, verified with tests or reviewer rubric; secondary accuracy at Top-1/Top-3 and supported abstention.
- **Token outcome:** provider-reported total input/output tokens, including history ingestion, memory access tool exchanges, retries and correction attempts; divide by successful tasks and report costs if pricing reliably known.
- **Cross-agent:** Agent A works, commits/records context and exits; independent Agent B begins in a fresh context and must accomplish a follow-up task. Include failed, conflicting and stale-memory scenarios.
- **Stats:** paired comparisons on the same problems, confidence intervals with clustered bootstrap by project/task family, and error taxonomy; resist cherry-picking. Keep held-out tasks held out.

Raw evidence: `benchmark/results/PAIRED_METRICS.json`, `benchmark/results/PUBLIC-CHECK-RC2.json`, `benchmark/results/REPEATABILITY-20x48.json`, `benchmark/results/REPEATABILITY-25x64-seed9427063.json`, and `audit/results-v0.7.json`.
