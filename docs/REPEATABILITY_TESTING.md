# NERVE repeatability and reliability audit

**Evaluation date:** November 8, 2026. This audit is an offline deterministic
retrieval and storage evaluation; no AI provider, production environment or
real two-agent task completion was tested.

## Reproduce

```bash
python -m unittest discover -s tests -v
python -m unittest discover -s examples/task-mini/tests -v
node --test examples/chess-mini/tests/*.test.mjs
python -m benchmark.repeatability --rounds 20 --targets 48 --seed 20261108 --strict --output benchmark/results/REPEATABILITY-20x48.json
python -m benchmark.repeatability --rounds 25 --targets 64 --seed 9427063 --strict --output benchmark/results/REPEATABILITY-25x64-seed9427063.json
```

Both randomized experiments use **different fresh SQLite databases for each
round**. Observations are synthesized from deterministic random identifiers
and inserted in shuffled order; the tests use distinct exact target labels,
aliases and historical incident markers. These are easier than real developer
questions. The simple flat-text baseline sees the **same target IDs, labels,
aliases, descriptions, events, and notes** and checks exact keys as well.

## Results

| Test set | NERVE | Fair flat-text baseline |
|---|---:|---:|
| 20×48 exact names | 960/960 | 960/960 |
| 20×48 exact IDs | 960/960 | 960/960 |
| 20×48 aliases | 960/960 | 960/960 |
| 20×48 history keywords | 960/960 | 960/960 |
| 25×64 exact names | 1600/1600 | 1600/1600 |
| 25×64 exact IDs | 1600/1600 | 1600/1600 |
| 25×64 aliases | 1600/1600 | 1600/1600 |
| 25×64 history keywords | 1600/1600 | 1600/1600 |
| 20×48 unobserved unrelated queries | 240/240 rejected | Not compared |
| 25×64 unobserved unrelated queries | 400/400 rejected | Not compared |
| Semantically paraphrased descriptions | 0/8 | Not a representative sample |

The randomized suites were **not tests of semantic understanding**. The fair
baseline ties NERVE on exact retrieval; there is no advantage to advertise.
For 960/960 successful cases, the naive Wilson 95% lower bound is about
99.60%; this still does NOT establish a universal 100% accuracy rate, and
repeated queries from the same generated targets are not independent.

## Important cases

- 160 new notes can evict an old note from the default context response, even
  while it persists in SQLite. The new `search_evidence` API returns that old
  note when the query contains distinctive matching keywords.
- `search_evidence` is lexical, not semantic. A query with different words
  may find nothing; model integration or opt-in local embeddings would be
  needed for broader paraphrase understanding.
- Unsupported random strings are simple negatives; near-miss claims about
  an existing target still need agent-side source verification.
- Reopening a database in a new Python process demonstrates persistence, not
  genuine model-to-model handoff success.
- SQLite integrity after scripted writes is not a full data-corruption proof.

## Repeat on GitHub

`.github/workflows/repeated-benchmarks.yml` executes 10 rounds of 24 targets
nightly, after the repository is pushed and GitHub Actions is enabled. The
workflow archives JSON results even on benchmark failure.

## Release blockers for a broad 100%-accuracy claim

1. Independent unseen developer projects with realistic ambiguity, stale code,
   multiple collaborators and alternative phrasings.
2. Real agent tasks with matched no-memory, plain-note and NERVE conditions,
   plus provider-reported total input and output tokens.
3. Security review, editor-host MCP compatibility testing and confidence
   calibration to avoid unwarranted conclusions.

Do not tune on the held-out cases and then continue calling them held out.

## Final package verification

- 73 Python unit/integration tests passed.
- 5 additional task-list tests passed.
- 16 JavaScript chess-engine tests passed.
- The rc2 wheel installed offline into a newly created Python environment.
- A fresh-process MCP tool call retrieved evidence absent from recent context.
- The short original release audit still returned 19/24 task-list cases for NERVE
  versus 11/24 for the original flat lexical comparator; this is a different,
  hand-authored test and should not be conflated with randomized tests.

This evaluation does NOT certify arbitrary hallucination prevention or 100% accuracy.
