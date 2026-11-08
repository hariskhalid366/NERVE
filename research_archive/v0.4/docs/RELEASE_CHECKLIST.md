# Release checklist — NERVE v0.4 developer preview

## Verified in local runtime

- [x] Python core tests and new local workflow tests passed.
- [x] Project SQLite persistence across independent Python processes.
- [x] Offline wheel installation and memory retrieval in an isolated Python virtual environment (Linux).
- [x] Opt-in Git metadata observer excludes `.env` and commit messages.
- [x] Cursor config generator preserves existing MCP servers and refuses overwrites.
- [x] Cloud HTTP contract tests run locally.
- [x] Opt-in Git post-commit hook integration test and multiple parallel memory writer test.
- [x] Built-in offline MCP stdio JSON-RPC subprocess simulated handshake and tool invocation.
- [x] Existing v0.3 synthetic diagnostic available as baseline.

## Must complete before declaring production-ready

- [ ] Publish source to a confirmed GitHub repository.
- [ ] Test MCP v2 handshake against actual Cursor/Claude/another supported host.
- [ ] Re-run benchmarks in independent *real* projects with provider token measurements.
- [ ] Obtain external security review and implement retention, scopes and quotas for hosted sharing.
- [ ] Deploy actual cloud instance with restricted credentials and a persistent volume, check HTTPS and backups.
- [ ] Run compatibility tests for Windows, macOS and Linux.
- [ ] Validate public onboarding from clean machine and publish installation packages.

**Distribution:** use the ZIP artifact until a GitHub repository exists. Do not claim a public GitHub URL or deployed production service without verifying them.
