# Open issues, risks, next experiments and release gates

## Highest-priority engineering blockers

| Priority | Issue | Current evidence | Acceptance criteria |
|---|---|---|---|
| **P0** | Weak semantic retrieval for paraphrases and indirect references. | 0/8 unseen-synonym cases; harder chess 12/24 equal to flat search. | Better held-out Top-1 and abstention than strong flat lexical baseline, without increasing incorrect confident selections. |
| **P0** | No direct proof of better real-agent task success or actual token savings. | Most metrics are scripted deterministic retrieval and JSON payload byte proxies. | Real model A/B trials, matched tasks, provider token reports including extra memory calls, independent agent A→B task outcomes. |
| **P0** | GitHub publication not verified. | Public repository `hariskhalid366/NERVE` exists, Chat-mode GitHub write APIs failed with 403. | Git/Codex push authorized, remote commit verified, CI results inspected, release tag artifacts published. |
| **P1** | MCP host version compatibility uncertain. | Built-in stdio fallback tested with simulated handshake and tool calls. | Verify on actively supported Codex/Claude Code/Cursor versions and document any differences. |
| **P1** | Security/access controls and cross-platform CI. | Basic secret skipping, redaction, path sanitization, project isolation and local tests. | macOS/Windows/Linux CI, manual external inspection, process concurrency/stale-source/load tests. |
| **P2** | Retrieval noise and recency vs historical coverage. | v0.7 and v0.8 fixed known eviction paths with `search_evidence`, but bounded context remains selective. | Larger, contradictory, noisy, real repository stress tests with recall@K and error tracing. |
| **P2** | Onboarding across different agents. | Cursor config helper; manual MCP configuration for other hosts. | Validated integration instructions and small recorded demos for at least two hosts. |

## Three highest priority next steps

1. **Publish a safe preview release** from this source snapshot to the existing GitHub repository with an authenticated Git environment; verify actual remote contents, license, README, CI, package and tag. Do not claim publication before remote verification.
2. **Build and freeze an independent, held-out real-project agent benchmark** (3+ real repos, 100+ questions/tasks, fair no-memory and flat-notes controls). Capture task success and true total tokens, not only retrieval output size.
3. **Improve NERVE's semantic candidate retrieval** using optional offline lexical+embedding or graph/rule hybrid, confidence thresholds and source evidence ranking, then run unchanged frozen benchmark. Preserve dependency-free fallback and ensure no regressions on precise aliases, historical incidents, stale files or unknown queries.

## Release classifications

- `v0.8.0-rc2`: **developer preview**, not stable v1.0.
- Tested: local Python/Node regressions, sample retrieval, concurrent SQLite in specific workloads, source freshness, simulated MCP, memory persistence and offline-wheel installation in earlier session.
- Not established: universal understanding, end-to-end model accuracy, no hallucinations, cost reductions, remote GitHub deployment or multiuser cloud features.

## Local-first policy

No cloud environment is required. Keep `.nerve/memory.sqlite3` and project notes local to the developer, never auto-sync. Do not install browser/device observers without explicit authorization. Cross-agent visibility requires same authorized project store, not “NERVE memory for everybody.”
