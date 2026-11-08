# Chess dogfood benchmark (v0.5)

**Purpose:** inspect a runnable software project, persist a series of observations, close the writing process, and verify whether another process can retrieve them via local MCP. Compare target candidate ranking against a minimal flat lexical search.

The **chess project is a real, runnable implementation**. The 12 memory notes and incident events are **deliberately constructed evaluation fixtures**, not historical evidence of real users or real AI agents. The original code regression suite validates the project. The benchmark's records are seeded by a script, not a model.

## Reproduce (from repository root)

```bash
PYTHONPATH="$(pwd)" python -m benchmark.chess.run --output benchmark/results/CHESS_DOGFOOD.json
PYTHONPATH="$(pwd)" python -m unittest discover -s tests -v
cd examples/chess-mini && node --test tests/*.test.mjs
```

No cloud account, model API, npm install, or internet connection is required. Node 18+ and Python 3.11+ are used. The benchmark runs in a fresh temporary directory, with a new NERVE database and separate MCP-process session on every invocation.

## What the four requested metrics mean here

1. **Target accuracy:** `nerve.resolve()` Top-1 object ID against a gold ID in a fixed dataset. 48 queries cover names, aliases, historic incidents, and free paraphrases; plus 10 unsupported questions. This is **deterministic retrieval accuracy**, not LLM target selection or successful editing.
2. **Context recovery:** using a *known exact ID*, how many seeded notes and events can a second connection retrieve? Does not test an AI's ability to synthesize an answer. Also checks a fresh MCP subprocess can resolve and fetch A's notes.
3. **Cross-agent continuity:** the first (A-like) process seeds memory, closes it; a different (B-like) process reopens it through MCP and recovers records. **No second LLM agent is running; this is a transport/persistence prerequisite only.**
4. **Token efficiency:** the difference between serializing all stored history and returning a selected candidate + context. The counter counts words/punctuation **pieces**, not actual provider tokens; it omits ingestion and response generation. This is a *payload proxy against full history*, not a competitive token efficiency result against RAG/notes or an AI agent.

## Comparison conditions

The simple flat baseline is a bag-of-words lookup over the **same stored labels, aliases, descriptions, notes and events** with uniform token overlap. NERVE has weighted evidence fields and special treatment of exact matches. This is deliberately a weak comparison; higher performance does **not** prove superiority over semantic search, lexical BM25, vector search, file-based agent memory or human notes.

The v0.5 ranking rules were modified after examining these queries. **This is an in-sample engineering regression test, NOT held-out benchmark evidence.** For deployment-quality claims, freeze the algorithm first and use independent projects and unseen queries.

## Scope and limitations

- No tested LLMs, provider token counts, API latency/cost, task completion, real UI-agent sessions, or production host interoperability.
- No semantic embedding index. Indirect descriptions and ambiguous targets remain weak.
- All stored observations could be outdated; users/agents must confirm current source state before acting.
- Do not commit `.nerve/` databases with private user data. This benchmark stores harmless fictional examples in a temp directory.

See [`../agent_eval.py`](../agent_eval.py) and [`../../docs/REAL_PROJECT_PILOT.md`](../../docs/REAL_PROJECT_PILOT.md) for subsequent real-agent trials.
