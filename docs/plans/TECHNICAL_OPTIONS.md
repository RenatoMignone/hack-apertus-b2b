# Technical choices and implementation handoff

**18 October 2026 · Core choices implemented; model assets and live quality remain to validate.**
The main reference is [the visual pipeline](../architecture.html), backed by
[ARCHITECTURE.md](ARCHITECTURE.md). These choices are user-selected starting
points, not measured superiority or verified hosting capabilities.

## Component choices

| Responsibility | Initial choice | Validation still needed |
| --- | --- | --- |
| Interpretation, extraction, reasoning, writing | Apertus v1.5 8B; bounded optional 70B fallback | Keera alias/base supplied; verify authenticated schema/tool behavior, served revision, quality/cost |
| Original-text embeddings | `google/embeddinggemma-2`, proposed text-only local, native 768d | Reference verified; pin revision/runtime/encoding before ingestion and evaluate pilot retrieval |
| Lexical + vector retrieval | PostgreSQL full-text search + pgvector cosine, fused with RRF | Full-text ranking is not BM25; validate language configs, access/snapshot filters and exact baseline before optional HNSW |
| Passage reranking | BGE-reranker-v2-m3 | Pair-token budget, ranking quality and latency; scores are not calibrated probabilities |
| Workflow and resumable dialogue | LangGraph with PostgreSQL checkpointer in separate database | Revision/thread isolation, idempotent recovery across application/checkpoint commits and bounded retries |
| Raw/evidence/claim storage | Artifact volume + PostgreSQL canonical records/jobs/cases | Reference integrity, atomic publication pointer, access-aware retention and restore |
| Tracking/evaluation observations | Self-hosted Langfuse | Local web/worker, PostgreSQL, ClickHouse, Redis/Valkey and S3-compatible storage; masked payloads and non-blocking failure |
| Interface/export | React/Vite HTTP client, FastAPI and ReportLab PDF; editable PowerPoint later | Synthetic browser-to-PDF and layout checks passed; partner acceptance and larger real reports pending |

Detailed records, payloads, indexing and initial budgets live in
[INGESTION_PLAN.md](INGESTION_PLAN.md#7-shared-contract-v1--owned-here-consumed-by-phase-2).
Case intake/research/revisions/export live in [OPERATIONS_PLAN.md](OPERATIONS_PLAN.md).
Physical ownership is in the [data-layer router](../data/DATA_LAYER.md), with
focused schema/retrieval/case/tracing/build specs. Avoid a second schema, taxonomy
or search API. U6/D09 supersedes Weaviate, SQLite and BGE-M3 as active defaults;
Keera served aliases/base URL and the EmbeddingGemma 2 artifact reference are now
known; immutable revisions, tokenizers/runtimes and limits still need validation.

## Retrieval approach and alternatives

Use a prefetched, dated evidence snapshot as the reproducible baseline. Connected
mode can add bounded company research/refresh. Live-only navigation cannot
substantiate an air-gapped runtime. Compare selected hybrid retrieval with a
simple lexical baseline on independently checked terminology variants.

Run lexical and vector branches independently over eligible evidence, fuse ranks,
then rerank. Keep inferred topic labels optional and validate factual support
after retrieval. A larger model or a high relevance score cannot establish truth.

A graph database, fine-tuning and autonomous browsing are not requirements.
Evidence-linked claims can use simple records. Keep core contracts independent
of sector and backend; new domains supply profiles and may rebuild indexes under
the architecture's [rebuild rules](ARCHITECTURE.md#rag-rebuild-rules).

## Deployment and dependencies

[ARCHITECTURE.md](ARCHITECTURE.md#target-architecture-mandatory) owns the proposed
primary air-gapped target, independent on-premise/Swiss-cloud alternatives,
component locations, build/collection/runtime inventory and proof required.
No target is yet demonstrated. Preserve `LLM_NAME`, `LLM_BASE_URL`, `LLM_API_KEY`;
do not infer credentials, endpoint compatibility, quotas or modality support.
All development/deployment stays outside cantonal ICT/internal networks.

## Next validation order

1. Confirm shared-host revision; back up and migrate to current head with its owner.
2. Verify matching embedding assets/configuration; publish a reviewed pilot snapshot.
3. Configure runtime identities/checkpoints/storage and complete one live public case.
4. Measure support, intent-balanced Recall@10, latency/cost and failure behavior.
5. Verify second-profile behavior and an actual disconnected cold start before claims.

The [live setup runbook](../data/LIVE_SETUP.md) owns commands and prerequisites;
[active questions](../project/OPEN_QUESTIONS.md) owns the remaining backlog.

## U8 selected runtime processing

Use bounded LangGraph stages and LangChain adapters for all agentic execution.
Primary Apertus 8B handles interpretation, batched extraction/assessment and draft
synthesis; optional 70B fallback has identical checks. Large context length does
not demonstrate one-call pack reliability. Exact model artifacts remain deferred.
Controlled HTTP acquisition plus Crawl4AI conversion is implemented;
[comparison and primary sources](../data/WEB_RESEARCH.md). PDF first, PPTX later.
Graph, services, semantic assessment and rendering are integrated; real model
quality and deployment are separate acceptance gates.

U9: [Keera settings](../data/INFERENCE_CONFIGURATION.md) own provider details;
[embedding deployment](../data/EMBEDDING_DEPLOYMENT.md) compares local, HF Providers,
dedicated endpoints and Spaces. Local text-only is recommended, not benchmarked.
The team-reported $10/user credit cannot be assumed eligible for all HF services.
