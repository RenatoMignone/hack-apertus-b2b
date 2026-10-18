# Backend workspace

Reserved for an HTTP server and modular backend services. No language/framework,
entry point, dependencies or runnable implementation have been selected.

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
