# Module guide for contributors and agents

Choose the row matching the feature, inspect its actual code and nearest README,
then read the focused specs. These boundaries support independent work; they do
not assign permanent ownership to named engineers.

| Module | Purpose | Focused context |
| --- | --- | --- |
| `api/`, `application/` | HTTP, identities, transactions, cases/reviews/exports, queue | [HTTP](FRONTEND_BACKEND_API.md), [case lineage](../data/CASE_STATE_AND_LINEAGE.md) |
| `workflows/` | Durable stage order, branching, budgets, clarification and recovery | [Operations](OPERATIONS_PLAN.md), [service ports](SERVICE_CONTRACTS.md) |
| `models/reasoning/`, `evidence/` | Structured interpretation, extraction and semantic assessment | [Processing](REPORT_PROCESSING_BOUNDARIES.md), [inference](../data/INFERENCE_CONFIGURATION.md) |
| `reports/` | Assessed writing and reviewed artifact rendering | [Output](OUTPUT_REPORT_STRUCTURE.md), [rich outputs](../data/RICH_OUTPUTS.md) |
| `data/` | Authorized persistence, artifact access, hybrid retrieval | [Schema](../data/RELATIONAL_SCHEMA.md), [retrieval](../data/RETRIEVAL_SPEC.md) |
| `ingestion/` | Public acquisition, canonical sources, taxonomy/curation and builds | [Ingestion](../data/ingestion/INGESTION_SPEC.md), [provenance](../data/DATA_AND_PROVENANCE.md) |
| `models/embeddings/`, `models/reranking/` | Compatible encoding and ranking | [Embeddings](../data/HOSTED_EMBEDDINGS.md), [reranker](../data/RERANKING.md) |
| `config/`, `deploy/`, `observability/` | Settings, services, readiness and safe diagnostics | [Runbook](../data/LIVE_SETUP.md), [deployment](../data/DEPLOYMENT.md), [traces](../data/OBSERVABILITY.md) |
| `evaluation/`, `tests/` | Contract, isolation, workflow and quality checks | [Verification](../judges/VERIFICATION.md), [evaluation](../challenge/EVALUATION.md) |
| `frontend/` | Browser interaction over `NavigatorApi` | [UI](FRONTEND_PLAN.md), [HTTP](FRONTEND_BACKEND_API.md) |

`contracts/data.py`, `contracts/pipeline.py` and `contracts/services.py` define
shared types. Change contracts with their consumers; avoid competing schemas.
`data/schema.py` plus migrations define storage; generated
[columns](../data/SCHEMA_REFERENCE.md) must remain in sync. Inspect OpenAPI for
transport details. Agree shared-file changes and migration numbering before
parallel edits, preserve worktrees and avoid unrelated formatting changes.

Checks should exercise behavior at the changed boundary. Database integration
uses disposable infrastructure only. Missing adapters fail explicitly in runtime;
synthetic providers are selected only by explicit tests/demo harnesses.
