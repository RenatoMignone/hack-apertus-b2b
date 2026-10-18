# Data layer architecture and build router

**18 October 2026 · Data-layer implementation added; model/product integration pending.** Authority: U6/D09 in
[decisions](../project/DECISIONS_AND_OPEN_QUESTIONS.md). PostgreSQL + pgvector
replace the earlier Weaviate/SQLite design. LangGraph orchestrates the workflow;
self-hosted Langfuse records execution. U9 supplies Keera endpoint/model aliases
and the EmbeddingGemma 2 artifact reference. Authenticated behavior, immutable
revisions, runtime packages and hardware benchmarks remain open.

## Final schema entry point

[Final schema contract v1](RELATIONAL_SCHEMA.md), [exact field inventory](SCHEMA_REFERENCE.md)
and [ingestion/retrieval handoff](INGESTION_RETRIEVAL_HANDOFF.md) are authoritative
for new queries at migration `0005_finalize_schema`. Seven unused/duplicate tables
and two redundant chunk fields are retired; populated history stays owner-only,
outside the application schema. Model choices remain configuration, not new tables.

## Read by implementation task

Start runnable setup and team onboarding at [deployment](DEPLOYMENT.md).
Source implementation lives under `src/backend/data/`, with typed contracts,
Alembic migrations, artifact adapters, hybrid retrieval and case repositories.
The specs below remain the intended behavior; measured checks and unresolved
integration gates are recorded in the deployment guide.

| Task | Owning specification |
| --- | --- |
| Tables, keys, evidence and taxonomy persistence | [Relational schema](RELATIONAL_SCHEMA.md) |
| Embeddings, lexical/vector fusion and entity ranking | [Retrieval](RETRIEVAL_SPEC.md) |
| Case history, graph checkpoints, review and exports | [Case state and lineage](CASE_STATE_AND_LINEAGE.md) |
| Langfuse integration, traces and evaluation events | [Observability](OBSERVABILITY.md) |
| Model contracts, migrations, publication, recovery and build order | [Build and operations](BUILD_AND_OPERATIONS.md) |

[Phase 1](../plans/INGESTION_PLAN.md#7-shared-contract-v1--owned-here-consumed-by-phase-2)
continues to own logical payloads/read interfaces. These files own their physical
storage, search and operational implementation. Do not create a second evidence
schema or a backend-specific contract for the case workflow.

## Components and ownership

| Component | Responsibility | Authority |
| --- | --- | --- |
| Artifact storage | Immutable raw HTML/public PDFs, normalized bodies/sidecars, manifests and rendered exports | Original bytes and source-located text |
| PostgreSQL `navigator` | Canonical records, claims, taxonomy, chunks/vectors, snapshots, case revisions and jobs | Durable application state and provenance |
| PostgreSQL `langgraph` | Framework-managed checkpoint tables, accessed through its saver | Resumable graph execution; not the public corpus |
| PostgreSQL `langfuse` | Framework-managed transactional tables | Langfuse configuration, not application evidence |
| Langfuse auxiliary services | ClickHouse, Redis/Valkey, S3-compatible blob storage, web and worker | Traces, observations and scores; not factual authority |
| Versioned domain profile | Sources, taxonomy, languages, relevance/access rules and ranking settings | Reviewed configuration pinned by each run |

One PostgreSQL instance with separate databases/users is the initial topology;
separate instances remain possible without changing domain contracts. Application
schemas are `corpus`, `taxonomy`, `retrieval`, `cases` and `ops`. Use SQL foreign
keys within `navigator`; framework databases are linked by IDs through APIs,
never direct writes or cross-database joins into their internal tables.

Artifact storage starts as a controlled local volume, with an adapter for
S3-compatible storage. Langfuse needs its own compatible blob service even when
application artifacts use a local volume. Separate buckets/prefixes and roles.
Database names/schema names are implementation defaults, not existing services.

## End-to-end data flow

```text
Connected collection → raw artifact → faithful normalized document version
    ├→ exact evidence → supported entities/claims + optional concept assignments
    └→ original chunks → embedding worker → pgvector + full-text search records
        → validated immutable snapshot → active profile pointer

Permitted message → case/input revision + pinned snapshot → LangGraph workflow
    → Apertus interpretation + contextual query plan
    → lexical search AND vector search → rank fusion → BGE reranking
    → claim/constraint checks + bounded follow-up retrieval
    → immutable evidence pack → report revision → human review → export

Graph/model/retrieval stages → sanitized Langfuse observations
```

Keyword matching does not exclude semantic candidates. Inferred topic labels
are hints, not mandatory gates. An embedding model is necessary for vector
retrieval; a tokenizer alone cannot generate semantic search vectors. Reranking
does not replace evidence validation. Keep the full request and exclusions
through every handoff, including when producing multiple search queries.

## Invariants

1. Original evidence, model derivations and human statements remain distinct.
2. Documents, source spans, embedding builds, snapshots, case inputs and results
   are versioned; one run never silently switches to a newer snapshot/model.
3. Public evidence and case-scoped material have explicit visibility. Both
   retrieval branches apply authorization before exposing candidates.
4. A case correction cannot mutate a published corpus, taxonomy or prior result.
5. Generated reports/traces are never their own factual corroboration.
6. Connected acquisition is separate from the proposed air-gapped runtime.
   All model, database, tracing, UI and export dependencies must be local there.

Medical pilot, three institutional families, public-only input and independent
deployment constraints remain in [architecture](../plans/ARCHITECTURE.md) and
[evidence policy](DATA_AND_PROVENANCE.md). The original U7 scaffold now contains
implemented Python data modules and the separately owned React frontend. Use
[module handoffs](../plans/MODULE_HANDOFFS.md) for scoped backend feature work.

## U8 implementation boundary

The agreed [case pipeline](../plans/REPORT_PROCESSING_BOUNDARIES.md) defines interpretation, parallel DB/web research,
supported frozen packs, reason-card review and PDF-first export. This change
implements contracts and persistence only; frontend remains on mocks. Live models,
search/scraping, HTTP, LangGraph execution and rendering are future integrations.

## Feature handoff and provider settings

Use [module handoffs](../plans/MODULE_HANDOFFS.md) for independently scoped work,
[inference configuration](INFERENCE_CONFIGURATION.md) for Keera and
[embedding deployment](EMBEDDING_DEPLOYMENT.md) for local/hosted comparison.
[Active questions](../project/OPEN_QUESTIONS.md) supersede historical unknown lists.
