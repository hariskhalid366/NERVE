# NERVE Evaluation Baseline — 2026-10-20

**Prototype version:** v0.3 (v0.2 storage/resolver, v0.3 evaluator).  
**Test status:** 17/17 automated tests passed.  
**Scope:** purely local **synthetic deterministic retrieval diagnostic**, **not** a run of real AI agents, not a generalizable real-world improvement estimate.

## Results

| Metric | NERVE | Naive full-information lexical lookup | Interpretation |
|---|---:|---:|---|
| Target Top-1 on 80 known-object queries | 65/80 (81.25%) | 65/80 (81.25%) | No improvement demonstrated. |
| Target Recall@3 | 65/80 (81.25%) | 66/80 (82.50%) | NERVE slightly worse. |
| Label/alias/incident queries | 60/60 (100%) | 60/60 (100%) | This synthetic set has deliberately strong lexical clues. |
| Paraphrased queries | 5/20 (25%) | 5/20 (25%) | Both fail most semantic paraphrases. |
| Unknown unrelated: no candidate | 10/10 (100%) | 10/10 (100%) | Easy to reject unrelated gibberish. |
| Unsupported near-miss: no candidate | 0/10 (0%) | 0/10 (0%) | Both return some candidate despite missing issue-specific evidence. This is over-retrieval, not hallucination. |
| Context fact available after Top-1 resolution | 65/80 (81.25%) | Full history has 80/80 facts | Not actual model answer correctness. |
| DB persistence after A closes and B reopens | 20/20 (100%) | N/A | Only demonstrates SQLite durability, not actual cross-LLM task completion. |
| Raw full-history context size (piece proxy) | — | 8,008 pieces | Flat arm contains equivalent persisted records. |
| Mean NERVE selected context size (piece proxy) | 644.6 pieces | — | 91.95% fewer pieces **but** only 81.25% correct Top-1 matches; not token savings. |
| Provider-reported tokens | NOT MEASURED | NOT MEASURED | Need real model/API instrumentation. |
| Actual LLM context-recovery accuracy | NOT MEASURED | NOT MEASURED | Need paired, blinded model calls. |
| Actual cross-agent task completion | NOT MEASURED | NOT MEASURED | Need A and B agents executing tasks. |

**Interpretation:** Target resolution relies on lexical token overlap; only 25% of indirect paraphrases were matched. The next iteration should prioritize semantic retrieval, calibrated no-answer behavior, temporal update handling and verifying that adding a memory system beats simple searchable notes on *held-out tasks*.

## Reproduce

```bash
cd NERVE-cloud-v0.3
PYTHONPATH=. python -m benchmark.smoke --output benchmark/results/smoke.json
PYTHONPATH=. python -m unittest discover -s tests -v
PYTHONPATH=. python -m benchmark.agent_eval export --dir benchmark/results/agent_trials
```

Machine-readable per-case outcomes are in `smoke.json`. Exact thresholds, measurement definitions and blind real-model log grading are documented in `BENCHMARK.md`. Do not feed the included `scenarios.json` or `gold_private.json` to agents under evaluation; they contain gold answers.
