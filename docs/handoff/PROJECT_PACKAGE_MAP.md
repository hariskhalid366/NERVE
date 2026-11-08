# Package contents and evidence map

This ZIP is designed for **Codex handoff, offline inspection and reproducibility**. Only one authoritative source implementation is shipped, located at the root. The archive of past versions contains selected documentation and benchmark data, not full duplicate code trees.

| Path | Role |
|---|---|
| `START_HERE_CODEX.md` | Start here; project goals, validation, access boundaries and instructions. |
| `AGENTS.md` | Agent-facing development and integrity rules. |
| `PROJECT_CONTEXT.md` | What user wants, scope, constraints and acceptance criteria. |
| `nerve/` | Current Python application and MCP/CLI implementation. |
| `tests/` | Current automated Python tests. |
| `benchmark/` | Repeatability, real-agent scorer scaffolding, retrieval checks and raw evidence. |
| `examples/chess-mini/` | Browser chess dogfood project and JS engine tests. |
| `examples/task-mini/` | Python task list dogfood project and tests. |
| `dist/` | Offline wheel, built in prior release process. |
| `.github/` | CI workflows and contribution templates. |
| `docs/handoff/` | Consolidated flow, timeline, metrics, open issues and publishing playbook. |
| `research_archive/` | Version-specific research documents and public benchmark results extracted from earlier ZIP releases. |
| `research_archive/ARCHIVE_MANIFEST.json` | Exact archived file list, source ZIP filenames, SHA-256 for provenance. |
| `PACKAGING_VERIFICATION.json` | Packaging-session validation results and file audit. |
| `SHA256SUMS.txt` | SHA-256 checksums for all files in the ZIP's source tree (generated at packaging). |

## Distinguish current from historic evidence

Current: `REPEATABILITY_REPORT.md`, current `benchmark/results/*`, current `CHANGELOG.md` and test source. Historic: `research_archive/v0.x` docs, which may record now-fixed bugs or superseded benchmark protocols. New developer changes must be tested afresh; copying an old success report is not fresh evidence.
