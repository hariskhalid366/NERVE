# NERVE Cloud (v0.4 developer preview) — Deployment and integration

**Status:** deployable prototype. It has been tested locally against FastAPI's HTTP test client, **not deployed to a hosting account**. This is a single-project, single-tenant server intended for private testing, **not** an internet-scale multi-user service.

## What lives in the cloud?

- A FastAPI HTTPS-facing JSON API that stores object identities, latest reported states, events, and project notes.
- SQLite persisted on a **durable volume** at `NERVE_DATA_DIR/project/.nerve/memory.sqlite3`.
- A credential for agents to **read context and add notes** (`NERVE_AGENT_TOKEN`).
- A **different** credential for observers to **write observations and events only** (`NERVE_OBSERVER_TOKEN`).
- A host-independent local stdio MCP connector (`python -m nerve.cloud_mcp`) that forwards agent tool calls over authenticated HTTPS.

**Not supported yet:** hosted remote MCP/OAuth, multi-user tenancy and registration, fine-grained per-agent permissions, rate limits, sensor discovery, automatic screen or microphone captures, content encryption at rest by the application, attested provenance, retention/deletion API, production backups, horizontal scaling, or automatic environment adapters. The server never reaches into users' computers. Adapters must explicitly submit permitted data.

## Deploy to Railway (recommended for prototype)

1. Push the `NERVE-v0.4-release` folder contents to a private GitHub repository (do not add `.env` or credentials).
2. In Railway, **New Project → Deploy from GitHub repo**, and select your repository. Railway detects this `Dockerfile` and `railway.toml`.
3. Add a **persistent volume** mounted at `/data`. **This is required**: SQLite memory is otherwise lost on redeployment. Run only **one application replica** with this SQLite setup.
4. In the service's **Variables** panel, add:

   ```text
   NERVE_DATA_DIR=/data
   NERVE_AGENT_TOKEN=<generated-long-secret-1>
   NERVE_OBSERVER_TOKEN=<different-generated-long-secret-2>
   ```

   Generate each secret separately in a local terminal:

   ```bash
   python -c 'import secrets; print(secrets.token_urlsafe(48))'
   ```

   Do **not** use the placeholder strings above; the tokens are passwords and must not be committed or shared in AI prompts, screenshots, issue threads, or log files.
5. Deploy. In Railway service **Settings → Networking → Generate Domain** to get an HTTPS URL such as `https://YOUR-NERVE-SERVICE.up.railway.app`.
6. Test unauthenticated health:

   ```bash
   curl https://YOUR-NERVE-SERVICE.up.railway.app/healthz
   # {"status":"ok"}
   ```

7. Test authenticated evidence retrieval from your local machine:

   ```bash
   export NERVE_AGENT_TOKEN='<agent-token-from-Railway>'
   curl -sS 'https://YOUR-NERVE-SERVICE.up.railway.app/v1/recent' \
     -X POST -H "Authorization: Bearer $NERVE_AGENT_TOKEN" \
     -H 'Content-Type: application/json' -d '{}'
   ```

   The API **fails closed** with 503 if tokens are missing, too short, or identical. Unauthorized access returns 401.

Railway documentation: [Deploy FastAPI](https://docs.railway.com/guides/fastapi), [Persistent Volumes](https://docs.railway.com/volumes), [Variables](https://docs.railway.com/variables). A volume or hosting usage may incur costs according to your plan.

## Local dry-run before deploying

```bash
cd NERVE-v0.4-release
python -m venv .venv
source .venv/bin/activate
pip install -e '.[cloud]'

export NERVE_DATA_DIR="$(pwd)/.nerve-cloud-data"
export NERVE_AGENT_TOKEN="$(python -c 'import secrets;print(secrets.token_urlsafe(48))')"
export NERVE_OBSERVER_TOKEN="$(python -c 'import secrets;print(secrets.token_urlsafe(48))')"
uvicorn nerve.cloud_api:app --host 127.0.0.1 --port 8000
```

The second local terminal uses the same tokens exported above. The local test allows unencrypted `http://127.0.0.1:8000`; **all remote agent connections must use HTTPS**.

## Connect external AI agents through local MCP

On each authorized AI host, install the Python project with the MCP extra:

```bash
pip install -e '.[mcp]'
```

Provide credentials using the host's **secret/environment-variable configuration**, not prompt text:

```text
NERVE_CLOUD_URL=https://YOUR-NERVE-SERVICE.up.railway.app
NERVE_AGENT_TOKEN=YOUR_AGENT_SECRET
```

Configure the MCP host's stdio server command:

```json
{
  "mcpServers": {
    "nerve-cloud": {
      "command": "/ABSOLUTE/PATH/.venv/bin/python",
      "args": ["-m", "nerve.cloud_mcp"],
      "env": {
        "NERVE_CLOUD_URL": "https://YOUR-NERVE-SERVICE.up.railway.app",
        "NERVE_AGENT_TOKEN": "ENTER_SECRET_IN_SECURE_HOST_CONFIG"
      }
    }
  }
}
```

This structure is representative; each host has its own settings format and support. The code uses MCP Python SDK v2 (`MCPServer`) through standard input/output. **The hosted service itself is REST**, and **the MCP bridge runs on each agent's machine**. It is not a public remote MCP endpoint, and no model automatically gains access to it.

The bridge exposes four tools:

| MCP tool | REST call | Access |
| --- | --- | --- |
| `resolve_target` | `POST /v1/resolve` | agent |
| `get_target_context` | `POST /v1/context` | agent |
| `get_recent_activity` | `POST /v1/recent` | agent |
| `remember_context` | `POST /v1/remember` | agent |

**Trust:** Notes authored by agents are explicitly recorded with `author=remote-agent`; they are not verified observations. Treat all events and notes as potentially adversarial/untrusted external content.

## Connect a permitted observation adapter

An adapter is an opt-in client installed in a user's app, browser extension, editor, or device that sends specific *structured* observations and events.

```bash
export NERVE_CLOUD_URL='https://YOUR-NERVE-SERVICE.up.railway.app'
export NERVE_OBSERVER_TOKEN='<observer-token-from-Railway>'

curl -sS "$NERVE_CLOUD_URL/v1/observe" -X POST \
  -H "Authorization: Bearer $NERVE_OBSERVER_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"target_id":"demo:setting:save","label":"Save settings","kind":"button","aliases":["apply preferences"],"state":{"enabled":true}}'

curl -sS "$NERVE_CLOUD_URL/v1/event" -X POST \
  -H "Authorization: Bearer $NERVE_OBSERVER_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"target_id":"demo:setting:save","event_type":"failure","message":"Save action timed out"}'
```

Now an authorized agent can retrieve that context:

```bash
curl -sS "$NERVE_CLOUD_URL/v1/resolve" -X POST \
  -H "Authorization: Bearer $NERVE_AGENT_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"query":"the settings save control with the timeout"}'
```

Every observation is a timestamped **report**, not proof that the live state remains unchanged. The current prototype only receives data: **it cannot autonomously inspect a device**. A real observer adapter is the next implementation milestone.

## Security and privacy checklist before real usage

- Keep NERVE private while evaluating; public internet exposure must be behind TLS and access restrictions. Do not send sensitive user data or customer production records to this prototype.
- Protect and periodically rotate the two tokens. The observer token cannot read memories; the agent token cannot submit sensor observations. However, **all agents currently share one agent token**, without individual identity or revocation.
- A hosting provider's HTTPS endpoint encrypts data in transit; the application does **not** encrypt SQLite at rest. Review the platform's volume encryption and backup policies.
- The current best-effort field-name redaction is not a comprehensive PII/secrets filter; avoid sending raw secrets, full browser pages, arbitrary personal data or private messages.
- Apply retention and deletion policies and scoped access before adding other users. No public observation endpoints without authentication; no network-wide surveillance.
- Do not run multiple replicas with a single mounted SQLite volume. To scale horizontally, redesign with Postgres, per-project OAuth/authorization, a queue, audit trail, and source-specific permission grants.
- Tool outputs and observed data can contain prompt injection. An AI host must treat them as **untrusted evidence**, not privileged instructions.
- Back up `/data` as required for any durable use. This prototype does not automate backups.

## Run tests

```bash
pip install -e '.[cloud]'
python -m unittest discover -s tests -v
```

At time of packaging, **13 unit/integration-style HTTP contract tests passed**, including role isolation, persistence across API client instances, oversized input rejection, and HTTPS requirement in the client. No hosted deployment has been verified and MCP v2 host integration is pending.
