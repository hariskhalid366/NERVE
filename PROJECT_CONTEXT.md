# Project context and non-negotiable requirements

## What the user is building

**NERVE / Nervous System** is a general-purpose memory-and-observation layer that compatible AI agents can use *with permission*. It is intended to help agents retain context for a particular software project after a chat or agent run ends, recognize the same component/feature in later sessions, preserve technical decisions and prior failures, and hand context between agents. It must serve **local/offline developers first**, without relying on a cloud service, expensive LLM APIs, or no-code tools.

The ambition grew from “eyes/ears/nervous system for AI” into a project-scoped system with identities, event history, source revision evidence and an MCP interface. The first supported environment is source-code projects; arbitrary visual/live environment observation requires adapters and user consent. Do not describe future sensors or global cross-user memory as already working.

## User priorities stated throughout the conversation

- **Measurable benefits before marketing claims:** context recovery, target accuracy, cross-agent continuity, token efficiency, regression quality and false candidate rates.
- **Portable and open:** ZIP/installation support, Python offline wheel, clear setup and README, model-agnostic MCP access, public GitHub discovery.
- **Trustworthy comparisons:** compare with no memory and ordinary notes or fair flat lexical search, not a deliberately weak baseline; use unseen tasks; run repeated randomized regressions.
- **Local privacy:** individual projects own their database; no ambient surveillance, no silent cross-project sharing, no uploading local memories, no committing secrets.
- **Publication goal:** public repository `https://github.com/hariskhalid366/NERVE`, accurate README and SEO-friendly *problem vocabulary* (AI context loss, model forgetting, coding-assistant hallucination from lost context) without unverifiable “eliminates hallucinations” claims.
- **Cloud deployment paused:** a prior cloud prototype exists for research, but user explicitly chose to prioritize local storage and GitHub source release.

## Scope of current v0.8.0-rc2

- Python 3.11+ project-local SQLite database; code-file and symbol indexing; metadata-only Git observation as opt-in; project brief; object resolution, incident and memory notes; evidence freshness; historical evidence retrieval; CLI; stdio MCP fallback; synthetic and toy-project regression suites.
- Two dogfood projects: browser chess (JavaScript ESM) and task-list (Python).
- The user can share the same project-local memory among authorized agents only when they access the project path and use the NERVE tools. This is **tool-supported external storage**, not modifying the model weights or assistant's internal memory.
- A cloud API prototype exists in the source tree but is not the target deployment for the current release.

## Success criteria for a future stable release

1. Real cross-agent tasks and true provider-token measurements showing positive performance versus fair controls on held-out tasks.
2. Better handling of unseen paraphrases and uncertain/ambiguous targets; freshness and provenance checks remain intact.
3. Real-world MCP integration on supported hosts, cross-platform installer tests and security review.
4. Clean, permission-safe GitHub repository and reproducible benchmark artifacts, no credentials or private datasets.

## Working agreement for future agents

Keep dates and test data explicit. Never invent numbers, published status or changes. Distinguish tests in `tests/` from benchmarks in `benchmark/`, in-sample queries from unseen queries, and static tool retrieval from actual LLM task completion. When source revisions change, recheck facts. If a user asks to “continue,” open the context and current tests rather than start a parallel project.
