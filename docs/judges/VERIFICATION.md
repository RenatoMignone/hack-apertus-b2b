# Verification and acceptance

**19 October 2026.** Counts below are dated receipts with defined scope, not a
claim that every live feature/provider has passed on the final deployment.

| Evidence | Result | What it establishes |
| --- | --- | --- |
| Integrated runtime `88f5b75`, disposable PostgreSQL/pgvector | 284 backend tests passed | Schema/RLS, actual module composition, queue/recovery contracts, evidence/review/export gates and regressions |
| Same baseline frontend | 24 tests, typecheck and production build passed | HTTP interaction and UI/export policy; not model quality |
| Recorded real-provider case | Five partial cards, 26 caveats; one kept ARTORG capability; 66,979-byte reviewed PDF | Narrow live path using Keera 70B, HF vectors, local reranker, authorized corpus, PostgreSQL checkpoints and MinIO; web was not configured |
| Encoder protocol probe | Finite 768d vectors, local/remote token parity and identical-input parity | Configuration/protocol compatibility, not semantic relevance |
| Synthetic capture fixture | 120,004 chunks in 7.206 s; prior query >30 s | Controlled capture regression; synthetic 3d vectors, not production SLA |
| Optional output fixtures | Reviewed PDF/PPTX, stale-review checks and own-case eligibility | Isolated implementation behavior; not deployment activation |

The latest My desk merge additionally passes 24 frontend tests and production
build. The documentation refresh does not rerun real-provider cases or shared
migrations. [Performance](../data/CAPTURE_PERFORMANCE.md) separates measured phase
cost from pending host rollout. Source head 0012 does not prove host revision.

## Reproduce checks

After [installation](QUICKSTART.md), from root:

```bash
.venv/bin/python -m pytest src/backend/tests -m "not integration" -q
.venv/bin/python -m backend.data.schema_docs --check
(cd src/frontend && npm test && npm run build)
```

Full database tests require an explicitly disposable `NAVIGATOR_TEST_ADMIN_DSN`
with pgvector and required test-role setup; they create/drop test databases:

```bash
.venv/bin/python -m backend.tests.run
```

Never use shared ingestion/deployment infrastructure. Ordinary pytest without a
test DSN skips DB checks; skips are not passes. The [synthetic harness](QUICKSTART.md)
uses actual application code with explicit fixture providers and memory checkpoints;
it does not establish deployed saver recovery.

## Research quality and deployment

The challenge's **80% of expected experts/units in the top 10** remains an unmeasured
target. Candidate queries have no gold labels. Independently review expected typed
entities and actual passages before computing intent-balanced Recall@10; compare
lexical/dense/RRF/reranked variants under identical pins.
[Evaluation](../challenge/EVALUATION.md) defines support, completeness, ambiguity,
negative cases, fairness/coverage and latency checks separately.

Combined real DB/web provenance, broader person/facility coverage, controlled
latency/cost, multilingual quality, load, target-host restart/resume and independent
offline deployment remain acceptance work. A source quotation and a model verdict
cannot guarantee every implication; human review remains necessary.

For release record commit/platform, corpus/profile/taxonomy/encoder/reranker/task
pins, enabled flags, passed/failed/skipped checks, actual output and limitations.
Keep case content, provider secrets and copyrighted source artifacts private.
