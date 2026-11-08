## v0.7.0 (evaluated candidate, November 8, 2026)

- Fixed disappearance of target-scoped memories from a context result when project-wide notes accumulated.
- Fixed historical incident retrieval being limited to the newest 300 global events or memories; uses optional local SQLite FTS5 evidence indexing with a scan fallback. Distinctive search terms are now queried individually so common-word floods do not hide rare old events.
- Preserved older v0.6 memories through on-open FTS index migration without rewriting their source records.
- Added eleven targeted regression tests, reproducible chess/scaling/concurrency audits, and evidence-based limitations.
- No claim of increased LLM intelligence, end-to-end model token savings or universal host compatibility.

# v0.6.0 — Evidence freshness and research (28 October 2026)

- Add source SHA-256 revision anchors to new memory and event rows; migrate old SQLite schemas.
- Label freshness on target context, project briefs and recent events.
- Preserve human enriched descriptions and aliases across source scans.
- Downgrade missing source candidates to `needs_confirmation`.
- Fix source-checkout Git post-commit hook module path issue.
- Add chess stress probes and contemporaneous research/evaluation protocol.
- Keep retrieval weights unchanged: no new semantic accuracy gains claimed.

# Changelog

## 0.5.0 — chess dogfood developer preview (2026-10-22)

- Added playable dependency-free Little Chess demo and 16 Node game-engine regression tests.
- Fixed JS/TS ESM indexing: `.mjs`, `.cjs`, `.mts`, and `.cts` now recognized (verified 6 files, 46 symbols in the chess fixture).
- Refined evidence ranking for descriptive historical queries and common incidental tokens; still lexical-only and uncalibrated.
- Added repeatable chess dogfood retrieval, persistence, subprocess MCP, payload and negative-query checks.
- Recorded clear evidence that paraphrased references still need improvement and that model-level quality gains are not measured.
- Added a portable offline Python wheel and local-project installation guide.

# Changelog

## 0.4.0 — Developer preview (2026-10-20)

**Local-first:** Added project brief tool and CLI, safe Cursor config generator with merge and collision checks, opt-in metadata-only Git post-commit observer, `doctor`, and built-in dependency-free MCP stdio tools compatibility path for air-gapped development.

**Evaluation:** Preserved v0.3 100-query synthetic diagnostic and added resolver's explicit candidate-verification advisory. Added workflow tests, built-in MCP JSON-RPC protocol simulations, cross-process memory handoff and simultaneous writer tests. **No real-model improvement has been measured.**

**Documentation:** Reorganized categorized README, offline setup, security/threat-model notes, real-project evaluation protocol, maintainer publishing instructions, release checklist, and contribution guide.

**Not shipped:** public GitHub repository, hosted NERVE Cloud instance, real agent-model benchmark, model-verified semantic retrieval, public multi-tenant authentication and live cross-editor integration.

## 0.3.0 — Benchmark diagnostic prototype

Synthetic lexical query fixtures, local deterministic diagnostics and blind-trial log scoring harness. 80 known-object query results: NERVE Top-1 81.25%, flat lexical Top-1 81.25%, paraphrase accuracy 25%.

## 0.2.0 — Cloud contract prototype

Single-project FastAPI REST gateway with agent/observer token separation, Docker/Railway recipe, and optional cloud-side local stdio MCP bridge. Local HTTP contract tests only.

## 0.1.0 — Local proof of concept

Project SQLite object identities, events, notes, static metadata index and opt-in local observer collector.

## 0.8.0-rc1 — release candidate (2026-11-08)

- Pruned excluded directories before source index traversal instead of enumerating excluded trees.
- Added extra safety and portability regression cases; 66 Python unit/integration tests passing on Linux.
- Added a second tiny task-list project and reproducible paired comparative statistics.
- Added raw, denominated evidence and a benchmark coverage matrix; documented missing real-agent and provider-token trials explicitly.
- Added public README, GitHub topics/metadata checklist, security policy and cross-platform CI configuration (not yet executed in GitHub).
