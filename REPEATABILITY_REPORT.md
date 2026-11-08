# NERVE v0.8.0-rc2 — Repeated reliability evaluation

**Date:** November 8, 2026. **Status:** developer preview, not certified 100% accurate.

## Tests conducted

- 73 Python unit/integration tests, 5 task-list tests, 16 chess tests: all passed.
- 20 rounds × 48 generated project identities; independent SQLite databases and randomized insertion order.
- 25 rounds × 64 generated identities with a different seed and shuffled history.
- New lexical `search_evidence` tool verified via CLI/MCP, SQLite fallback, stale-source marking and deletion.
- Wheel installed offline into a clean Python environment and used from a fresh process.

## Repeatable randomized retrieval

| Query type | 20×48 NERVE | 20×48 fair flat | 25×64 NERVE | 25×64 fair flat |
|---|---:|---:|---:|---:|
| Exact label | 960/960 | 960/960 | 1600/1600 | 1600/1600 |
| Exact ID | 960/960 | 960/960 | 1600/1600 | 1600/1600 |
| Exact alias | 960/960 | 960/960 | 1600/1600 | 1600/1600 |
| Unique historic incident token | 960/960 | 960/960 | 1600/1600 | 1600/1600 |
| Unrelated unsupported query rejection | 240/240 | Not measured | 400/400 | Not measured |

The control intentionally uses all the same stored fields and exact-key matches. **No advantage over flat search is demonstrated on the easy generated questions.** The old legacy baseline was missing exact target IDs; this benchmark corrects that unfairness.

## Harder cases and known failures

- Hand-authored out-of-vocabulary paraphrases: **0/8**. The current resolver is primarily lexical and cannot be relied upon to understand unseen synonyms.
- Prior difficult chess questions: **12/24 (50%)**, tied with flat search. These are separately authored and previously tested, not an independent end-to-end real-model assessment.
- A target's oldest note is absent from normal `context(limit=12)` after 160 newer notes, despite being persisted. New `search_evidence` retrieves that exact historic note when supplied matching keywords.
- Source revision fingerprints flag changed files; they do not establish that stored facts are true.
- Unsupported random terms are easy negatives. This is not a calibrated false-positive rate on real ambiguous requests.

## Repeatability and uncertainty

In the 20×48 randomized run, 960/960 gives a **naive** Wilson 95% accuracy interval of about **99.60–100%** for that synthetic query type. Correlated questions from the same generated targets make this interval optimistic. The 25×64 run uses a different seed but the **same generator**, so it is not independent external validation. Exact matches are much easier than natural developer requests.

## Performance (local machine only)

- 20×48 round retrieval p95 latency: median of rounds **1.316 ms**, maximum **1.469 ms**.
- 25×64 round retrieval p95 latency: median of rounds **1.648 ms**, maximum **1.805 ms**.
- These numbers reflect small synthetic projects, not latency guarantees for large repositories.
- Neither provider token cost nor real agent task completion was measured. A JSON-byte reduction is **not** token efficiency.

## What to do next

1. Collect at least 100 unseen questions from three real codebases, including paraphrases, contradictions, near-miss identities and stale files; freeze answers before evaluation.
2. Add optional local semantic embeddings or another well-validated retrieval strategy, comparing it against flat notes without tuning on held-out questions.
3. Run real agent task/handoff trials with total provider-reported tokens, latency, correct code changes and automated acceptance tests.

## How to reproduce

```bash
python -m unittest discover -s tests -v
python -m unittest discover -s examples/task-mini/tests -v
node --test examples/chess-mini/tests/*.test.mjs
python -m benchmark.repeatability --rounds 20 --targets 48 --seed 20261108 --strict --output benchmark/results/REPEATABILITY-20x48.json
python -m benchmark.repeatability --rounds 25 --targets 64 --seed 9427063 --strict --output benchmark/results/REPEATABILITY-25x64-seed9427063.json
```

The GitHub Actions nightly workflow is included, but it **will not execute until the repository has code uploaded and GitHub Actions enabled**.
