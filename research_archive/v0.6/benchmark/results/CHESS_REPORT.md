# NERVE v0.5 — chess project dogfood report

**Run type:** local deterministic integration evaluation, not an LLM efficacy study. 22 October 2026. Input project: `examples/chess-mini`.

## Tested software

- Little Chess is a browser chess board implemented in standard ESM JavaScript, HTML and CSS, with no runtime packages. It loads over a static HTTP server.
- Automated Node engine tests cover standard positions, promotion, castling, checkmate, repetition, etc. **16/16 passed**.
- NERVE Python suite, including two new real-project regression tests and lexical retrieval safety tests: **35/35 passed**.
- The original v0.4 scanner ignored `.mjs` source files. v0.5 now indexes `.mjs`, `.cjs`, `.mts`, `.cts`; in this project it found **6 permitted files and 46 symbols**.
- A fresh MCP subprocess successfully initialized, exposed 8 tools, resolved a target, and read a note written by a prior closed process.

## Results — deterministic target matching

| Query style | NERVE v0.5 | Equal-data flat word-overlap baseline |
|---|---:|---:|
| Exact symbol/file names | 12/12 (100%) | 2/12 (16.7%) |
| Aliases | 12/12 (100%) | 12/12 (100%) |
| Historical bug descriptions | 10/12 (83.3%) | 10/12 (83.3%) |
| Indirect/paraphrased references | 4/12 (33.3%) | 6/12 (50%) |
| **Overall** | **38/48 (79.2%)** | **30/48 (62.5%)** |

For reference, the *untuned* NERVE scoring algorithm on this same project yielded **32/48 (66.7%)**. The result after inspecting and tuning on those queries is **not a held-out gain**.

- NERVE got **8/10** unsupported questions with zero candidates; **10/10** avoided the `supported_candidate` label. Some irrelevant candidates remain, and *all* candidate responses require external confirmation before acting.
- On the 12 known exact target IDs, a new handle recovered both the expected note and event on **12/12**. This shows persistence, not comprehension or correct answer generation by a fresh LLM.
- A separately spawned MCP process successfully returned the expected identity and an A-recorded note. This is not a genuine cross-model handoff task.
- Average selected result payload was **781.4 word/punctuation pieces**, against **9,043** pieces for full project history: **91.36% less serialized material** compared with dumping everything. This **does not measure tokens billed to a model** and excludes the cost of ingestion and MCP tool calls.

## What cannot yet be claimed

No performance gain in actual model context recovery, cross-agent task completion, or provider-reported tokens has been measured. An in-sample 48-question diagnostic has high sampling uncertainty and selection bias. NERVE also still **underperforms the simple baseline on paraphrases**. The improvement priority is semantic or hybrid retrieval with calibration on a held-out set.

## Versioned artifacts

- Machine-readable results: `CHESS_DOGFOOD.json`.
- Before-query-tuning run on the same chess project: `CHESS_BEFORE_RANKING.json`.
- Reproducer: `python -m benchmark.chess.run`.
- Game tests: `examples/chess-mini/tests/rules.test.mjs`.
