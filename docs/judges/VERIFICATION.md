# Verification, evidence and limitations

**Snapshot: 19 October 2026; source baseline `072f099`.**
The records below are existing engineering receipts, not tests rerun by writing
these docs. Working-tree ingestion/runtime changes are not automatically part
of this source baseline. Final release checks must identify their exact commit.

## Recorded evidence

- **Integrated application:** the [integration handoff](../team/INTEGRATION.md)
  records restricted-role API, real backend modules, synthetic providers, review
  gates, browser flows and actual PDF generation. Counts in older sections refer
  to earlier commits.
- **Optional features:** [completion roadmap](../team/COMPLETION_ROADMAP.md) and
  [rich-output verification](../data/RICH_OUTPUTS.md) record isolated tests and
  browser/PPTX checks. The [status page](../project/STATUS.md) records 267 backend
  and 20 frontend tests/build at that checkpoint. These do not prove live feature
  activation or quality.
- **Performance baseline:** [capture specification](../data/CAPTURE_PERFORMANCE.md)
  records 273 regression tests with disposable PostgreSQL and synthetic providers,
  and a single 120,004-chunk fixture capture in 7.206 seconds; the old query
  exceeded 30 seconds. That measurement used 3-dimensional synthetic vectors and
  is not a production latency guarantee. Later host receipts in the same file,
  where present, have their own scope and rollout status.
- **Actual providers:** the [live acceptance receipt](../team/BACKEND_RESEARCH_COMPLETION.md#completed-live-acceptance--19-october-2026)
  records Keera 70B, HF embeddings, local reranker, authorized live corpus,
  PostgreSQL checkpoints and MinIO. It produced five partial-report cards and 26
  caveats. All cards were reviewed; one ARTORG capability was kept and downloaded
  as a 66,979-byte PDF. No web service was configured for that run. Earlier context
  failures and unsupported wording were blocked before the successful retry.
- **Encoder protocol:** [HF verification](../data/HOSTED_EMBEDDINGS.md) records
  finite 768d vectors, pinned tokenizer and query/document protocol checks.
  This verifies compatibility, not retrieval relevance.
- **Deployment:** [migration status](../team/MIGRATION_STATUS.md) and
  [runtime checklist](../team/RUNTIME_CHECKLIST.md) are dated host records.
  Schema activation, process restart and completed live acceptance are distinct.
  Neither a configured flag nor a reachable capability endpoint proves every
  provider, permission and optional output works.

## What is not established

The challenge's **at least 80% of expected experts/units in the top 10** is a
target, not a result. No independently judged Recall@10 or semantic-support
percentage is reported. Candidate evaluation queries are not gold labels.
Synthetic fixtures cannot establish model accuracy, multilingual quality,
fair discoverability or named-expert coverage.

Combined real database/web provenance and deduplication acceptance, broader
source coverage, resource/cost measurements and controlled target-host
restart/resume remain open. A live partial PDF is not evidence of air-gapped
operation or Swiss sovereignty. Exact quotations plus model assessment reduce
risk but cannot guarantee that every implication is supported or a source is
trustworthy.

## Reproduce engineering checks

After the [backend installation](QUICKSTART.md#2-local-synthetic-api-and-worker),
run from root with the virtualenv active:

```text
python -m pytest src/backend/tests -m "not integration" -q
```

For full tests, explicitly set `NAVIGATOR_TEST_ADMIN_DSN` to a disposable local
PostgreSQL/pgvector cluster and run:

```text
python -m backend.tests.run
```

That command requires the explicit DSN; it does not derive admin credentials
from deployment config. Tests create/drop databases and require
`navigator_app NOLOGIN`. Never point them at the shared host. Without a test DSN,
ordinary pytest skips database tests; skipped tests are not passes.

In `src/frontend`:

```text
npm ci
npm test
npm run build
```

The [quickstart's synthetic harness](QUICKSTART.md#2-local-synthetic-api-and-worker)
exercises API/worker and export with fixture models. It does not use durable
PostgreSQL checkpoints. Real recovery acceptance must use the deployed worker
and saver.

## Evaluate research quality separately

Use the [evaluation protocol](../challenge/EVALUATION.md) and
[candidate queries](../evaluation/PILOT_QUERIES.json). Independently review
expected experts/units before calculating intent-balanced Recall@10. Compare
lexical, dense, fused and reranked results on the same pins. Audit each public
assertion against its actual passage, and measure missing fields, direct/adjacent
fit, source coverage and latency separately. Do not treat rank, valid JSON or
editorial keep decisions as factual gold labels.

A release receipt should record commit, platform, model/tokenizer/configuration
pins, corpus capture or release, query/label version, enabled features, passed/
failed/skipped checks, observed failures and the reviewed export outcome.
Private cases, credentials and copyrighted source artifacts stay out of that
public receipt.
