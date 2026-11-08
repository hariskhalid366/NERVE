# Little Chess — a real NERVE dogfood project

A dependency-free two-player chess game in the browser. It includes legal move validation, check/checkmate, stalemate, promotion, en passant, castling, undo, draw claims, and simple move history. Its board is interactive, but there is no AI opponent, multiplayer backend, clocks, or full tournament adjudication.

**Run:** from this directory, execute `python -m http.server 8000`, then open `http://localhost:8000/`. **Test:** `node --test tests/*.test.mjs` (Node 18+).

## Why this project?

NERVE's local memory should track decisions and resolved issues about real source targets (`chess.mjs` move legality, `app.mjs` move selection, `style.css` board sizing) and let a *fresh process* retrieve them. The benchmark seed data are invented but scoped to real functions and checked against this actual code. The test proves file/symbol indexing, persistence, retrieval, and the offline MCP transport; it does **not** simulate an LLM's reasoning or measure LLM usage costs.

## Privacy

`nerve --project . init` creates `.nerve/memory.sqlite3`. Keep `.nerve/` out of Git. The chess fixture is suitable for public release: the stored examples are fictional and contain no personal data.
