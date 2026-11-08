# Security and data handling (developer preview)

## Trust boundaries

1. **Host ↔ local MCP process:** An AI host spawns the server with access to the explicitly configured project root. Only grant MCP server launch and tool use to trusted workspaces and users. An untrusted project should not be allowed to execute arbitrary agent-invoked tooling.
2. **Local MCP process ↔ SQLite:** NERVE stores information in `.nerve/memory.sqlite3`; protect local filesystem permissions, backups, disk encryption, and `.gitignore`. Deleting the database deletes the index and memories, not copies backed up elsewhere.
3. **Observer ↔ NERVE:** Observations are submitted by opt-in adapters, not automatically trusted. Fields are sanitized only heuristically and can contain secrets, PII, incorrect data, or prompt injection. **Never submit confidential raw screenshots, conversations, keys, browser pages, or production logs.**
4. **NERVE ↔ model:** Retrieved data is untrusted tool output. It is evidence, not a new system instruction. Require confirmation before changing files or using stale observations.
5. **Cloud gateway:** `NERVE_AGENT_TOKEN` can read and write notes; `NERVE_OBSERVER_TOKEN` can write observations. They are single-project shared credentials and cannot safely support arbitrary third-party tenants. Use private HTTPS, a persistent volume, and secret management. No unauthenticated memory API.

## Data minimization defaults

- Local source indexing uses filenames and declared symbols. It reads files transiently to detect symbols; raw source bodies are not persisted.
- Excludes directories such as `.git`, `.venv`, `node_modules`, `.nerve`, build outputs, and `.env*` and key/certificate file extensions. These are best-effort, not a complete secret scanner.
- Optional `git-hook install` records SHA and permitted changed source filenames; it does not save the diff, commit body, or author details. The hook never overwrites another hook and can be removed.
- No automatic cloud upload or tracking in the local mode.
- Deletion: `nerve --project /path forget <target_id>` removes one target's event/note records. Project-scoped notes must be reviewed separately; SQLite deleted bytes may persist in WAL/backups until compacted or backups expire.

## Threat model and pending work

| Risk | Present mitigation | Needed before public multi-user usage |
| --- | --- | --- |
| Prompt injection in observations | Host safety guidance, tools treat observations as data | Structured provenance, source attestation, injection tests |
| Secret leakage from notes | Heuristic sanitizer, no default cloud sync | Client-side secret detection, encryption, allowlists |
| Compromised observer token | Write-only token, request-size limit | Per-device scoped credentials, revocation, rate limits |
| Compromised agent token | Authenticated reads | Per-user OAuth, per-project ACL and audit log |
| Stale state misinterpreted as live | Timestamps, explicit status cautions | Freshness policy and live verification protocol |
| Disk loss, concurrent writes | SQLite WAL, persistent volume guidance | Backups, retention policy, migrations and Postgres for scaling |
| Git hook interference | Refuses existing hook, opt-in only | Tests on Windows and worktree configurations |
| Untrusted source trees | Sandbox path validation and exclusions | Broader adversarial filesystem security audit |

**Not audited. Not production security certification.** Do not deploy it as a public service for unrelated users yet.
