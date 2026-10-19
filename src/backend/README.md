# Backend

Python 3.12–3.14, FastAPI, Pydantic, SQLAlchemy/psycopg, Alembic and a separate
durable LangGraph/LangChain worker. PostgreSQL/pgvector stores authorized evidence,
cases and retrieval; artifact, checkpoint and optional trace stores have separate
roles. Exact interfaces live in `contracts/`; composition in `application/`.

From root:

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r src/backend/requirements.lock
.venv/bin/python -m pip install --no-deps -e src/backend
```

Provision private settings, infrastructure, profile and compatible model assets
using the [runbook](../../docs/data/LIVE_SETUP.md). Then `make server` / `make worker`
show logs, or `make all` starts local services in background. Startup never migrates,
ingests, publishes or downloads weights. Hosted embeddings add
`requirements.hosted.lock`; reranker assets are explicit. Crawl4AI has a separate
venv/lock and must not be installed into the backend environment.

```bash
.venv/bin/python -m backend.deploy.check_runtime --env-file src/backend/deploy/.env
.venv/bin/python -m backend.deploy.check_runtime --env-file src/backend/deploy/.env --network
.venv/bin/python -m pytest src/backend/tests -m "not integration" -q
.venv/bin/python -m backend.data.schema_docs --check
```

Full tests require an explicitly disposable `NAVIGATOR_TEST_ADMIN_DSN`, pgvector
and test-role setup; they create/drop databases. Never use shared infrastructure.
[Verification](../../docs/judges/VERIFICATION.md) and the
[quickstart synthetic harness](../../docs/judges/QUICKSTART.md) describe scope.

| Components | Guidance |
| --- | --- |
| [API](api/README.md), [application](application/README.md), [contracts](contracts/README.md) | [HTTP](../../docs/plans/FRONTEND_BACKEND_API.md), [service ports](../../docs/plans/SERVICE_CONTRACTS.md) |
| [Workflows](workflows/README.md), [evidence](evidence/README.md), [reports](reports/README.md) | [Operations](../../docs/plans/OPERATIONS_PLAN.md), [processing](../../docs/plans/REPORT_PROCESSING_BOUNDARIES.md) |
| [Data](data/README.md), [ingestion](ingestion/README.md), [models](models/README.md) | [Data layer](../../docs/data/DATA_LAYER.md), [ingestion](../../docs/data/ingestion/INGESTION_SPEC.md) |
| [Configuration](config/README.md), [observability](observability/README.md), [evaluation](evaluation/README.md) | [Deployment](../../docs/data/DEPLOYMENT.md), [evaluation](../../docs/challenge/EVALUATION.md) |

Read the [module map](../../docs/plans/MODULE_HANDOFFS.md) before changing shared
interfaces. Source migration head is 0012; the maintainer verifies host rollout.
