# Backend workspace

Python 3.12–3.14 backend: authenticated FastAPI, durable LangGraph worker,
PostgreSQL/pgvector, reasoning/evidence/draft adapters, actual PDF, artifacts,
checkpoints and masked tracing. [Integration status](../../docs/team/INTEGRATION.md)
separates verified synthetic execution from live deployment prerequisites.

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r src/backend/requirements.lock
python -m pip install --no-deps -e src/backend
python -m pytest src/backend/tests -m "not integration" -q
navigator-runtime --env-file .env serve --host 127.0.0.1 --port 8000
# Separate terminal, same environment:
navigator-runtime --env-file .env worker
```

Copy root `.env.example` privately and fill identity/token bindings, application
DSN, checkpoint DB, artifact access, published profile and verified embedding
configuration/assets. Startup never migrates, ingests a corpus or downloads weights.
Eric completed the shared migration through `0007_frontend_lifecycle`;
see [host status](../../docs/team/MIGRATION_STATUS.md). Set up the separate framework database explicitly.
See [live setup](../../docs/data/LIVE_SETUP.md) and [deployment](../../docs/data/DEPLOYMENT.md).

Before startup: `python -m backend.deploy.check_runtime --env-file .env` checks
local settings/assets. Add `--network` for read-only infrastructure probes with
your SSH tunnel open. Neither mode migrates or runs cases; publication, provider
calls and artifact/checkpoint writes still require separate acceptance checks.

Core/test dependencies are locked. Hosted embeddings use
`requirements.hosted.lock` (tokenizer runtime, no local model weights);
[HF setup](../../docs/data/HOSTED_EMBEDDINGS.md) documents endpoint/config/tokenizer
requirements. Local models and connected web remain optional extras requiring
target-platform packaging. Hosted services require connected mode.

| Component | Local guidance |
| --- | --- |
| HTTP transport | [api](api/README.md) |
| Use cases / authorization | [application](application/README.md) |
| DTOs and ports | [contracts](contracts/README.md) |
| LangGraph coordination | [workflows](workflows/README.md) |
| PostgreSQL, retrieval and artifacts | [data](data/README.md) |
| Model adapters | [models](models/README.md) |
| Public acquisition and explicit corpus build | [ingestion](ingestion/README.md) |
| Retrieved material → evidence pack | [evidence](evidence/README.md) |
| Evidence pack → final output | [reports](reports/README.md) |
| Local tracing | [observability](observability/README.md) |
| Server configuration and profiles | [config](config/README.md) |

The [source architecture](../../docs/plans/SOURCE_STRUCTURE.md) owns component
boundaries; [HTTP handoff](../../docs/plans/FRONTEND_BACKEND_API.md) owns the current
frontend integration. Components can share one backend initially. Keep files
focused on single purposes, dependencies acyclic and SQL inside data adapters.
`application.factories` wires the three lanes without embedding business logic.

## Tests and local browser smoke

For the full suite, set `NAVIGATOR_TEST_ADMIN_DSN` to an **isolated disposable
PostgreSQL cluster with pgvector and the NOLOGIN navigator_app role**. Tests create
and delete their own databases. Never use Eric's shared development database.

```bash
python -m pytest src/backend/tests -q
# Optional: local synthetic API + worker, real A/B/C code, memory checkpoints.
PYTHONPATH=src python -m backend.tests.runtime.smoke
```

The smoke server requires that same test-admin DSN, binds only localhost:8000,
prints its test-only token and removes its temporary database on shutdown. Start
the [frontend](../frontend/README.md) separately. Synthetic model/embedding adapters
are explicit here and never selected by production factories.

## Feature agent entry point

Use [module handoffs](../../docs/plans/MODULE_HANDOFFS.md) for focused read paths,
DTOs, owned directories and integration checks. Provider setup lives in
[inference configuration](../../docs/data/INFERENCE_CONFIGURATION.md); model
credentials stay server-side. [Active questions](../../docs/project/OPEN_QUESTIONS.md)
distinguish blocked live inputs from independent fixture work. Do not edit
`src/frontend/`; request consumer changes through the HTTP contract.
