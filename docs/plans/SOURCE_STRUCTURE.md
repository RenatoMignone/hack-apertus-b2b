# Source structure

```text
src/
  frontend/                 React browser application
  backend/
    api/                    HTTP routes, validation and response projection
    application/            Authorized use cases, transactions, queue and factories
    contracts/              Pydantic records, typed DTOs and service/repository ports
    workflows/              LangGraph nodes, durable execution and research loops
    data/
      repositories/         PostgreSQL authorization, persistence and projections
      migrations/           Forward application migrations
      retrieval/            Independent full-text/vector retrieval, RRF and ranking
      artifacts/            Source/report byte storage
    models/
      reasoning/            Apertus transport and structured task services
      embeddings/           Shared ingestion/query encoder protocol
      reranking/            Cross-encoder adapter and explicit provisioning
    ingestion/              Acquisition, normalization, taxonomy, review and builds
    evidence/               Extraction, support assessment and pack proposal
    reports/                Generation, validation and deterministic rendering
    observability/          Safe console events and masked Langfuse tracing
    config/                 Validated settings and domain/model profiles
    evaluation/             Pinned retrieval comparisons and quality metrics
```

API → application → workflow/services. Shared contracts do not import concrete
adapters. SQL belongs to `data/`; reasoning belongs to model/evidence/report
services; nodes coordinate typed calls. `application.bootstrap` and
`application.factories` compose dependencies. Backend modules are code boundaries,
not separately deployed microservices.

The frontend calls the versioned HTTP API. API and worker run independently with
compatible private settings. Source bytes, checkpoints and traces have separate
storage roles. Read the nearest README and [module map](MODULE_HANDOFFS.md) before
changing a module. Coordinate DTO, migration and frontend consumer changes; keep
files focused, imports acyclic and fixtures explicit.
