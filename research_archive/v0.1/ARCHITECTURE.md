# NERVE Architecture & roadmap

## Design target

A portable, consent-driven context layer that gives independent AI agents a *shared model of a specific project or environment*. Avoid building a proprietary chatbot. The model remains replaceable.

```text
                   [person: grants scope & consent]
                                 |
       +-------------------------+-------------------------+
       |                         |                         |
 [source indexer]        [app/browser adapter]      [future sensors]
 (static metadata)       (structured telemetry)    (explicit opt-in)
       |                         |                         |
       +---------------[NERVE ingest boundary]-------------+
                                 |
                          [Identity registry]
                           stable target IDs
                                 |
        +------------------------+-----------------------+
        |                        |                       |
   [Project memory]        [Event timeline]         [State snapshots]
   decisions/facts         provenance, timestamp     last reported
        |                        |                       |
        +------------------------+-----------------------+
                                 |
                       [Evidence resolver]
                       candidates + reasons
                                 |
                        [MCP tool adapter]
                                 |
                   [AI hosts / independent models]
                                 |
                 [Optional external action tools]
                    only with user permission
                                 |
                    [Fresh event verifies result]
```

## Entity identity contract

Every object needs:

- `target_id`: stable, opaque, namespace-qualified ID (e.g. `browser:tab13:button:submit`). Must not be inferred from screen coordinates alone.
- `label`, `kind`, `aliases`: human reference vocabulary.
- `source_path`, `locator`: how instrumentation can verify it exists, within the configured environment.
- `origin`: source-index, adapter, agent, etc. Provenance should eventually be cryptographically validated / scoped by trusted adapters.
- `updated_at`: last observation timestamp.
- `state`: limited structured properties only; sanitized before ingestion.

**Target identity is not the same thing as screen coordinates.** An AI may recognize a target from accessibility-tree IDs, DOM landmarks, API resource IDs, file symbols, or device identifiers. Visual images become optional supporting evidence.

## Evidence & retrieval

- User text refers to a target, perhaps indirectly.
- Resolver scores name, aliases, indexed path, descriptions and associated *recent event/memory* matches.
- Return top candidates with matched fields. This v0.1 score is a **ranking heuristic**, not a calibrated confidence probability.
- Agent reads exact-target context and checks observation age/source before answering.
- Ambiguous matches should result in a clarification question, not arbitrary selection.
- Target state should be refreshed by a trusted adapter for time-sensitive questions.

## Cross-agent memory

An agent that is authorized to write NERVE should write:
- explicit user decision,
- verified state transition,
- confirmed solution and verification evidence,
- unresolved question or caveat,
- links to target IDs / references.

Another agent should be able to answer without reconstructing all prior chat context. However, it should not promote hallucinated agent notes to facts: *decisions* and *observations* need provenance and approval workflows.

## Adapter direction

Adapters are the real differentiator:

1. Browser: DOM/accessibility tree, network failures, user-authorized visible events, semantic locators.
2. Desktop: accessibility APIs, focus, app/window identity, app-provided state events; never record globally by default.
3. Code editors: file, symbol, diagnostics, git changes, test results.
4. Backend/services: OpenTelemetry spans/logs with secret-filtering and stable resource IDs.
5. Hardware: opt-in sensors and explicit recording lifecycle.

For production adapters, define a schema version and a capability grant per source, such as `observe:appX.ui` or `read:projectY.events`. Bind events to provenance and reject untrusted agents pretending to be other sensors.

## Phased success criteria

v0.1: explicit observed target returns from a vague alias; event history and note survive process restart; another MCP host can read the same data (subject to host support); no screenshot required; no unauthenticated collector writes.

v0.2: at least one *real automatically instrumented* environment produces stable IDs and transitions; record source identity and freshness; exact object recalled across host restarts.

v0.3: multiple different model hosts resolve the same target consistently and can recover from drift or ambiguous aliases without making up a live state.

v1.0: security and privacy model hardened; local encryption policy, per-project/user/access scopes, content provenance and trusted adapters, deletion/export, no unintended cross-project leakage.

## Suggested benchmark

Use 100 tasks with 5–10 ambiguous target names per project. For each, record:
- target resolution top-1 and top-3 accuracy,
- wrong-object action rate (should approach zero via clarification),
- retrieval latency,
- percent of stale claims identified,
- share of tasks requiring an image,
- token/context savings between blind agent and NERVE-connected agent,
- cross-agent handoff success.

Don't claim NERVE improves reasoning or autonomy without controlled measurements.
