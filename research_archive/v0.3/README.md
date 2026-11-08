# NERVE — shared nervous system for AI agents

**v0.3 benchmark-enabled, cloud-ready prototype.** NERVE provides evidence-backed, project-scoped identity and memory for multiple AI agents. Authorized observer adapters can report structured object state and events; authorized AI agents can resolve vague references, retrieve history, and leave shared notes **without screenshots** when sufficient context has been observed.

**Start here: [CLOUD_DEPLOY.md](CLOUD_DEPLOY.md)** — Railway deployment, role-scoped keys, HTTPS API, optional MCP bridge, privacy and operational limitations.

## What is included

| Component | Status |
| --- | --- |
| Local SQLite NERVE object/identity/memory store | Working, tested |
| Local project metadata indexer | Working, tested |
| Local opt-in HTTP observation collector | Working, tested |
| Cloud REST gateway with two authorization roles | Working, tested locally |
| Dockerfile and Railway config | Included; not deployed in this package |
| Local MCP v2-to-cloud adapter | Implemented; host integration not yet tested |
| Universal automatic browser/desktop/device observer | Not implemented yet |
| Hosted multi-user OAuth MCP server | Not implemented yet |

## Design boundaries

- NERVE does not give models consciousness, unauthenticated access, or continuous environmental awareness by itself.
- Data is scoped to one explicit project per instance; sharing an agent credential grants access to that project's full recorded history.
- An observer must be installed and approved for its environment; it only uploads structured reports, not covert recordings.
- An observed state can become stale. Agents should verify age, source and last event before claiming current status.
- MCP integration requires an AI host to support and authorize tool connections; the cloud REST API does not automatically connect to ChatGPT.

## Structure

```text
nerve/
  core.py        local SQLite identities, notes, events, evidence resolver
  cli.py         local maintenance, scan, context, delete and collector commands
  collector.py   loopback-only observer receiver
  mcp_server.py  local stdio MCP integration (project-local mode)
  cloud_api.py   hosted authenticated JSON REST API
  cloud_client.py  HTTPS agent API client
  cloud_mcp.py   stdio MCP tools backed by NERVE Cloud
Dockerfile       cloud container
railway.toml     Railway health check + Docker build
CLOUD_DEPLOY.md  deployment and integration guide
ARCHITECTURE.md  design goals and roadmap
```

Run core/cloud HTTP tests:

```bash
pip install -e '.[cloud]'
python -m unittest discover -s tests -v
```

For older local CLI usage, see `nerve/cli.py`, or run `python -m nerve --help`.

MIT licensed. Treat this as a prototype; implement production authorization, quotas, safe retention, per-source identity, audit, backups, threat modeling, and a real observation adapter before offering it to other users.

## Benchmark suite (v0.3 evaluation add-on)

See [BENCHMARK.md](BENCHMARK.md) for experimental design and the runnable synthetic smoke test. The report **does not** establish real LLM performance or token savings. Use `python -m benchmark.smoke` to reproduce the diagnostic and `python -m benchmark.agent_eval export` to prepare blind real-agent trials. Cloud deployment remains optional.
