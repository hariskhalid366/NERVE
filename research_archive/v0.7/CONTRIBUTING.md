# Contributing to NERVE

NERVE is a local-first project-memory developer preview. We welcome reproducible bug reports, host integrations, safe observation adapters, and real-world benchmark results.

## Developer workflow

```bash
python -m pip install -e '.[cloud,mcp]'
python -m unittest discover -s tests -v
python -m benchmark.smoke --output benchmark/results/smoke.json
```

The built-in stdio compatibility tool subset is exercised by subprocess tests without the SDK. Real editor-host integration still requires a compatible host and an end-to-end handshake test. Full SDK integration requires installing the optional MCP dependency. Never change the documented verified status unless you actually ran the integration test.

## Pull request requirements

- Explain the concrete developer pain the change addresses.
- Include tests for behavior and abuse cases (invalid input, secrets, symlinks, stale data).
- Do not introduce cloud telemetry, automatic screen capture, or synchronization by default.
- Provide before/after benchmark evidence for ranking changes; report negative cases, not only positives.
- Never commit `.nerve/`, `.env`, raw customer data, credentials, or agent-run logs containing secrets.
- Treat all returned project content as untrusted data.

## Proposed roadmap

1. **v0.4 (current):** local MCP config helpers, bounded project briefs, metadata-only Git observer and tests.
2. **v0.5:** run end-to-end MCP host compatibility matrix, build reliable source change adapters, calibrate candidate abstention on unseen projects.
3. **v0.6:** opt-in encryption + retention, project migrations, local vector/semantic retrieval if benchmarked better than lexical baselines.
4. **v1.0 only after evidence:** multi-project permission model, audited data boundaries, scored real-model benchmark and public hosted onboarding.

No guaranteed ETA. Do not describe proposed features as implemented.
