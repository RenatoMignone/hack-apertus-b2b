# Live capture and retrieval performance

19 October 2026. Source revision `0011_capture_performance`; the shared host was
last measured at `0010_rich_outputs`. Apply the maintainer migration before
claiming the capture speedup on that host. Frontend and ingestion source data are
unchanged. [Maintainer handoff](../team/CAPTURE_PERFORMANCE_HANDOFF.md).

## Observed bottleneck

Case creation waits for `ops.capture_live_corpus` before creating a queued run.
Two own `dev_ren` requests were observed running for several minutes without lock
blockers; one showed temporary-file I/O. They were cancelled explicitly under the
same login, rolling back their uncommitted cases/captures. No ingestion or other
user's query was cancelled.

An isolated nested execution plan reproduced the issue: a ready-membership CTE
estimated one row but produced 20,004. The newest-version DISTINCT/sort subplan
ran 20,004 times, with about four million rejected join pairs. Most elapsed time
was eligibility selection, not snapshot insertion, SSH or model inference.
The initial typed-row rewrite alone did not improve the benchmark; the final
window-selection change removes that repeated-sort plan.

## Changes

- `live_capture_fast.sql`: authorize public scopes and check source/artifact
  eligibility before processing their chunks; retain exact text, compatible
  vector, lexical projection and evidence checks. Choose the newest **ready**
  version with one `dense_rank` window instead of the self-join. Retain latest
  eligible embedding selection and every eligible chunk, not a top-N cutoff.
- Use typed, indexed transaction-local membership instead of repeatedly parsing a
  huge JSON intermediate. Preserve the manifest fields, immutable memberships,
  supported claims/entities, grants, revocation checks and own-case boundaries.
  Temporary tables are dropped on success/transaction completion; an existing
  caller-created table with the reserved name fails closed. No persistent new
  application tables or shared readiness cache are introduced.
- `snapshot_projection.py`: authorization/context reads return small metadata
  plus the server-extracted owning-case ID, not entire per-chunk manifests.
- Hybrid retrieval reads ranked passage metadata and citation IDs in two bounded
  queries instead of per-hit round trips. Recheck distinct selected scopes after
  reranking; rank/fusion/overlap rules and exact cosine search are unchanged.
- An optional `embed_queries` capability batches query variants. Local/HF adapters
  keep identical query templates, input-token checks and vector validation; other
  embedders retain the serial port fallback. Up to six variants fit one bounded
  HF request instead of six individual requests. No hidden model fallback/cache.
- `RUNTIME_CAPTURE_TIMEOUT_SECONDS=30` bounds corpus preparation separately from
  the worker's research deadline. A stricter caller timeout wins. Successful calls
  restore the previous setting; failure rolls back the whole command and local
  setting. Capture timeout/completion logs contain elapsed time, not prompts,
  credentials or source text. Slow preparation returns unavailable, not an empty
  or silently truncated corpus.

## Measurements and limits

All old/new comparisons below used **isolated PostgreSQL 17/pgvector**, synthetic
public text and 3-dimensional fixture vectors, not the shared corpus or 768d
production vectors. Case/capture changes were rolled back between measurements.

| Fixture | Original | Optimized | Verification |
| --- | --- | --- | --- |
| 20,004 chunks, diagnostic profiling enabled | About 18 s | 1.025 s | Identical chunk/embedding membership hash; newest-version sort runs once |
| 120,004 chunks, profiling disabled | Exceeded the 30 s limit | 7.206 s | All 120,004 eligible chunks captured; old full-size equality not measured because it timed out |

These are single-run engineering measurements, not production latency guarantees,
quality scores or a hardware benchmark. The full regression suite passed **273
tests**; one existing pytest loop-policy deprecation warning remains. Coverage
includes unchanged old/new membership with accepted claims, newer incomplete
versions, stable previous captures, foreign-user denial, temp-name collision,
statement-timeout rollback/restoration, identical batched/serial ranking and real
reviewed PDF/PPTX flows using synthetic providers. No frontend code changed.

Reproduce on an explicitly isolated local disposable test cluster, never the shared
SSH tunnel or deployment credentials:

```bash
NAVIGATOR_TEST_ADMIN_DSN='<disposable-local-admin-DSN>' \
  .venv/bin/python -m backend.tests.runtime.benchmark_capture --documents 1200
```

`--profile` additionally requires `pg_stat_statements` preloaded with nested
tracking (`pg_stat_statements.track=all`) in that isolated server; it loads
`auto_explain` in the benchmark connection and saves synthetic plans under ignored
`.local/capture-performance/`. It never loads deployment `.env`. The tool creates
and removes only its uniquely named synthetic benchmark database. It refuses the
standard shared-tunnel port and non-loopback addresses.

An independent live HF batch probe also passed: two permitted synthetic queries
returned two valid 768d vectors in 1.184 seconds through the configured adapter.
No real case or corpus was modified by that probe.

Remaining acceptance: Eric applies 0011, then measure real case-creation latency
with ingestion active, run actual DB/web/Keera extraction through review/export,
and inspect plan/scaling on production dimensions and hardware. Inference latency,
source fetch failures and relevance still require independent measurement.
