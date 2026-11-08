# NERVE development roadmap: evidence before claims

## What exists now (v0.4 preview)

- Dependency-free local Python + SQLite project memory, identity/alias index, recorded events and decisions.
- Local CLI and opt-in metadata scan; bounded memory brief at session start.
- Project MCP via official SDK v2 when installed or small built-in stdio tools subset otherwise.
- Opt-in Git commit metadata observer that doesn't read source diffs or commit messages.
- Single-project cloud REST prototype with role-separated tokens, Docker and Railway manifest. **No live cloud deployment yet.**
- Deterministic synthetic diagnostics, per-query reports, and blind trial log scorer.

## Next high-value engineering tasks (not complete)

1. **Real host interoperability:** test the same memory read/write workflow through Cursor, Claude, Codex or other compatible hosts; report host versions and exact protocol issues.
2. **Target accuracy and calibration:** obtain a heterogeneous held-out dataset, add retrieval and negative abstention metrics, introduce optional on-device semantic retrieval only if it beats a simple search baseline.
3. **Memory lifecycle:** clear provenance, edit/retraction semantics, retention and TTL, snapshot summaries, scoped permissions, conflict resolution, safe deduplication.
4. **Developer usability:** editor plugin / automatic opted-in observer, human-readable timeline explorer, one-command installation, measured startup performance.
5. **True cross-agent evaluation:** A investigates project; B independently resumes in clean session using either simple notes or NERVE; external tests determine task success. Report provider token usage, cost and time fairly.
6. **Cloud sharing:** per-project and per-device keys, authorization, encrypted optional sync, retention, quotas, audit, backup and migration strategy; no public tenant onboarding until threat model reviewed.
7. **Open-source publication:** after GitHub repository creation, publish code, CI and release, request security review and third-party replications.

## Release gates

- No claims of token improvement without provider token counts and completion parity.
- No claims of cross-model continuity without separate actual models/agents on controlled tasks.
- No claim of strong target accuracy unless held-out data contains renamed objects, ambiguous references, and unsupported targets.
- No claim of production-ready cloud storage without identity, retention, threat model, backup and monitored deployment.

See [real-project pilot](REAL_PROJECT_PILOT.md), [security notes](SECURITY.md) and [release checklist](RELEASE_CHECKLIST.md).
