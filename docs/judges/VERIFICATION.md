# Verification and acceptance

**19 October 2026.** These records distinguish tested application behavior,
real-source retrieval and research quality.

| Evidence | Result | Scope |
| --- | --- | --- |
| [Combined recovery/retrieval integration](../project/FRONTEND_RECOVERY.md) | 310 backend tests, 39 transport/helper tests, 18 React interaction tests; TypeScript/build passed | Disposable PostgreSQL, authorization, workflow/recovery, evidence/review/export gates and browser behavior |
| [Actual-Apertus isolated pipeline](../project/PIPELINE_RELIABILITY.md) | Match, clarification/resume and no-match; two assessed reasons and reviewed PDF for each matching scenario | Actual 70B reasoning with fictional sources, synthetic embeddings and local PostgreSQL checkpoints; separate restart tests used scripted providers |
| [Latest isolated HTTP acceptance](../project/FRONTEND_RECOVERY.md) | Two assessed reasons, review/PDF and stale-download rejection in 63.271 s | Actual Apertus, fictional evidence; includes a wording revision |
| [Real-corpus retrieval PoC](../proof-of-concept/README.md) | Four queries, 120 passage occurrences, 52 documents; all recorded literal/hash checks passed | Original 127,902-chunk capture; inspected researcher mentions, zero accepted entity profiles |
| [Live retrieval optimization](../data/LIVE_RETRIEVAL_PERFORMANCE.md) | Six-input SQL: 6.04-7.43 s over 144,268 chunks; full RRF: 6.81 s | Actual restricted operator identity, cached real query vectors, exact dense ranking; excludes encoding/reranking; migration 0013 applied on shared host |
| Earlier real-provider case | Five partial cards, 26 caveats, one kept ARTORG capability and 66,979-byte reviewed PDF | Keera 70B, HF vectors, local reranker, authorized corpus, PostgreSQL checkpoints and MinIO; web not configured |
| Encoder protocol probe | Finite 768d vectors, local/remote token parity and identical-input parity | Configuration/protocol compatibility |

The PDF PoC is a presentation of its original receipt, not a newly measured case.
Timings above use different inputs and include different work. Use the linked
records for exact conditions, pins and reproduction.

## Run checks

After [installation](QUICKSTART.md), from repository root:

```sh
python -m pytest src/backend/tests -m "not integration" -q
python -m backend.data.schema_docs --check
(cd src/frontend && npm test && npm run build)
```

Full database tests create/drop test databases and require an explicitly disposable
`NAVIGATOR_TEST_ADMIN_DSN` with pgvector:

```sh
python -m backend.tests.run
```

Do not point tests at shared ingestion/deployment storage. Missing-DSN skips are
not passes. The quickstart distinguishes scripted fixtures from actual-Apertus
isolated acceptance; both use synthetic evidence.

## Remaining acceptance

- Run a fresh complete live-corpus case after restarting the API/worker with the
  retrieval fix; verify combined database/web provenance and output quality.
- Independently review expected experts/units and measure the challenge's 80%
  Recall@10 target, factual support, freshness and source-family coverage.
- Measure representative latency/cost, reranker value, multilingual quality and
  load; verify target-host recovery and checkpoint access isolation.
- Demonstrate the selected air-gapped deployment with packaged local services and
  egress disabled. Current development is connected.

[Current status](../project/STATUS.md) tracks rollout and delivery. Keep private
case text, provider credentials and full source bodies out of published receipts.
