# NERVE v0.4 — local deterministic diagnostic (2026-10-20)

**Scope:** synthetic hand-authored data and heuristic retrieval; no LLM invoked. This is not evidence of improved AI intelligence, actual token efficiency, or real cross-model task success.

| Diagnostic | Result |
| --- | ---: |
| Known-object Top-1 target resolution | 65/80 = **81.25%** |
| Simple flat lexical baseline Top-1 | 65/80 = **81.25%** |
| Indirect paraphrase target Top-1 | 5/20 = **25%** |
| Unrelated queries with no candidate | 10/10 = **100%** |
| Unsupported near-miss queries with no candidate | 0/10 = **0%** |
| Candidates marked `supported_candidate` on positives | 63/80 = **78.75%** |
| Top-1 accuracy *among supported candidates* | 62/63 = **98.41%** |
| Unsupported near-misses marked confirmation/no match | 8/10 = **80%** |
| Cross-session SQLite persistence for 20 exact facts | 20/20 = **100%** |
| Raw context-payload reduction (word/punctuation pieces) | **91.72%** |
| Provider-reported token savings | **NOT MEASURED** |
| Real agent context recovery and handoff | **NOT MEASURED** |

**Important caveat:** The new candidate advisory does not improve target ranking. It declines to endorse some ambiguous answers, but still incorrectly marks **2/10 unsupported near-misses** as supported. The advisory is *uncalibrated* and every result still requires verification. The 98.41% figure is conditional on selecting 63/80 positive cases; do not present it as overall accuracy.

**Reproduction:** `python -m benchmark.smoke --output benchmark/results/smoke-v04.json`, with the full per-case results in `smoke-v04.json`.

**Engineering next step:** benchmark semantic retrieval on independent held-out real projects, negative target rejection and stale-object temporal correctness, then repeat using real models and actual token usage.
