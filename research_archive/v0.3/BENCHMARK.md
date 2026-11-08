# NERVE Benchmark Suite (NBS) — v0.1 methodology

**Do not advertise prototype diagnostics as real AI model gains.** The package includes a deterministic smoke diagnostic and a scoring format for *future, externally executed* AI-agent trials. Baselines must be measured first and versions must be pinned.

## Four primary metrics

| Metric | Definition | Important limitations |
|---|---|---|
| Context recovery | `correct answers / queries`, with gold facts hidden from the agent during evaluation. Record exactness, evidence citations, and abstention on unknown facts. | Retrieval of a fact into tool output is NOT equivalent to answering correctly. |
| Token efficiency | `total provider-reported input tokens for all tasks / number of successful tasks`, compared across matched tasks and models. Track total input and output tokens separately. | A low token count is worthless if accuracy decreases. Include memory ingestion, MCP/tool exchanges, retry turns, and prompt compaction. The smoke diagnostic only measures word/punctuation *pieces* in data payloads, **not model tokens**. |
| Cross-agent continuity | `successful B-agent tasks / B-agent handoff tasks` after A-agent finishes and its session is closed; change models and repeat. | Opening SQLite and reading a stored fact proves persistence, not another LLM completing a task. |
| Target accuracy | Top-1 target ID accuracy, Recall@3, false selection rate, and abstention on unsupported requests. Distinguish labels, aliases, historical references, ambiguous phrasing, and paraphrases. | Candidate retrieval is not the same as agent selection or acting correctly. |

## Fair comparison arms

All arms get the same base project state, permitted observer instrumentation, task goals, model and time limits. The differences below are the only permitted memory intervention. The observer feed must not secretly give NERVE additional ground-truth facts not available from the same observations to control arms.

- `no_memory`: task starts with fresh conversation; may inspect project/source files, but no previous session memory.
- `flat_notes`: agent receives the same shared history as ordinary text notes/files and can search it with ordinary tools.
- `nerve`: agent queries the project's NERVE MCP tools; notes written during the ingest stage are structurally equivalent to `flat_notes` content.

For full-history comparisons, add a separate clearly named control with a larger context budget; don't conflate it with `flat_notes`. If NERVE costs ingest tokens, count those tokens. If controls must rebuild state, count that work as well. Match task conditions, budget and API model version, and use randomized task order. Don't use the gold `answer` during agent prompts, retrieval indexes created by answers, or agent decisions.

## Current deterministic smoke diagnostic (run locally)

```bash
cd NERVE-cloud-v0.3
PYTHONPATH=. python -m benchmark.smoke --output benchmark/results/smoke.json
python -m unittest discover -s tests -v
```

- 20 synthetic objects, 80 target queries (20 labels + 20 aliases + 20 historical clues + 20 paraphrases), 10 unrelated unknown queries, and 10 near-miss unsupported questions.
- Agent A creates the indexed objects, events and notes then closes its DB handle. Agent B creates a fresh handle before querying.
- NERVE's heuristic retrieval is compared against a naive flat bag-of-words lookup over the same object facts.
- Full-history payload contains the **actual records from the populated NERVE store**. NERVE's selected payload includes retrieval results and one target context. A word+punctuation piece counter computes only a *rough context-size proxy*. No tokenizer/API billing information is used.
- Smoke measurements are **not** model reasoning accuracy, end-to-end handoff outcomes or measured API-token savings.
- Query styles and their gold answers are hand-authored and intentionally easy in three categories. This is a regression test set, not an independent external benchmark.

## Real-agent trial file protocol

Produce blind inputs and private gold answers:

```bash
PYTHONPATH=. python -m benchmark.agent_eval export --dir benchmark/results/agent_trials
```

- Give the agent harness **only** `agent_prompts.jsonl`, the project test environment, and allowed memory tools. Never expose `gold_private.json`.
- Run paired arms for the *same model and seed* on each test. Ingest the same source facts through the same observation mechanisms. Initialize independent project fixtures per trial; do not let trial output leak into another arm.
- In cross-agent cases, close A's session; launch B with no hidden history; record model names as `agent_a`/`agent_b`, and set `handoff_completed: true` only for a real completed A→B handoff. For reproducible models, use three or more different random seeds; for deterministic models repeat across projects.
- Write one JSON object per run to `runs.jsonl` with: `case_id`, `arm` (`no_memory`, `flat_notes`, `nerve`), `model`, `seed`, `target_id`, `answer`, `input_tokens`, `output_tokens`, `latency_ms`. Optional: `agent_a`, `agent_b`, `handoff_completed`. Token counts MUST come from the actual model provider or instrumented client, not estimated from the input length.
- Grade with `PYTHONPATH=. python -m benchmark.agent_eval score --runs benchmark/results/agent_trials/runs.jsonl`. The evaluator rejects the included example placeholder and compares only genuinely supplied records.
- Strict grading requires an exact target ID and normalized exact factual answer. Correct paraphrases may be unfairly scored wrong; supplement with blinded human adjudication or independent task tests before making public claims.
- Reports include Wilson confidence intervals and same-model paired comparisons where both arms are present. More robust CIs (e.g. bootstrap paired by project, with confidence intervals) and task-validity auditing are required before publication.

## Criteria for announcing a measured improvement

Proposed minimum gates—not scientifically proven universal standards:

1. Target Top-1 >=90% on **held-out** targets and ≥85% on held-out paraphrases; abstention on unobserved/unsupported details >=90%.
2. Context recovery >=90% on supported known-information tasks, and exceeds `flat_notes` with paired 95% CI excluding 0 or a preregistered significance test.
3. Cross-agent task completion >=85% with at least 3 genuinely different model families involved; show gain over equivalent flat handoff notes.
4. Provider-reported input tokens per successful task <=70% of flat-notes control, **without a drop** in task success, counting setup and writes in the amortized experiment.
5. Benchmark at least 100 *unseen* realistic cases from >=3 projects, task order randomized, with a separately tracked ambiguous/unsupported cohort. Report sample size, cost, 95% intervals, all failures and version hashes.

## External validity roadmap

- Add LongMemEval-V2 for agentic memory, original LongMemEval for longitudinal chat QA, and LoCoMo for long conversation retrieval. Do not call our synthetic test a LongMemEval score.
- Use an agent harness that supports live tool calls; otherwise the measurements are retrieval-only.
- Add actual action outcomes: test suite passes, correct files changed, target confirmation before destructive actions, stale observation rejection, and no cross-project memory leakage.
- Keep synthetic and held-out cases separate to prevent tuning on the test set.

## Security

Do not commit real project `.nerve/memory.sqlite3` or secrets; benchmark fixtures contain invented data. The optional cloud host does not validate model effectiveness by itself. Treat observation tools as scoped and potentially sensitive; measure exposure and incorrect-identity actions separately.
