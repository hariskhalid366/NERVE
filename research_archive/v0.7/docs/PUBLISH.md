# Publish NERVE (maintainer steps)

This snapshot is packaged as a local release and **has not been pushed to GitHub**. The connected GitHub actions available to the build environment did not expose repository creation, and no confirmed NERVE repository was accessible. Do not invent a repository URL.

1. Create a **public** repository `NERVE` at https://github.com/new, with no initial README, license or gitignore (the archive already contains them). If an initial public code review is needed, create it as private first and deliberately switch visibility later.
2. Extract the release archive and review its files. Make sure you are at the root containing `pyproject.toml`.
3. Confirm no `.nerve/`, `.env`, secrets, or benchmark fixtures containing private data are staged.
4. Push explicitly:

```bash
git init -b main
git add .
git status --short
git commit -m "Release NERVE v0.4 developer preview"
git remote add origin https://github.com/YOUR_ACCOUNT/NERVE.git
git push -u origin main
```

5. In the GitHub repo description: *Local-first, evidence-backed project memory and observation tools for AI agents (developer preview).* Add topics: `mcp`, `local-first`, `agent-memory`, `developer-tools`, `sqlite`, `open-source`.
6. Create a `v0.4.0-preview` GitHub release using the archive and clearly link the outstanding release checklist. Do not market unmeasured productivity gains as measured improvements.
7. Only after the repo exists, connect it in Railway. Deploy a private single-project test instance, configure random agent and observer tokens and a `/data` volume, and verify health/authenticated endpoints. See [cloud deployment](../CLOUD_DEPLOY.md).

**Safety:** This is a public developer preview, not a secure multi-user hosted memory service. Do not publish tokens or personal project memories.
