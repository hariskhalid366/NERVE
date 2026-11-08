# NERVE — Complete Project Handoff for Codex

**Authoritative source snapshot:** `v0.8.0-rc2` (8 November 2026). This ZIP contains the project source at its root, its test projects, the source distribution wheel, raw benchmark files, and a curated archive of available historical research and results.

## Your objective

NERVE is a **local-first, offline-capable project memory system for AI coding agents**. It stores project-scoped identities, incidents, decisions and evidence outside the model's context window, so another authorized agent can retrieve them in another session. The user wants NERVE to be reusable by developers working in restricted local environments; the user has *deprioritized cloud deployment*. Immediate priorities are publishing a safe, accurate GitHub repository, measuring real-agent benefits, and improving semantic retrieval without sacrificing privacy.

**Do not imply that the model gained permanent internal memory or that NERVE prevents hallucinations.** The model can use memories only when an authorized tool/agent connects to the correct project store and explicitly retrieves them.

## Start here (recommended sequence)

1. Read `PROJECT_CONTEXT.md`, `docs/handoff/ARCHITECTURE_AND_WORKFLOW.md`, `docs/handoff/RESEARCH_TIMELINE.md`, `docs/handoff/BENCHMARK_LEDGER.md`, and `docs/handoff/OPEN_ISSUES_AND_NEXT_STEPS.md`.
2. Inspect `nerve/`, `benchmark/`, `tests/`, `examples/chess-mini/` and `examples/task-mini/`.
3. Run the offline test commands below. Do not assume previous reports are evidence for new changes.
4. Use `research_archive/` only for tracing historical decisions; **the current `nerve/` directory is the authoritative implementation**. Some old research may describe abandoned approaches.
5. If GitHub publishing is requested, confirm that the environment has Git write permission for `hariskhalid366/NERVE`, inspect the staged files for secrets/private project data, push to `main` only once safe, and verify the remote commit/README/CI afterward. Do not publish hidden answer keys or `.nerve/` databases.

## Run validation from this directory

```bash
python -m unittest discover -s tests -q
python -m unittest discover -s examples/task-mini/tests -q
node --test examples/chess-mini/tests/rules.test.mjs
```

This packaging session reran these tests successfully on **Python 3.13.5** and **Node 22.16.0**: 73 Python NERVE tests, 5 task-list tests, 16 chess-engine tests. A clean-environment offline wheel installation, project initialization, memory write and subsequent brief retrieval also passed in this handoff session. The previous archive's randomized/scale benchmarks are stored as JSON under `benchmark/results/` and are *not automatically rerun by the three test commands*.

## Try it locally in a separate project

```bash
python -m pip install --no-index --no-deps dist/nerve_agent_memory-0.8.0rc2-py3-none-any.whl
nerve --project /absolute/path/to/your-project init
nerve --project /absolute/path/to/your-project scan
nerve --project /absolute/path/to/your-project brief
nerve --project /absolute/path/to/your-project doctor
nerve --project /absolute/path/to/your-project cursor-config --write
```

Local project memory lives under `/absolute/path/to/your-project/.nerve/`, which must not be committed to Git. NERVE **does not** automatically write every conversation to memory; agent integration must call the relevant tools and only store approved context.

## What's inside

- `nerve/` — current Python package (SQLite memory, code scanner, evidence search, MCP server, CLI, optional observers/cloud prototype).
- `tests/` — automated Python regression suite.
- `benchmark/` — retrieval, repeatability, multi-agent evaluation scaffolding and recorded JSON results.
- `examples/chess-mini/`, `examples/task-mini/` — independent runnable toy projects used for dogfood and retrieval experiments.
- `docs/` and root documents — architecture, usage, roadmap, security, public release and research.
- `research_archive/v0.1` through `research_archive/v0.8.0-rc1` — available *documentation and public benchmark evidence* from previous packages, not historical copies of the entire implementation.
- `docs/handoff/` — this conversation's consolidated objective, timeline, benchmark ledger, status, privacy constraints and publication plan.
- `dist/` — offline Python wheel (provided for testing/release attachment, usually not committed to Git).

## What has NOT been validated

- No independent, unseen end-to-end trials showing increased coding-task completion for actual AI models.
- No provider-reported token/cost savings including ingestion and MCP traffic.
- No full cross-model agent A→B task-success benchmark (a new MCP process reading memory is not that).
- No proof of general semantic understanding: an 8-question unseen-synonym probe scored **0/8** and harder chess retrieval was **12/24**, identical to flat search.
- No cloud deployment needed for the current user goal; no guarantee of modern MCP host interoperability, cross-platform CI or third-party security certification.
- GitHub publication is not verified in this archive. The repository was confirmed to exist and be public, but Chat-mode GitHub write attempts returned HTTP 403. Codex's Git credentials are separate.

## Safety guardrails

Do not commit `.env`, secrets, private identifiers, `.nerve/` databases, private test answer keys, git credentials, source archives containing private fixtures, runtime caches or developer-specific local paths. Do not claim 100% accuracy based on synthetic exact-match scores. Before release, use the `docs/handoff/RELEASE_AND_PUBLISH_PLAYBOOK.md` checklist and verify the remote repository.

## Research and evidence navigation

For the full evolution, see `docs/handoff/RESEARCH_TIMELINE.md` and `research_archive/ARCHIVE_MANIFEST.json`. For current reproducible results, prefer `REPEATABILITY_REPORT.md`, `BENCHMARK.md`, `benchmark/results/PAIRED_METRICS.json`, `benchmark/results/PUBLIC-CHECK-RC2.json`, and `benchmark/results/REPEATABILITY-25x64-seed9427063.json`.
