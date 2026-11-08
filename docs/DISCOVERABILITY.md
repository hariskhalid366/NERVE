# GitHub discovery and honest SEO checklist

GitHub search prioritizes **repository name, description, and topics by default**; README search requires `in:readme`. The following is factual discoverability guidance, **not a promise to rank first**. See [GitHub repository search documentation](https://docs.github.com/en/search-github/searching-on-github/searching-for-repositories) and [GitHub topics](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics).

## Suggested repository settings

- **Repository name:** `NERVE` (or `nerve-agent-memory` if the short name is occupied)
- **About / Description** (copy exactly): `Local-first persistent memory for AI coding agents. An offline MCP server for project context recovery, multi-agent handoff and context drift.`
- **Topics** (add in GitHub > About > Edit; use only relevant tags): `ai-agent`, `agent-memory`, `llm`, `mcp`, `model-context-protocol`, `local-first`, `offline-first`, `developer-tools`, `coding-assistant`, `persistent-memory`, `context-management`, `multi-agent`, `python`, `sqlite`, `open-source`, `ai-coding`
- **Homepage:** leave unset until you have a real site or verified documentation URL. Do not invent a project domain.
- **Visibility:** public only after checking the ZIP/repo does not include secrets, database files, absolute machine paths, hidden evaluation answers not intended for publication, or other users' data.
- **First release title:** `NERVE v0.8.0-rc1 — Local-first AI agent project memory (developer preview)` (a release candidate, not a stable production guarantee).

## Search terms to explain naturally

Answer the actual question in docs and examples, instead of stuffing keywords:

- **"AI coding assistant forgets context" / "LLM context loss"** → persistent project notes, session-start retrieval.
- **"AI hallucinations from missing project context"** → source-linked evidence with freshness signals; not zero hallucinations.
- **"Cursor loses context" / "Claude Code memory" / "Codex project memory"** → MCP compatibility is host-dependent and must be verified.
- **"local MCP memory server"** → stdio setup, SQLite storage, offline installer.
- **"multi-agent memory shared between coding sessions"** → same-project authorized connections, evidence provenance and limitations.

## Search QA after publishing

Check GitHub repository search after indexing: `agent-memory in:name,description,topics`, `mcp local memory in:readme`, `context-management topic:context-management`, and `NERVE project memory`. Search ranking and indexing are controlled by GitHub and search engines; there is no guaranteed time or position. Update documentation when users report an actual missing workflow. Encourage authentic issues, reproducible demos, external benchmarks and helpful releases; never buy stars, spam keywords or claim unmeasured gains.

## Launch checklist

- [ ] Create or connect a repository; set About and topics.
- [ ] Push scanned, reviewable source, LICENSE, README, examples and tests.
- [ ] Inspect GitHub Actions outcome on Linux/macOS/Windows; fix platform failures before claiming support.
- [ ] Add a real release ZIP + wheel with SHA-256 checksums.
- [ ] Run an independent agent-host smoke test and publish exact environment versions.
- [ ] Ask early adopters for anonymized *reproducible* failed-context-recovery reports.
