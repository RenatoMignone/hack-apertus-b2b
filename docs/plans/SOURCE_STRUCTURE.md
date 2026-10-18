# Source structure and component boundaries

**18 October 2026 · Scaffold followed by authorized database implementation.**
The backend data layer now uses Python 3.12, SQLAlchemy Core, psycopg, Alembic
and Pydantic, with Docker Compose and an administrative CLI. See
[deployment](../data/DEPLOYMENT.md). HTTP framework and frontend remain undecided.
Keep the submission template: application work stays under root `src/`.

## Directory map

```text
src/
  README.md
  frontend/                 Browser client; internal layout deliberately deferred
  backend/
    api/                    HTTP transport validation, routes and response mapping
    application/            Use cases, access checks and transaction coordination
    contracts/              Future typed contracts, ports and schema exports
    workflows/              LangGraph graph composition and resumable stages
    data/
      repositories/         Canonical PostgreSQL records and transactions
      migrations/           Application schema migrations only
      retrieval/            Lexical/vector queries, fusion and ranking integration
      artifacts/            Controlled artifact storage adapters
    models/
      reasoning/            Apertus adapter
      embeddings/           Embedding adapter; exact source deferred
      reranking/            Reranker adapter
    ingestion/              Reserved acquisition/normalization integration
    evidence/               Retrieved evidence → frozen ReportEvidencePack
    reports/
      generation/           Pack → structured report revision
      validation/           Report claim/citation checks
      rendering/            Reviewed revision → downloadable artifacts
    observability/          Masked local Langfuse integration
    config/
      profiles/             Versioned domain-profile configuration
```

Every component directory has a local README or an empty `.gitkeep`. Subfolders
are ownership boundaries, not separate deployed services. Module/file names and
package conventions come with the implementation language. Do not create empty
source files or pretend these are importable packages. Frontend internals are absent.

## Communication and dependency rules

The browser communicates with the backend through versioned HTTP APIs. It never
connects directly to PostgreSQL, artifact volumes, models, LangGraph or Langfuse.
Backend capabilities can share one application initially; worker/process separation
is an implementation decision. An accepted asynchronous HTTP request does not
imply an in-memory background task is durable.

```text
frontend --HTTP--> api --> application --> workflows
                              |               |
                              +--> contracts <+--> evidence / reports
                                      ^                |
                                      +-- data / models adapters

config supplies validated settings; observability receives masked events.
```

`contracts/` will own typed payloads and narrow ports at implementation time.
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
| `ingestion` | Future acquisition/normalization integration | Publication contracts; scraper behavior/library explicitly undecided in this task |
| `evidence` | Assessment and frozen pack boundary | Retrieval/record/model ports; does not generate the final report |
| `reports` | Drafting, claim/citation checks and rendering from a pack | Model/artifact ports; cannot silently search or mutate its pack |
| `observability` | Masked traces and diagnostic correlation | Local Langfuse; no authority over facts or run completion |
| `config` | Validated server settings and versioned profiles | No secrets in repository/frontend; future bootstrap wires adapters |

Application services and workflows use repository/storage ports rather than SQL
scattered across graph nodes or report functions. `data/` owns implementations;
`contracts/` owns interfaces. Keep business checks in evidence/report components
and HTTP errors in `api/`. Framework migrations use their supported tools,
outside application SQL migrations.

## File discipline and handoff

- One file has one purpose: route group, use case, record/port, adapter, stage or
  transformation. Split responsibilities; avoid one backend/model/report file.
- Keep imports acyclic. Contracts cannot import concrete adapters. A small future
  bootstrap/composition entry point may wire services when authorized.
- Maintain the nearest README with public inputs/outputs, dependencies, unresolved
  choices and focused spec links. Central specs remain authoritative.
- Add meaningful contract/integration checks with implementation. No invented
  runnable commands or fake successful model responses in this scaffold.
- Future executable placeholders fail explicitly; unresolved models/processing
  must never fabricate data or silently return success.

First agree the [HTTP handoff](FRONTEND_BACKEND_API.md) and caller/access integration.
Then map the two [processing boundaries](REPORT_PROCESSING_BOUNDARIES.md), choose
backend/tooling/adapters and implement a vertical slice using the
[data-layer build gates](../data/BUILD_AND_OPERATIONS.md). Existing high-level plans
are not a completed stage-by-stage processing design. No dependency installation
or scraper selection is part of this scaffold.
