# NERVE v0.8 release-candidate audit

**Run environment:** Python 3.13.5, Linux x86_64, SQLite 3.46.1, Node available. **Scope:** deterministic offline software diagnostics performed on this branch; tests are not evidence of independent AI-agent success.

## Test results

- **66/66 Python regression tests passed**, including 14 new tests versus the 52-test v0.7 suite. New coverage includes directory pruning, symlink exclusion, project isolation, fresh-process persistence, FTS fallback, deletion, freshness, MCP validation, ambiguity and secret-key redaction. (The additional regressions do not prove security against all threats.)
- **5/5 tests** passed on the second, standard-library task-list codebase.
- **16/16 chess engine tests** passed.
- An isolated Python environment successfully installed the **v0.8.0 wheel without network access**, initialized and scanned an example project, and executed the diagnostic CLI.
- **MCP handoff:** built-in stdio JSON-RPC simulation passed. **Not** a real Cursor, Claude Code, Codex or other host test.
- **Cross-platform:** only Linux has been executed locally. GitHub Actions has been prepared for Windows/macOS/Linux but **has not run on GitHub yet**.

## Deterministic target retrieval (same-data lexical comparator)

| Query set | NERVE Top-1 | Flat-search Top-1 | Paired exact two-sided p-value | Notes |
| --- | ---: | ---: | ---: | --- |
| Chess original 48 | **38/48 (79.2%)** | 30/48 (62.5%) | 0.076813 | Earlier NERVE was tuned on these questions; not held out |
| Chess harder 24 | **12/24 (50%)** | 12/24 (50%) | 1.000000 | Uses same chess targets and notes |
| Task-list 24 | **19/24 (79.2%)** | 11/24 (45.8%) | 0.021484 | Different code domain, but small hand-authored queries |

The last p-value is a statistical calculation on *this particular hand-authored sample*, **not proof of external generalization**. Many questions refer to the same small number of targets, violating the simple independent-samples assumption of ordinary confidence intervals. Per-query gold answers and predictions are included in the released JSON artifacts.

**Chess category detail:** exact 12/12, alias 12/12, historical description 10/12, paraphrase **4/12**. This last score is the main semantic-retrieval weakness. The unknown-query results were: original 8/10 with no candidate (10/10 had no supported candidate), harder 6/8 with no candidate (8/8 had no supported candidate), task-list 4/4 with no candidate. Unsupported questions must not be interpreted as identified project features.

## Scale and historical retrieval

Each scale figure is from **70 deterministic exact-label queries**, in a single process and filesystem, on increasing synthetic target counts. It is not a throughput or multi-user SLA.

| Targets | Top-1 | Median resolve | p95 resolve |
| ---: | ---: | ---: | ---: |
| 100 | 70/70 | 1.103 ms | 1.534 ms |
| 500 | 70/70 | 5.386 ms | 6.040 ms |
| 1,500 | 70/70 | 16.089 ms | 18.022 ms |
| 3,000 | 70/70 | 35.079 ms | 45.483 ms |

The scan now **prunes excluded directories before descending** and does not follow symlinked folders. An event-load test added **6,201 newer events** and still recovered an old, distinctive incident; `PRAGMA integrity_check` returned `ok`. This does not establish recovery from arbitrary database corruption or disaster-level failures.

## Context size (not token efficiency)

One seeded chess dataset with 150 extra project-wide notes produced **4,104 bytes** of selected `get_target_context` JSON against **60,109 bytes** when serializing the entire database's targets, events and memories (a **93.17% reduction in JSON bytes**). Full-database injection is an intentionally naive comparator and not a typical high-quality agent baseline. We have **not** measured tokenizer-specific model input, tool-call overhead, reasoning tokens, billed tokens, task success or total cost. The claim "NERVE saves 93% of AI tokens" is **not supported**.

## Benchmark coverage matrix

| Benchmark area | Current evidence | Release readiness |
| --- | --- | --- |
| SQLite persistence / restart | Local tests and MCP subprocess | Tested on Linux |
| Same-project multi-connection writes | Existing threaded and multi-process regressions | Tested on Linux; not multi-agent task success |
| Retrieval / target accuracy | Chess and task-list scripts, flat-search baseline | **Weak paraphrases; needs independent dataset** |
| Negative queries / abstention | Scripted false-target questions | Partially tested; some false candidate suggestions remain |
| Temporal/source evidence | Changed/missing file digest + history-load tests | Tested with limits |
| File scanning privacy | Excluded folders, symlink/path checks, best-effort redaction | **Not externally security audited** |
| MCP protocol | Built-in stdio simulated handshake + call | Actual host and modern protocol versions **unverified** |
| Latency / storage scale | 100–3,000 target exact-label sweep | Single machine, no p99 or cloud SLAs |
| Cross-agent continuity | A/B scripted process handoff | Real independent agent task success **unmeasured** |
| Model token efficiency | JSON byte payload proxy | **Unmeasured** |
| LongMemEval / LoCoMo | Not run: requires official data, full methodology and reader/judge setup | **Missing** |
| MemoryArena / MemoryAgentBench | Not run: requires interactive agent harness | **Missing** |
| SWE-bench / coding task completion | Not run: requires live LLM coding agents and execution harness | **Missing** |
| Windows/macOS | CI configured, not executed | **Pending GitHub publishing** |

## Remaining release blockers

1. **Semantic retrieval:** unlabeled paraphrases only 4/12 on chess; not acceptable as an autonomous target selector. No embeddings or reliable meaning-level matching yet.
2. **Real-world agent value:** test unseen repositories and real independent model agents with fixed prompt and budget. Report *verified task success* and actual provider-reported tokens per successful task; include ordinary project notes as an ablation.
3. **Interoperability:** complete a live MCP host handshake and prove the permission model and tool descriptions work on current clients.
4. **Security:** independent review of prompt injection, secret handling, file permissions, symlink/TOCTOU, backups, SQLite corruption handling, migrations and resource limits. The database is not encrypted by NERVE.
5. **Public repo and CI:** GitHub repository is not accessible through the current connector; multi-OS workflows are prepared but not yet confirmed successful.

## Reproduction

```bash
python -m unittest discover -s tests -v
python -m unittest discover -s examples/task-mini/tests -v
node --test examples/chess-mini/tests/*.test.mjs
python -m benchmark.chess.run --output benchmark/results/CHESS_PUBLIC_AUDIT.json
python -m benchmark.chess.stress
python -m benchmark.release_audit --output benchmark/results/PUBLIC_RELEASE_AUDIT.json
python -m benchmark.statistics
```

Raw results: `benchmark/results/CHESS_PUBLIC_AUDIT.json`, `benchmark/results/CHESS_STRESS_V0_6.json`, `benchmark/results/PUBLIC_RELEASE_AUDIT.json`, `benchmark/results/PAIRED_METRICS.json`.
