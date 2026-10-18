# Technical choices and implementation handoff

**18 October 2026 · Initial architecture to validate; not implemented.**
The main reference is [the visual pipeline](../architecture.html), backed by
[ARCHITECTURE.md](ARCHITECTURE.md). These choices are user-selected starting
points, not measured superiority or verified hosting capabilities.

## Component choices

| Responsibility | Initial choice | Validation still needed |
| --- | --- | --- |
| Interpretation, extraction, reasoning, writing | Apertus v1.5 8B; bounded optional 70B fallback | Actual served model/protocol, structured output handling, resources, quality/cost and licensing |
| Original-text embeddings | BGE-M3 dense vectors | Pin revision/tokenizer/settings, query/corpus compatibility and domain/language retrieval |
| Lexical + vector retrieval | Weaviate BM25F + supplied vectors | Schema/mapping, access/snapshot filters, batch failures and offline packaging; no hosted default vectorizer |
| Passage reranking | BGE-reranker-v2-m3 | Pair-token budget, ranking quality and latency; scores are not calibrated probabilities |
| Workflow and resumable dialogue | LangGraph | Revision/checkpoint isolation, cancellation, bounded retries and no required external tracing |
| Raw/evidence/claim storage | Versioned artifact store; SQLite may hold job/provenance/case state | Reference integrity, atomic publication pointer and access-aware retention |
| Interface/export | Framework/library not selected; supplied editable PowerPoint template | Rendered report/slide QA, editability, citations, local assets and licensing |

Detailed records, payloads, indexing and initial budgets live in
[INGESTION_PLAN.md](INGESTION_PLAN.md#7-shared-contract-v1--owned-here-consumed-by-phase-2).
Case intake/research/revisions/export live in [OPERATIONS_PLAN.md](OPERATIONS_PLAN.md).
Avoid a second schema, taxonomy or search API.

## Retrieval approach and alternatives

Use a prefetched, dated evidence snapshot as the reproducible baseline. Connected
mode can add bounded company research/refresh. Live-only navigation cannot
substantiate an air-gapped runtime. Compare selected hybrid retrieval with a
simple lexical baseline on independently checked terminology variants.

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

## Implementation order once authorized

1. Obtain promised endpoint/hardware details; review profile/taxonomy and gold examples.
2. Build shared evidence contracts and faithful collection across the three families.
3. Publish a validated snapshot and one complete case with honest unknown/no-match behavior.
4. Add questions/revisions and reviewed export; evaluate support, Recall@10 and cost.
5. Test second-profile fixtures/rebuilds and actual disconnected cold start.

Record results and choices in [decisions](../project/DECISIONS_AND_OPEN_QUESTIONS.md).
No application implementation is authorized by this documentation update.
