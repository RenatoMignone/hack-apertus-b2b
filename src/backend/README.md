# Backend workspace

Python 3.12 data services are implemented: PostgreSQL repositories and migrations,
hybrid retrieval, artifact storage, checkpoint persistence, local tracing and
the `navigator` administration CLI. See [deployment](../../docs/data/DEPLOYMENT.md).
The HTTP server/framework and full product workflows remain separate work.

| Component | Local guidance |
| --- | --- |
| HTTP transport | [api](api/README.md) |
| Use cases / authorization | [application](application/README.md) |
| DTOs and ports | [contracts](contracts/README.md) |
| LangGraph coordination | [workflows](workflows/README.md) |
| PostgreSQL, retrieval and artifacts | [data](data/README.md) |
| Model adapters | [models](models/README.md) |
| Acquisition boundary, deferred | [ingestion](ingestion/README.md) |
| Retrieved material → evidence pack | [evidence](evidence/README.md) |
| Evidence pack → final output | [reports](reports/README.md) |
| Local tracing | [observability](observability/README.md) |
| Server configuration and profiles | [config](config/README.md) |

The [source architecture](../../docs/plans/SOURCE_STRUCTURE.md) owns component
boundaries; [HTTP handoff](../../docs/plans/FRONTEND_BACKEND_API.md) owns the draft
frontend integration. Components can share one backend initially. Keep files
focused on single purposes, dependencies acyclic and SQL inside data adapters.
The future bootstrap wires adapters; it must not become the business-logic file.

## U8 implementation boundary

The agreed [case pipeline](../../docs/plans/REPORT_PROCESSING_BOUNDARIES.md) defines interpretation, parallel DB/web research,
supported frozen packs, reason-card review and PDF-first export. This change
implements contracts and persistence only; frontend remains on mocks. Live models,
search/scraping, HTTP, LangGraph execution and rendering are future integrations.

## Feature agent entry point

Use [module handoffs](../../docs/plans/MODULE_HANDOFFS.md) for focused read paths,
DTOs, owned directories and integration checks. Provider setup lives in
[inference configuration](../../docs/data/INFERENCE_CONFIGURATION.md); model
credentials stay server-side. [Active questions](../../docs/project/OPEN_QUESTIONS.md)
distinguish blocked live inputs from independent fixture work. Do not edit
`src/frontend/`; request consumer changes through the HTTP contract.
