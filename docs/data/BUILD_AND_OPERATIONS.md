# Data layer build, models and operational gates

**18 October 2026 · Agent implementation handoff; documentation only today.**
Read [data layer router](DATA_LAYER.md). The user deliberately defers exact model
sources/tokenizer packages/revisions/endpoints. Do not fetch weights, provision
services or fill these gaps with guessed model URLs as part of this docs task.

## Model roles and required interfaces

| Logical role | Intended model | Input → output | Resolution still needed |
| --- | --- | --- | --- |
| `reasoning_primary` | Apertus v1.5 8B | Permitted request or bounded source passages → structured interpretation, enrichment, support assessment or grounded prose | Artifact/served ID, tokenizer/chat template, endpoint and resource limits |
| `reasoning_fallback` | Apertus v1.5 70B, optional and bounded | Difficult permitted task → same validated output contract | Availability, routing criteria, resources, quality/cost |
| `embedding` | EmbeddingGemma 2, initial candidate replacing BGE-M3 | Original document chunks or contextual queries → finite dense vectors | Source/revision, role templates, tokenizer/limits, normalization; provisional full dimension 768 |
| `reranking` | BGE-reranker-v2-m3, initial candidate | Contextual request + original passage → relevance score | Source/revision, tokenizer/pair limit, score handling and latency |

Named candidates are not measured winners. Preserve the ability to replace an
adapter while rebuilding compatible index data explicitly. Each model consumes
text through its own compatible tokenizer/processor; there is no universal
Apertus-token-ID interface across models. Chunking respects the embedding limit;
synthesis and reranking enforce their separate token budgets.

The implementation must resolve a model configuration to an immutable record:

```text
role, logical_name, model_artifact_or_served_id, revision, adapter_version,
tokenizer_processor_and_template_id, input_limit, output_limit_if_applicable,
dimension_if_embedding, pooling_normalization, query_document_templates,
precision, config_hash, provenance_license_and_verification_status
```

Unknown fields may exist in design configuration, but actual inference/index
builds fail clearly until required fields are resolved. Query/corpus vectors
share one configuration; changing model space/configuration publishes a new
build. Changing templates that affect embedding input requires affected vectors
to be rebuilt. Never assume native tool calling/JSON support from a model name;
code owns control flow and validates model output with bounded retries.
Store resolved model records in `ops.model_configurations`; embedding configs
reference that registry and add encoding-specific settings. Do not maintain
different mutable model identities in ingestion, graph nodes and tracing.

## Configuration and module boundaries

Preserve `LLM_NAME`, `LLM_BASE_URL`, `LLM_API_KEY` for the primary Apertus adapter.
Additional embedding/reranking config, database DSNs, artifact root, deployment
mode and local Langfuse endpoint/keys remain server-side configuration. Suggested
names are `DATABASE_URL`, `LANGGRAPH_DATABASE_URL`, `ARTIFACT_ROOT`,
`DOMAIN_PROFILE_PATH`, `LANGFUSE_BASE_URL`, `LANGFUSE_PUBLIC_KEY`,
`LANGFUSE_SECRET_KEY`; final naming must agree with the implemented adapters.
No credentials or real deployment endpoints belong in committed examples.

The selected [source structure](../plans/SOURCE_STRUCTURE.md) now places backend
components under `src/backend/` and the independent HTTP client under
`src/frontend/`. See local folder READMEs for ownership. This is a directory-only
scaffold; scraper behavior, backend tooling and detailed evidence/report
transformations remain undecided. Components are logical boundaries, not
mandatory separate services.
Use parameterized SQL and validated DTOs; retrieval tools accept structured
queries, not arbitrary model-generated SQL. Direct SQL repositories are sufficient;
ORM/migration tooling and exact package versions are implementation choices.

## Build order and acceptance gates

1. **Contracts/configuration:** resolve model/deployment inputs; implement DTOs,
   profile loading and SQL migrations for `navigator`; install pgvector. Bootstrap
   separate framework DBs/users and their supported migration paths. Reject
   unresolved inference configuration with useful errors.
2. **One faithful ingestion slice:** use representative HTML/public-PDF fixtures
   and then eligible live pages across the required families. Persist hashes,
   versions/spans and supported entity/claim records; verify exact reconstruction.
3. **Baseline retrieval:** create deterministic chunks, embeddings and lexical
   projections; compare lexical-only, dense-only, fused, and reranked retrieval.
   Exercise multilingual aliases, exclusions and unlabeled relevant evidence.
4. **Snapshot publication:** enforce membership/config/scope compatibility;
   validate quality/coverage and atomically switch the active profile pointer.
   Verify a failed publication leaves the previous snapshot usable.
5. **One complete case:** PostgreSQL case state + LangGraph checkpointer, pinned
   run, bounded retrieval, validated pack and reviewed editable export. Exercise
   restart, required questions, refocusing, concurrent cases and idempotent writes.
6. **Tracing:** add sanitized local Langfuse integration, custom retrieval spans
   and known evaluation results. Verify payload masking and trace outage handling.
7. **Deployment and quality evidence:** reproduce the selected target, test a
   network-disabled run if claiming air-gap, then report actual pilot metrics.

Fixtures and mock model adapters can unblock development before endpoint handoff;
they are not evidence of actual model quality or a complete prototype. Collection
and query costs are measured separately. Do not optimize HNSW before a working
exact-search baseline and known entity recall.

## Transactional publication and artifacts

Write raw/normalized/vector/export artifacts to temporary storage, hash them,
then atomically finalize local paths (or verify completed object uploads).
Commit available artifact references and validated rows in PostgreSQL. A crash
can leave unreferenced artifacts; collect them after a grace period, never by
deleting referenced bytes blindly. A cross-system distributed transaction is
not assumed. Queue export/deletion/index jobs through a transactional outbox or
equivalent durable job table with unique idempotency keys and worker leases.

Stage build membership and validation results before publication. In a short
transaction, lock/update the active profile pointer, mark the verified snapshot
published and record the publication event. A competing publisher must detect a
changed base pointer rather than overwrite another valid build silently. Existing
runs retain their snapshot. Schema/data revisions are separate from index builds.

## Refresh, recovery and deletion

- Use conditional requests/raw and body hashes. Unchanged content reuses valid
  derivations/vectors; parser changes reprocess stored bytes; taxonomy changes
  update affected assignments; model/chunker changes rebuild affected vectors.
- Keep SQL migrations versioned and test upgrades/restore against a representative
  backup. Never modify LangGraph/Langfuse internal tables through app migrations.
- Back up `navigator`, framework persistence, artifact manifests/bytes and required
  Langfuse stores consistently enough to restore linked revisions. A PostgreSQL
  dump alone does not back up local artifacts or ClickHouse/blob trace data.
- Restore one pinned case, reproduce citations and validate model/index compatibility
  before declaring recovery. Backup frequency/retention/RPO/RTO remain deployment
  choices. Encryption/access and storage limits apply to backups too.
- Revocation immediately blocks evidence/case reads, including old snapshots and
  caches; queue cleanup of dependent vectors/artifacts/checkpoints/traces/exports.
  Access deletion policy overrides historical immutability where required.

## Technical references and deferred work

Framework interfaces were checked during this session on 18 October 2026:
[pgvector and hybrid search](https://github.com/pgvector/pgvector),
[PostgreSQL text search](https://www.postgresql.org/docs/current/textsearch-controls.html),
[LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence),
[Langfuse integration](https://langfuse.com/integrations/frameworks/langchain),
[Langfuse self-hosting](https://langfuse.com/self-hosting).
Exact software compatibility, licensed model artifacts, hardware, taxonomy
contents, partner gold labels and final tracing/retention settings remain to be
resolved. Model-source selection is intentionally a later task, not a docs blocker.
