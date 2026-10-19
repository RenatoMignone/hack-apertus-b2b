# Local application setup

Run from repository root. Use Python 3.12–3.14 (3.13 recommended), Node 22.18+,
Docker Compose v2 and GNU Make. Linux/macOS commands follow; Windows can use WSL
or the [PowerShell quickstart](../judges/QUICKSTART.md).

## Install

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r src/backend/requirements.lock
.venv/bin/python -m pip install --no-deps -e src/backend
(cd src/frontend && npm ci)
```

Hosted embeddings additionally need `requirements.hosted.lock` and the pinned
local tokenizer/configuration; see [encoder setup](HOSTED_EMBEDDINGS.md).
Optional reranker and web conversion have their own provisioning instructions.

## Private configuration

For a new developer environment, copy [.env.example](../../.env.example) into
ignored `src/backend/deploy/.env`, then fill real values. Preserve an existing
private environment instead of overwriting it. Restrict its file permissions.
Exported shell values take precedence over env-file values.

| Required input | Purpose |
| --- | --- |
| Application DSN, principal, namespace and narrow scope grants | Owned cases and authorized corpus reads; never use migration-owner credentials |
| `RUNTIME_AUTH_BINDINGS` | Server-side identity and token-digest mapping shared by API/worker |
| `RUNTIME_PROFILE_ID` and taxonomy pin | Accessible domain vocabulary and compatible corpus selection |
| Embedding configuration, tokenizer and endpoint/token or local assets | Query encoding compatible with indexed documents |
| `LANGGRAPH_DATABASE_URL` | Separate provisioned saver database/credential; plain psycopg PostgreSQL DSN |
| Artifact backend/bucket/application credential | Authorized source reads and report writes |
| `LLM_NAME`, `LLM_BASE_URL`, `LLM_API_KEY` | Explicit Apertus model/provider |

Shared servers require an operator bearer token whose SHA-256 digest is bound to
the intended principal. The browser holds the raw token in memory. For private
local testing, `RUNTIME_LOCAL_ACCESS=true` accepts loopback requests using exactly
one existing binding; it does not remove DB authorization or create credentials.
Keep it false for shared deployment. See [HTTP](../plans/FRONTEND_BACKEND_API.md).

If infrastructure is reached through SSH, keep the authorized tunnel running:

```text
ssh -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -L 15432:127.0.0.1:5432 -L 19000:127.0.0.1:9000 YOUR_USER@YOUR_HOST
```

Use privately supplied host/key/credentials. PostgreSQL and MinIO forwarding does
not grant application, checkpoint or object permissions. API/worker must agree
identity, profile, configuration and queue placement. Do not start competing workers
without coordination.

## Readiness

```bash
.venv/bin/python -m backend.deploy.check_runtime --env-file src/backend/deploy/.env
.venv/bin/python -m backend.deploy.check_runtime --env-file src/backend/deploy/.env --network
```

The first validates local settings/assets. The second adds read-only DB identity/
schema, checkpoint reads and bucket HEAD. Neither performs model calls, checkpoint
writes, authorized object read/write, migrations or full research acceptance.
Application startup checks schema without migrating. The source head is 0012;
the maintainer verifies/updates the actual host through [deployment](DEPLOYMENT.md).

## Four service commands

| Command | Behavior |
| --- | --- |
| `make docker` | Start local SearXNG Compose project and follow logs |
| `make server` | Start/reuse API on 127.0.0.1:8000 and follow logs |
| `make worker` | Start/reuse durable worker and follow logs |
| `make frontend` | Start/reuse Vite HTTP client on 127.0.0.1:5173 and follow logs |
| `make all` | Start all four in background; print URLs/log paths |
| `make destroy` | Stop Make-managed app process groups and local search project |
| `make help` | Usage and prerequisites |

[Makefile](../../Makefile) uses `src/backend/deploy/.env` by default;
`ENV_FILE=/private/path` overrides it. Logs/PID records are ignored under
`.local/dev-services/`. Repeated startup reuses tracked processes. Ctrl+C on an
app target stops that service; Ctrl+C on Docker ends log-following only. Destroy
preserves logs, volumes, SSH and shared infrastructure, and never kills unrelated
or manually started processes. Stop manual services before reusing their ports.

Make starts the **search sidecar**, not the shared PostgreSQL/MinIO stack. It does
not install dependencies, migrate, ingest or download models. Prepare
[web dependencies](WEB_RESEARCH.md) before enabling research. For manual startup:

```bash
.venv/bin/navigator-runtime --env-file src/backend/deploy/.env serve --host 127.0.0.1 --port 8000
# Separate terminal:
.venv/bin/navigator-runtime --env-file src/backend/deploy/.env worker
# Separate terminal:
(cd src/frontend && VITE_API_MODE=http npm run dev -- --host 127.0.0.1 --port 5173)
```

## Manual acceptance

Open the frontend, connect if bearer authentication is enabled, create a permitted
fictional company case, inspect actual progress/clarification, then sources and
caveats. Review every reason, keep one and download PDF. Verify wording-only edits,
focus changes, read-only history and stale-review rejection. Record source/model
pins, enabled capabilities, latency and failures. See [walkthrough](../judges/DEMO.md).
A 200 capability response is configuration evidence, not full pipeline health.
