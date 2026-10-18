# Data layer build, models and operational gates

**18 October 2026 · Adapters and application integrated; live assets/quality/rollout pending.**
Read [data router](DATA_LAYER.md), [inference configuration](INFERENCE_CONFIGURATION.md)
and [embedding deployment](EMBEDDING_DEPLOYMENT.md). Keera endpoint/model aliases
and `google/embeddinggemma-2` are known. Authenticated synthetic Keera probes
passed; current key/quotas, immutable served revision, local model packages/assets
and representative performance still need validation.
Do not download weights/provision endpoints as part of documentation work.

## Model roles and required interfaces

| Logical role | Intended model | Input → output | Resolution still needed |
| --- | --- | --- | --- |
| `reasoning_primary` | Keera `apertus-v1-5-70b` (current explicit env) | Permitted request or bounded source passages → structured interpretation, enrichment, support assessment or grounded prose | Authenticated gateway behavior, served revision, tokenizer/chat template and resource limits |
| `reasoning_fallback` | No automatic fallback; 8B/70B are explicit configurations | Difficult permitted task → same validated output contract | Availability, routing criteria, resources, quality/cost |
| `embedding` | `google/embeddinggemma-2`, proposed local text-only | Original document chunks or contextual queries → finite dense vectors | Immutable revision/runtime and local benchmark; encoding defaults in embedding deployment; native dimension 768 |
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
Additional configuration stays server-side. `config/settings.py` owns storage/
DB settings; `config/runtime.py` owns mode, bindings, factories, model endpoint,
budgets, `RUNTIME_PROFILE_ID`, CORS and tracing. `EMBEDDING_CONFIGURATION` and
`EMBEDDING_MODEL_PATH` configure the local query encoder; optional reranking has
matching `RERANKER_*` settings. Use root [.env.example](../../.env.example) and
[config README](../../src/backend/config/README.md), not guessed variable names.
Public aliases/endpoints may be committed; real keys/credentials may not.

[Source structure](../plans/SOURCE_STRUCTURE.md) maps the integrated FastAPI,
worker, evidence/report/model adapters and independent HTTP frontend. Ingestion
has explicit collect/registry/build/publication entry points; case-time web is
optional controlled HTTP plus isolated Crawl4AI conversion and keyless
private SearXNG discovery; browser/Brave API remain explicit alternatives.
See [web provisioning](WEB_RESEARCH.md), [integration](../team/INTEGRATION.md)
and [live setup](LIVE_SETUP.md).
Components are logical boundaries, not mandatory separate services.
Use parameterized SQL and validated DTOs; retrieval tools accept structured
queries, not arbitrary model-generated SQL. Direct SQL repositories are sufficient;
SQLAlchemy Core, psycopg and Alembic are implemented; package pins are in the
backend lock file. Optional heavy model/web extras require a resolved target-platform
lock; the core lock alone does not provision those runtimes or model assets.

## Build and acceptance sequence

Core stages are implemented and fixture-tested. This sequence also includes
real corpus/provider/target acceptance work that remains to run. Do not rebuild existing modules simply because an old lane
prompt described them as future work.

1. **Contracts/configuration:** configure existing DTOs, profile and SQL migrations
   for `navigator`; install pgvector on a new host. Bootstrap
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
   run, bounded retrieval, validated pack and reviewed PDF export (editable slides later). Exercise
   restart, required questions, refocusing, concurrent cases and idempotent writes.
6. **Tracing:** verify the masked local Langfuse integration, custom retrieval spans
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

## Interpretation taxonomy prompt — 19 October 2026

Do not serialize raw database taxonomy rows into Apertus calls. The interpretation
adapter projects them into a compact vocabulary keyed by short concept codes,
with explicit label/edge column legends. Validate selected codes, then map them
back to canonical IDs in code. All concepts, aliases, ambiguities, semantic notes
and relationship directions remain; stored taxonomy/provenance is unchanged.

The current 132-concept runtime taxonomy shrank from **107,282 to 24,255 JSON
characters**, retaining 132 labels and 230 edges. Its former raw representation
exceeded the 80,000-character model-task limit before the first inference request;
that is an input-size budget error, not an expired research deadline. Keep the
input guard in place. For substantially larger vocabularies, evaluate bounded
semantic/lexical candidate retrieval or hierarchical classification separately;
never let a keyword shortlist discard the operator's original intent.

Live recheck of the failed case interpretation passed against configured Apertus
70B in 27.64 seconds, selecting four canonical concepts and requesting four
clarifications. The private probe changed no case/run records. The model-facing
activity label is a bounded word array, joined to the unchanged public string
contract; one schema repair succeeded. This verifies interpretation only, not
the subsequent retrieval, report or PDF for that case.
