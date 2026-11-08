# NERVE v0.7 — Evaluation summary

**Date:** November 8, 2026. **Status:** local-first developer preview / evaluated candidate, not a production release.

## Key outcomes

- **Tests:** 52/52 Python unit and integration tests passed; 16/16 mini-chess rules tests passed.
- **Memory continuity:** Separate-process MCP initialization, target resolution and exact-ID retrieval passed; new test events/notes were read back from stored SQLite history. This is not proof of two independently reasoning AI models solving a task.
- **Paired chess target accuracy:** 38/48 NERVE versus 30/48 flat lexical on the previously tuned set; McNemar exact two-sided p=0.076813. On a harder 24-query set, both methods scored 12/24 (p=1.0). No robust evidence of a general semantic accuracy advantage.
- **Long-history defects fixed:** target-scoped notes no longer vanish from context beneath new project notes; old events stay searchable after newer events; rare old incidents survive 6,201-event common-term-flood stress. Older SQLite databases are migrated and deletion/FTS behavior is regression-tested.
- **Concurrent storage:** 8 processes wrote 600/600 events plus 600/600 memories without failed workers; SQLite integrity check returned `ok`.
- **Crash recovery:** a committed note remained accessible after abrupt process termination.
- **Scalability:** 120 exact alias lookups for each of 100, 500, 1500, and 3000 targets yielded 120/120 each; NERVE v0.7 95th-percentile query latency ranged 1.41 to 37.20 milliseconds in this one local run. This cannot predict host performance.
- **Memory footprint:** approximately 1.61 MB SQLite for 3000 synthetic targets, 3000 synthetic events and 3000 synthetic notes (about 19.4% above v0.6 because of the full-text index).
- **Context size:** NERVE serialized response averaged 2606.9 bytes versus 25313 bytes for a naive full-history dump, an **89.7% smaller payload**. This is **not** a model-token or monetary savings measurement, and 10/48 target matches were wrong.
- **Self-use proof:** this audit stored verified NERVE findings and recovered them from a new local MCP subprocess. It does not install NERVE into ChatGPT's core or share it across user accounts.

## Limitations that matter

- No actual usage telemetry from OpenAI/Anthropic/Google inference, no live IDE host confirmation, and no independent multi-agent successful-task comparison.
- Automatically indexed filenames and code symbols do not equal semantic comprehension. Unseeded descriptive matching over the tool's own source got only 6/18 queries right.
- Full-text search still caps common-token matches; very old generic references may remain ambiguous or unreachable by natural-language search. It is a candidate resolver, not an autonomous permission to edit code.
- The local database is not encrypted by NERVE; only best-effort redaction is included. Protect projects and backups. No system-level or cross-user installation is possible through this conversation.

## Next steps

1. Run a held-out real-model evaluation across no-memory, README-only, and NERVE conditions, collecting actual per-successful-task tokens and task accuracy.
2. Develop and benchmark an optional, offline semantic retrieval mechanism on previously unseen codebases.
3. Verify MCP integration in real local coding-agent hosts and expand security tests before a public v1.0 release.

For exact queries, detailed result JSON and reproduction instructions, use the included `docs/CAPABILITY_AUDIT_2026-11-08.md` and `audit/` directory.
