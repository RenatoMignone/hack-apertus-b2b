# Data layer architecture and build router

**18 October 2026 · Selected design; not implemented.** Authority: U6/D09 in
[decisions](../project/DECISIONS_AND_OPEN_QUESTIONS.md). PostgreSQL + pgvector
replace the earlier Weaviate/SQLite design. LangGraph orchestrates the workflow;
self-hosted Langfuse records execution. Exact model sources, tokenizer packages,
revisions, endpoints and deployment resources are deliberately deferred.

## Read by implementation task

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
[evidence policy](DATA_AND_PROVENANCE.md). U7 adds a directory-only
[source scaffold](../plans/SOURCE_STRUCTURE.md); future agents implement code
under `src/` after an implementation task authorizes it.
