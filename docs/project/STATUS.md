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
| Source schema | `0013_retrieval_scope_sets`, applied on shared host; real `dev_ren` six-input SQL retrieval 6.04–7.43 s over 144,268 chunks; 310 backend tests passed on disposable PostgreSQL; operator API/worker restart and fresh full-report acceptance remain |

## Verification available

19 October retrieval fix: both original branches reproduced 30-second timeouts
under Renato's actual restricted identity. Shared eligibility and read-policy work
now complete with identical authorized membership and exact dense ranking. The
complete RRF adapter returned 30 hits in 6.81 s using cached real embeddings, without
reranking. See the [measured receipt, plans and restart commands](../data/LIVE_RETRIEVAL_PERFORMANCE.md).

Combined recovery/retrieval integration passed **310 backend tests**, **39 frontend
transport/helper tests** and **18 React interaction tests**, TypeScript and build.
Actual-Apertus isolated cases passed match, clarification/resume and no-match,
with assessed drafts, review/PDF and stale-download rejection. Browser fault
injection verified connection, authentication, revision and export recovery.
See [pipeline](PIPELINE_RELIABILITY.md) and [recovery](FRONTEND_RECOVERY.md) receipts.

A separate earlier live-corpus case produced five partial cards, 26 caveats, one
kept ARTORG capability and a reviewed PDF using Keera, HF, local reranking,
PostgreSQL checkpoints and MinIO; web was not configured. The
[retrieval PoC](../proof-of-concept/README.md) preserves the earlier real-source
experiment and its revised standalone PDF. [Verification](../judges/VERIFICATION.md)
separates the scope and conditions of each result.

## Remaining acceptance and delivery

- Pull and restart each operator's API/worker for the measured retrieval fix;
  repeat a fresh live case through review/export. Shared migration 0013 is applied;
  broader capture/registration latency and report/provider acceptance remain separate.
- Validate combined database/web provenance and deduplication on actual providers.
- Build reviewed expected experts/units and measure Recall@10, support quality,
  source-family coverage, reranker value and representative latency/cost.
- Verify optional exports/history on the intended deployment and controlled worker
  restart/resume with deployed checkpoints; review checkpoint credential isolation.
- Package and demonstrate the selected offline target, or explicitly qualify the
  connected demonstration. Current development proves no air-gap or Swiss residency.
- Produce final report PDF, accessible video/demo handoff and release/submission
  confirmation; use the [delivery checklist](../judges/DELIVERY.md).

## Runtime behavior

Interpretation uses pinned domain codes and bounded clarification repair. Draft
assessment covers every reason and caveat before code derives acceptance.
Unchanged follow-up evidence reuses prepared work; unchanged evidence after a
failed draft stops repeated generation. Wording edits retain evidence; focus
changes research again.

Default search preserves a surviving branch with an explicit limitation if the
other branch times out. Both branches timing out fails; evaluation strategies
never silently degrade. Shared SQL optimization and rollout are measured in the
linked performance receipt.

Frontend reconnect observes existing work, stale revisions reload without replaying
writes, and export retries reuse an accepted operation within the session. Safe
request IDs support diagnosis. Restart API/worker after pulling runtime updates.
