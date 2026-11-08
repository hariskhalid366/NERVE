# Ready-to-paste Codex task prompt

You are continuing NERVE, a local-first open-source persistent project memory tool for AI coding agents. Read `START_HERE_CODEX.md`, `PROJECT_CONTEXT.md`, `AGENTS.md`, and `docs/handoff/*`. The `nerve/` Python source at this ZIP's root is authoritative `v0.8.0-rc2`; `research_archive/` holds earlier research and benchmark reports for provenance. Do not rewrite from scratch or assume the model has built-in project memory. Inspect every module and current test before editing.

**Immediate tasks:** (1) Extract safely, run all NERVE, chess, and task-list tests, review security and packaging; (2) if your environment has authorized Git write access to `https://github.com/hariskhalid366/NERVE`, publish current clean source to `main` without exposing `.nerve` databases, secrets, private answer keys or stale build artifacts; verify the remote SHA/README/CI, and report actual outcomes; (3) plan/run a genuinely held-out cross-agent benchmark comparing no memory, flat notes and NERVE with provider-reported total tokens; (4) improve semantic/indirect-reference retrieval without eroding exact, stale-source, unknown-query, historical memory or privacy behavior. Do not deploy a cloud backend.

**Known issues:** chess stress 12/24 tied with baseline; separate paraphrases 0/8; no proven real LLM agent task-completion/token gains; GitHub publication wasn't verified when this ZIP was built. Treat all historical reports as recorded results, not current test evidence. If GitHub push permission is missing, report the exact permission error; do not ask for tokens in chat or claim publication succeeded.

**Test commands:**

```
python -m unittest discover -s tests -q
python -m unittest discover -s examples/task-mini/tests -q
node --test examples/chess-mini/tests/rules.test.mjs
```

Summarize changes and verification with actual command outputs, failure counts, source paths, commit SHA and external URLs only when checked.
