# Source structure and component boundaries

**18 October 2026 · Integrated application source.** Python 3.12–3.14 uses
FastAPI, LangGraph/LangChain, SQLAlchemy Core, psycopg, Alembic and Pydantic.
React/Vite defaults to HTTP; mock mode is explicit. API and worker are separate
processes. [Integration](../team/INTEGRATION.md) records verified scope;
[live setup](../data/LIVE_SETUP.md) lists rollout prerequisites. Start feature
work with [module handoffs](MODULE_HANDOFFS.md). Preserve root `src/`.

## Directory map

```text
src/
  README.md
  frontend/                 React browser client over HTTP; explicit demo mode
  backend/
    api/                    HTTP transport validation, routes and response mapping
    application/            Use cases, access checks and transaction coordination
    contracts/              Implemented DTOs/projection helpers; additional agreed ports
    workflows/              LangGraph graph composition and resumable stages
    data/
      repositories/         Canonical PostgreSQL records and transactions
      migrations/           Application schema migrations only
      retrieval/            Lexical/vector queries, fusion and ranking integration
      artifacts/            Controlled artifact storage adapters
    models/
      reasoning/            Apertus adapter
      embeddings/           EmbeddingGemma 2 adapter; revision/runtime pending
      reranking/            Reranker adapter
    ingestion/              Public acquisition, normalization, registry and build CLI
    evidence/               Retrieved evidence → frozen ReportEvidencePack
    reports/
      generation/           Pack → structured report revision
      validation/           Report claim/citation checks
      rendering/            Reviewed revision → downloadable artifacts
    observability/          Masked local Langfuse integration
    config/
      profiles/             Versioned domain-profile configuration
```

Component READMEs describe actual inputs/outputs and configuration. Subfolders
are module boundaries, not separate deployed services. Backend/docs tasks do not
edit `src/frontend/`; coordinate consumer changes with its owner.

## Communication and dependency rules

The browser communicates with the backend through versioned HTTP APIs. It never
connects directly to PostgreSQL, artifact volumes, models, LangGraph or Langfuse.
Backend capabilities can share one application initially; the durable worker runs
separately from the HTTP server. An accepted asynchronous HTTP request does not
imply an in-memory background task is durable.

```text
frontend --HTTP--> api --> application --> workflows
                              |               |
                              +--> contracts <+--> evidence / reports
                                      ^                |
                                      +-- data / models adapters

config supplies validated settings; observability receives masked events.
```

`contracts/` owns implemented typed payloads and narrow ports; add missing service
ports explicitly before consumer integration.
Specification authority remains [ingestion plan §7](INGESTION_PLAN.md#7-shared-contract-v1--owned-here-consumed-by-phase-2)
for shared evidence records, [architecture](ARCHITECTURE.md#evidence-pack-the-report-generation-gate)
for pack contents, and focused data specs for storage/lineage. Reuse contracts;
do not create unrelated HTTP, graph and database versions of a fact. HTTP can
expose a smaller eligible view without changing its identity.

| Component | Owns | Calls / boundaries |
| --- | --- | --- |
| `api` | HTTP validation, routes, projections and errors | Application use cases; no SQL, prompts or workflow logic in handlers |
| `application` | Authorized case/run/revision/review/export operations | Repository and workflow ports; caller identity from trusted backend integration |
| `workflows` | Bounded stage order, pause/resume/cancel and checkpoints | Contracts, evidence/report services and adapters; no HTTP types |
| `contracts` | Shared DTOs, validation definitions and narrow service/repository/model/storage ports | No framework, database, UI or model-client dependencies |
| `data` | PostgreSQL repositories, artifacts and hybrid retrieval | Contracts; retrieval uses injected embedding/reranking ports, never HTTP routes or graphs |
| `models` | Reasoning, embedding and reranking adapter behavior | Validated model configs; no routing, case ownership or publication policy |
| `ingestion` | Public acquisition/normalization and explicit corpus build | Controlled HTTP, Crawl4AI conversion, registry/MeSH/build CLI; case web never auto-publishes |
| `evidence` | Assessment and frozen pack boundary | Retrieval/record/model ports; does not generate the final report |
| `reports` | Drafting, claim/citation checks and rendering from a pack | Model/artifact ports; cannot silently search or mutate its pack |
| `observability` | Masked traces and diagnostic correlation | Local Langfuse; no authority over facts or run completion |
| `config` | Validated server settings and versioned profiles | No secrets in repository/frontend; `application.factories` wires adapters |

Application services and workflows use repository/storage ports rather than SQL
scattered across graph nodes or report functions. `data/` owns implementations;
`contracts/` owns interfaces. Keep business checks in evidence/report components
and HTTP errors in `api/`. Framework migrations use their supported tools,
outside application SQL migrations.

## File discipline and handoff

- One file has one purpose: route group, use case, record/port, adapter, stage or
  transformation. Split responsibilities; avoid one backend/model/report file.
- Keep imports acyclic. Contracts cannot import concrete adapters. `application.bootstrap` /
  `application.factories` own composition.
- Maintain the nearest README with public inputs/outputs, dependencies, unresolved
  choices and focused spec links. Central specs remain authoritative.
- Add meaningful contract/integration checks with implementation. No invented
  runnable commands or production fixture fallbacks.
- Unconfigured adapters fail explicitly; unresolved models/processing
  must never fabricate data or silently return success.

The [processing stages](REPORT_PROCESSING_BOUNDARIES.md) are integrated through
application services and LangGraph. Synthetic fixtures exercise real module
boundaries; they do not establish model quality or a deployed shared runtime.
Keep missing dependencies unavailable in production until explicitly configured.
