# NERVE v0.8.0-rc1 — local-first release candidate

## Shipped in this candidate

- Scanner now prunes excluded directories before traversal; no symlinked directory traversal.
- Additional public-release regressions: source path safety, project isolation, deletion, memory persistence, source freshness, FTS fallback and MCP validation.
- Second independent **code domain** for scripted smoke testing: tiny Python task-list module (not independent LLM evaluation).
- Reproducible performance, payload and paired-retrieval diagnostics with raw JSON results and caveats.
- Developer-friendly README with natural search terms, GitHub metadata guidance, platform CI matrix, local offline installation, security policy and contributor templates.

## Verified locally

66 Python tests; 5 task-list tests; 16 chess tests; offline wheel installation; 6,201 newer-event history-pressure recovery; 3,000-target exact-label latency sweep. **All are offline scripted tests**.

## Not done

No public GitHub repository, no confirmed search ranking, no cross-OS CI result, no full live agent task benchmark, no official LongMemEval/LoCoMo/MemoryArena results, no actual LLM token/cost numbers, and no third-party security audit. **Not production ready.**
