# NERVE research and implementation timeline

This is a **curated lineage of available local artifacts**, not a claim that all designs, tests or research references were independently reviewed today. Original version-specific documents are preserved under `research_archive/`; current code is at the ZIP root.

| Version and period | Main milestone | Evidence / notes | Known limitation |
|---|---|---|---|
| **v0.1**, Oct 2026 | Initial NERVE local project identity + events + notes with SQLite and early agent interface. | `research_archive/v0.1/README.md` and `ARCHITECTURE.md` | Prototype; no strong benchmark. |
| **v0.2**, Oct 2026 | Cloud API experiment, authentication and authorized observation receiver; Railway packaging. | `research_archive/v0.2/` | Cloud not deployed or required for current local-first roadmap. |
| **v0.3**, Oct 2026 | Deterministic 100-question retrieval diagnostic and controls; four metrics formalized. | `research_archive/v0.3/BENCHMARK.md`, `benchmark/results/BASELINE_REPORT.md` | Simple search parity; hand-authored fixtures. |
| **v0.4**, Oct 20 | Developer preview: project brief, safe Git metadata observer, Cursor config generator, offline stdio MCP fallback. | `research_archive/v0.4/`, `CHANGELOG.md` | Initial integration not validated broadly on real hosts. |
| **v0.5**, Oct 22 | Playable JS chess project as dogfood; `.mjs` indexing fix; retrieval ranking changes; wheel packaging. | `research_archive/v0.5/benchmark/results/CHESS_REPORT.md`, `examples/chess-mini/` | Original retrieval set influenced tuning; paraphrases weak. |
| **v0.6**, Oct 28 | Revision-aware evidence freshness; preserve enriched metadata across rescans; detect changed/missing sources; Git hook import fix. | `research_archive/v0.6/RESEARCH_OCT_2026.md`, `benchmark/results/CHESS_STRESS_V0_6.json` | Hard chess probes tie lexical baseline at 12/24. |
| **v0.7**, Nov 8 | Fixed historical evidence evictions, note crowding; SQLite FTS5 optional index and fallback, scale/concurrency audits. | `research_archive/v0.7/EVALUATION-SUMMARY.md`, `audit/results-v0.7.json` | Scalability measured locally, no real model gains proven. |
| **v0.8.0-rc1**, Nov 8 | Public release candidate: source-scan pruning, second mini project, GitHub docs/security/CI and keyword-friendly README. | `research_archive/v0.8.0-rc1/`, `benchmark/results/PUBLIC_RELEASE_AUDIT.json` | No public CI verification or independent real-agent trials. |
| **v0.8.0-rc2**, Nov 8 | Repeatability suite with randomized DBs and fair exact-match baseline; `search_evidence` historical memory API; opt-in scheduled CI. | `REPEATABILITY_REPORT.md`, `benchmark/repeatability.py`, `benchmark/results/REPEATABILITY-*.json` | Exact matches 100% in generated queries, baseline also 100%; unseen synonym probe 0/8. |

## Research questions investigated

1. Can an authorized agent resume a project from structured external memory rather than manually repasting screenshots/context? A fresh-process MCP exchange demonstrates **data persistence and retrieval**, but task-completion outcomes remain unmeasured.
2. Does memory improve finding a specific component? Chess and task mini scripted target localization benchmarks provide mixed evidence. Robust semantic paraphrasing has not been achieved.
3. Can we reduce context payload without losing needed facts? Bounded context payloads are smaller than full-history dumps, but this is **not** measured end-to-end model token efficiency.
4. Can evidence go stale? v0.6+ attaches source revision fingerprints; these are freshness hints, not proof a note is right.
5. Can long history cause retrieval loss? v0.7 fixed known recency/FTS crowding cases; v0.8-rc2 added historical search beyond bounded briefs. Regressions should keep these issues from recurring.
6. Does local memory isolate projects and keep secrets safe? Synthetic and unit tests cover isolation and basic redaction/exclusion; a third-party security audit is pending.
7. Are agent memory benchmark scores predictive of work completed? Prior research summaries warn they are not; a held-out end-to-end agent trial is the highest-priority validation still missing.

## Related external research catalogued (not reverified during packaging)

- MemoryArena — multi-session agent tasks vs recall.
- LongMemEval / LoCoMo / MemoryAgentBench — evolving memories, temporal reasoning and abstention.
- MemTrace — evidence consistency with repository state.
- CORE-Bench — code-change localization.
- Graphiti — episodic/temporal knowledge representations.
- Model Context Protocol — portable agent/tool integration; version compatibility requires checking.

Detailed study notes and the citations originally collected live in `RESEARCH_OCT_2026.md`. The purpose of this package is preserving project work, not claiming a fresh literature survey.

## How to explore archival material

`research_archive/ARCHIVE_MANIFEST.json` enumerates the copied public-facing documents and benchmark JSON files from every historical source archive used. Each record identifies the archived source ZIP and its SHA-256. This archive intentionally **does not embed previous private test answer keys or full duplicate source trees**. Earlier code should be recovered from version-control history or its original ZIP if that is required; the current source is the release candidate provided here.
