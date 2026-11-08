# NERVE v0.7 candidate — capability and reliability audit

**Date:** 2026-11-08  
**Environment:** local Python 3.11+ / SQLite / Node 22.16, isolated temporary projects; no LLM API calls.  
**Versions:** unmodified v0.6 vs patched v0.7.0 candidate.  
**Evidence:** `audit/results-v0.6.json`, `audit/results-v0.7.json`, `audit/payload_bytes.json`, `audit/self_dogfood.json`; `tests/test_long_memory.py`.  
**Disclaimer:** The experiments below are fixture-based software tests, **not** independent real-agent performance evaluation. The dataset's original 48 chess questions influenced previous ranking weights.

## Summary

- **Local persistence:** Confirmed for a fresh process, for committed data before an abrupt exit, and under 8 concurrent writing processes.
- **Cross-process continuity:** 12/12 seeded chess target notes and incident histories recovered by stable ID, plus a successful separate MCP JSON-RPC subprocess handoff. This is not a two-LLM completion trial.
- **Target resolution:** 38/48 (79.2%) in-sample chess queries vs 30/48 (62.5%) flat overlap; on 24 harder queries both scored 12/24 (50%). Improvement was **not demonstrated on the harder set**.
- **Old event retention in retrieval:** Previously 0/1 after 325 newer unrelated events, now 1/1. Additional tests with 1000 unrelated events and 1000 memories pass. A new 6,201-event common-term-flood regression also passes.
- **Target-specific memory preservation:** Previously 0/1 after 25 global notes, now 1/1; regression also verifies 120 newer project notes.
- **Exact-alias stress:** 120/120 at each of four sizes (100, 500, 1500, 3000 targets), useful for testing scaling, **not** a semantic retrieval benchmark.
- **End-to-end real-agent task success and billed tokens:** not measured; no model/provider integrations were available in this runtime.

## Chess retrieval: paired comparison

| Test set | NERVE | Flat-overlap baseline | Paired difference | McNemar two-sided p |
| --- | ---: | ---: | ---: | ---: |
| Previously tuned, 48 questions | 38/48 (79.2%) | 30/48 (62.5%) | +16.7 percentage points | 0.076813 |
| Harder hand-written, 24 questions | 12/24 (50.0%) | 12/24 (50.0%) | 0 points | 1.000000 |

Paired-bootstrap descriptive 95% intervals (5000 re-samples): **+2.1 to +33.3 points** on the first set; **−25 to +25 points** on the second. These are *within-fixture* uncertainty calculations only. Because sample selection was not random and the first set was used for tuning, neither interval supports broad claims of real-world improvement. The exact paired McNemar test on the first set also does not cross the conventional 0.05 threshold. The deterministic benchmark includes 10/10 and 8/8 unsupported queries that did not receive an automatic supported-candidate decision; this does not demonstrate robust unknown detection in natural usage.

## Data-scale results

Each target has one synthetic event and one memory; query workload contains 120 exact alias lookups per size. Timings are one machine/run, without production concurrency or a confidence interval.

| Objects | Evidence rows | v0.6 p95 resolution | v0.7 p95 resolution | v0.7 SQLite bytes |
| ---: | ---: | ---: | ---: | ---: |
| 100 | 200 | 1.82 ms | 1.41 ms | 122,880 |
| 500 | 1,000 | 7.25 ms | 6.23 ms | 356,352 |
| 1,500 | 3,000 | 20.43 ms | 17.77 ms | 872,448 |
| 3,000 | 6,000 | 39.01 ms | 37.20 ms | 1,613,824 |

The SQLite FTS index increases disk storage at 3000 targets from **1,351,680** to **1,613,824 bytes**, about **19.4%** more. The p95 differences are not evidence of a general throughput speedup: they are unreplicated timings, and CPU/storage factors vary by environment. Query work still scales approximately linearly with the target count for the existing resolver.

## Context size versus real token efficiency

For 48 chess retrieval requests, serializing the **entire** seeded memory gives 25,313 bytes. Serializing NERVE's selected candidate plus context averages **2,606.9 bytes** (89.7% smaller); median is 2,766 bytes. In 10/48 queries the top target is wrong, and the all-history comparator is intentionally naive. **This is a payload-byte reduction proxy, not the number of LLM tokens billed or a valid per-successful-task cost comparison.** We have not established whether selective retrieval improves real task accuracy or reduces *total* agent tokens once additional tool calls are included.

## Concurrency, crashes, permissions and data handling

- 8 independent processes attempted 75 events and 75 memories each: **600/600** events and **600/600** memories persisted; no worker exceptions, SQLite `integrity_check=ok`.
- A committed note persisted after the process called `os._exit(0)` and was recovered after reopening; no assertion is made for uncommitted data or disk failure.
- SQLite file-backed revision anchors moved through `source_unchanged` → `source_changed` → `source_missing` when a file was edited and removed; missing file matches require confirmation.
- Tested simple `.env` exclusion and example key/inline-value redaction. This is **not** a comprehensive privacy, secret or injection audit; memory text can still carry sensitive information.
- Two temporary project directories had independent SQLite stores. No cross-user/tenant permission system is provided.
- Unseeded self-source diagnostic produced **6/18** correct target matches for descriptive queries (flat bag-of-words baseline **0/18**); this tiny task set is not independent and demonstrates that automatic symbol indexing does not produce natural-language understanding.

## What was fixed

1. `Nerve.context`: target-specific memories are selected first, and project-wide notes fill only remaining slots (no overwrite by recency of unrelated global facts).
2. `Nerve.resolve`: indexed event and memory text can be searched across long history through SQLite FTS5; fallback scans full history if FTS5 unavailable. No assumption that the memory record is true. FTS5 index is built from existing records on upgrade and stays in sync for write/delete.
3. Historical matching now searches individual terms to prevent generic terms flooding out rare old incidents; verified with an artificial 6,201-event project. The 500-match-per-term cap still limits generic-term recall.
4. Eleven regression tests cover long-event history, long-memory history, crowding, reopened databases, migration, syntax safety, and evidence deletion.

## Limitations and release blockers

1. **Semantic paraphrase accuracy is low** on untuned references; no independent statistically powered benchmark or held-out model trials. Do not use target matches to justify automatic edits without confirmation.
2. **No actual task-level token costs**, latency budgets across host tools or model task success rates. Need provider usage telemetry from actual test agents.
3. **MCP host interoperability is incomplete.** Built-in JSON-RPC stdio has been tested in subprocesses, not against a live supported IDE host. The SDK alternative requires an external dependency.
4. **Security scope is local and opt-in only**: best-effort redaction, plaintext SQLite, no cryptographic project synchronization or multi-user access controls. Never expose arbitrary agent inputs as privileged operations.
5. **Scaling bottlenecks**: resolve still reads all targets; FTS5 search results are capped at 500 hits per individual term per history source; highly ambiguous repeated terms may not cover very old matching evidence. This is not an infinite-recall guarantee.

## Next three priorities

1. Run **two real model agents** on 50–100 new coding tasks with no-memory, README-only and NERVE conditions. Measure task success, actual billed input/output tokens, time, and retry count.
2. Add optional offline semantic retrieval and a reranker; evaluate with a sequestered set of paraphrases and negatives from multiple unrelated codebases before tuning.
3. Validate the built-in MCP client integration against real IDEs and add privacy hardening (opt-in sources, encrypted local store option, data retention, and security tests).

## Reproduction

```bash
python -m unittest discover -s tests -q
node --test examples/chess-mini/tests/*.test.mjs
PYTHONPATH=. python audit/run_extended.py
PYTHONPATH=. python audit/payload_bytes.py
PYTHONPATH=. python audit/self_dogfood.py
```

The extended script writes its own results to `audit/results.json`; use the archived version-specific reports for the comparisons above. You can separately evaluate the earlier v0.6 archive under the same harness. The commands do not call hosted models. See `docs/AGENT_INTEGRATION.md` for connecting to your own project.
