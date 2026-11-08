# NERVE release and GitHub publishing playbook

## Target

**Repository:** `https://github.com/hariskhalid366/NERVE`

**Version:** `v0.8.0-rc2` preview; current GitHub source was not verified published when this handoff was packaged. Cloud deployment is excluded.

The Chat-mode GitHub API showed public repository metadata but returned `403 Resource not accessible by integration` for file and Git-blob creation. Do not retry unauthorized credentials or claim remote success. Use a git-capable environment with user-approved repository write access, which might require the user to authorize Codex. Do not ask for personal tokens in chat.

## Source staging

This archive is the complete development handoff, **not a command to publish every historical attachment**. For GitHub, prefer the top-level current project package, `nerve/`, `tests/`, `benchmark/`, `examples/`, `.github/`, public docs, `LICENSE`, and safe templates. The `research_archive/` folder is valuable for Codex handoff but optional for the public repository; avoid bloating public history with redundant old reports. `dist/` is a build artifact; attach the verified wheel to a GitHub Release rather than committing it unless the maintainer explicitly chooses otherwise.

Avoid including from local workspaces: `.env`, `.nerve/`, `.git/`, `*.sqlite*`, credentials, API tokens, hidden benchmark gold, build caches, screenshots of private accounts, or personal paths. `.env.example` contains placeholder text and may be public.

## Commands for authorized Git-capable Codex environment

```bash
# Start inside the extracted *source root* and run tests first.
python -m unittest discover -s tests -q
python -m unittest discover -s examples/task-mini/tests -q
node --test examples/chess-mini/tests/rules.test.mjs

git status --short
# Review before publishing and ensure no sensitive/private content is staged.
# If an empty remote exists, initialize the validated source into git:
git init
git branch -M main
git add .
git status --short
git diff --cached --check
git commit -m "Release NERVE v0.8.0-rc2 local-first developer preview"
git remote add origin https://github.com/hariskhalid366/NERVE.git
git push -u origin main
```

If a repo/branch already exists, **fetch and inspect it before deciding on a merge or push**; do not force-push over existing work. If a valid repository already exists, prefer a feature branch and PR. Do not blindly run `git init` or `git remote add` if already configured. If GitHub authorization is missing, stop and request the appropriate OAuth / device authorization in the Codex environment; never paste or solicit tokens in chat.

## Post-push checks

1. Open the repository and confirm README, license, code, tests, docs and workflows exist at the intended commit.
2. Compare remote SHA with the pushed local SHA; record the URL and exact commit hash.
3. Check GitHub Actions `CI` and repeated benchmarks. The scheduled repeated-benchmark workflow is **configured but not proven active until it runs on GitHub**.
4. Add a truthful repository description and discovery topics (see `docs/DISCOVERABILITY.md`), without guarantees about GitHub or Google search rank.
5. Only after source/CI checks, create an annotated `v0.8.0-rc2` release tag if that tag does not exist, attach the wheel and source ZIP with checksums, and label it **pre-release**.
6. Include release caveats: scripted tests only, semantic 0/8 in an OOV probe, real token savings and agent productivity unmeasured.

## Search/discoverability content

GitHub description suggestion: **"Local-first persistent project memory for AI coding agents — offline SQLite + MCP, context recovery, cross-session handoff, evidence freshness and reproducible benchmarks."**

Topics to consider (subject to GitHub limits/allowed strings): `ai-agent`, `agent-memory`, `mcp`, `local-first`, `persistent-memory`, `context-management`, `multi-agent`, `coding-assistant`, `sqlite`, `offline-first`.

Use problem-first README sections answering searches about **AI context loss**, **coding assistants forgetting project changes**, **context drift**, **project memory across coding sessions**, and **hallucinations caused by missing context**. Don't promise eliminated hallucinations, exact token savings, guaranteed search ranking or consciousness.

## Release gate checklist

- [ ] Confirm current version matches package metadata and changelog.
- [ ] Verify all current test suites in the target environment.
- [ ] Run a security scan for credentials and local project data.
- [ ] Inspect test fixtures for hidden answers/private data.
- [ ] Publish and verify the actual commit; do not infer from a local bundle alone.
- [ ] Confirm GitHub Actions results on supported Python / operating systems.
- [ ] Rebuild or verify the offline wheel and attach checksums.
- [ ] Document measured metrics and known limitations clearly.
- [ ] Run external real-agent trials before a stable v1.0 effectiveness claim.
