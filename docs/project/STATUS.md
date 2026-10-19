# Delivery status

**19 October 2026.** This is the single summary of implementation and acceptance.
Code availability, database rollout and real research quality are distinct.

| Area | Current state |
| --- | --- |
| Product | My desk, board, cases/chat, real progress, citations, revision history and review/export; B2B branding and HelioSense mock tour integrated |
| Backend | FastAPI, separate durable LangGraph worker, typed services, authorization/idempotency, frozen packs and assessed drafts |
| Search | Independent full-text/pgvector branches, RRF, optional pinned CPU reranker, observed query/evidence lineage and bounded gap-driven follow-up |
| Providers | Explicit Apertus v1.5 70B connected setting; shared compatible HF EmbeddingGemma 2 protocol; optional private SearXNG/Crawl4AI web research |
| Data | Immutable source versions, authorized taxonomy/corpus, live case captures and published releases; ongoing ingestion determines actual coverage |
| Output | Reviewed PDF; optional manual company plans, reviewed PPTX and opt-in own-case similarity implemented behind capability/configuration gates |
| Operations | Readiness checks, safe timestamped logs, progress projection, lock/lease safeguards and root Make service launcher |
| Source schema | `0012_membership_lookup`; maintainer reports 0012 applied with restricted-role access checks and 20 disposable tests; query impact remains inconclusive and fresh live acceptance remains pending with the operator |

## Verification available

The integrated runtime baseline `88f5b75` passed **284 backend tests** against
disposable PostgreSQL/pgvector and **24 frontend tests**, TypeScript and production
build. A separately recorded live run used Keera 70B, HF encoding, local reranking,
authorized corpus, PostgreSQL checkpoints and MinIO: five partial-report cards,
26 caveats, one kept ARTORG capability and a 66,979-byte PDF. Web research was not
configured in that live acceptance. Later UI/documentation integration needs its
own recorded checks; earlier test counts are not automatically attributed to it.
See [verification](../judges/VERIFICATION.md).

## Remaining acceptance and delivery

- Confirm maintainer migration rollout and measure capture/retrieval/registration
  latency on the current host; repeat a fresh live case through review/export.
- Validate combined database/web provenance and deduplication on actual providers.
- Build reviewed expected experts/units and measure Recall@10, support quality,
  source-family coverage, reranker value and representative latency/cost.
- Verify optional exports/history on the intended deployment and controlled worker
  restart/resume with deployed checkpoints; review checkpoint credential isolation.
- Package and demonstrate the selected offline target, or explicitly qualify the
  connected demonstration. Current development proves no air-gap or Swiss residency.
- Produce final report PDF, accessible video/demo handoff and release/submission
  confirmation; use the [delivery checklist](../judges/DELIVERY.md).

No fixed source count, current provider availability or completed migration is
inferred from configuration. Readiness is a configuration/access check, not proof
of all permissions, corpus completeness or report quality.

## Latest runtime corrections

297 disposable-backend tests pass, including real SQL timeout/savepoint recovery;
the last frontend verification passed 24 tests/build. The original long
HelioSense request passed live interpretation after excluding nonliteral optional
lead annotations. Registration now bounds large source span sets before the
100-record reader, with explicit omissions; it passed that stage on live data.
Search variants share authorized branch projections, literal validation is batched,
metadata reuse is request-local, and extraction runs two independent batches at
once. No scope/support checks are waived. Shared revision 0012 was read-only verified.

Default runtime search now preserves a surviving authorized branch when the other
hits its SQL statement timeout, carrying an explicit coverage limitation into the
pack. Both timing out still fails, and explicit evaluation strategies never degrade.
This bounds the failure impact; it does not establish faster shared-host SQL.

The developer-created acceptance cases were cancelled to free the queue for manual
testing; a fresh latest-code case through report/review/PDF is not yet certified.
Restart API/worker/frontend after source updates and test a new case. UI hot-reload
invalidation during the My desk merge was observed and its mixed helper export
removed; it was separate from durable backend execution.

## Isolated pipeline reliability acceptance

The reliability pass passed **304 disposable-backend tests**, **26 frontend tests**,
TypeScript and production build. Continuous actual-Apertus 70B runs with fictional
sources, synthetic embeddings and local PostgreSQL checkpoints passed match,
clarification/resume and no-match scenarios. Match and clarification each produced
two assessed reasons and a reviewed PDF; wording revisions invalidated old downloads.
This establishes isolated orchestration/model integration, not shared-host retrieval
performance or real expertise quality. See the [receipt](PIPELINE_RELIABILITY.md).

Interpretation now uses pinned domain codes in its private schema and targeted
clarification repair. Draft assessment requires complete reason/caveat findings;
code derives its verdict. Follow-up research with identical passages/entity context
reuses assessed work with unresolved gaps; unchanged evidence after a draft failure
stops rather than regenerating repeatedly. Restart API/worker after updating.
