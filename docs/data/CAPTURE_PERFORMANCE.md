# Capture and retrieval performance

## Implemented safeguards

- Migration **0011** replaces the quadratic newest-version live-capture sort with
  a bounded compatible projection. Authorization/source/artifact readiness remain.
- Migration **0012** changes four membership RLS policies to use an uncorrelated
  eligible-snapshot lookup; table structure and grants are unchanged.
- Snapshot authorization reads use small metadata projections instead of full
  membership manifests. Lexical SQL uses constant language-specific query objects.
- Case summaries are batched projections. Corpus duplicate detection reads documents
  and aliases in one join rather than issuing one alias query per document.
- Pure reads/lease renewal avoid long case-write locks. Runtime connections cap
  lock waits at five seconds and idle-in-transaction at sixty, retaining stricter
  settings. Write authorization and worker identity checks remain active.
- `RUNTIME_CAPTURE_TIMEOUT_SECONDS` defaults to 30 (range 1–120), independently
  bounding preparation. Retrieval SQL is bounded and preserves stricter timeouts.

## Recorded measurements

| Environment / phase | Observation | Scope |
| --- | --- | --- |
| Disposable 120,004-chunk fixture | New capture 7.206 s; prior query exceeded 30 s | Synthetic 3d vectors, not production latency |
| Disposable 20,004-chunk fixture | 30-hit retrieval 1.871 s | Synthetic controlled dataset |
| Connected run before rollout | Capture 28.546 s; six sequential lexical/dense query pairs 120.296 s | Single observed slow run, not hardware diagnosis |
| Same run | Six batched query embeddings 1.368 s; 10 page attempts 14.683 s | Actual phase logs; some fetches failed |
| Same run | Source registration cancelled after 192.488 s | Incomplete operation, not successful latency |
| Read-only optimized corpus duplicate lookup | 2.857 s, no duplicate found | One probe; not end-to-end acceptance |
| Read-only batched list | Eight case summaries 0.854 s | One probe; cache/load unspecified |

Suspended local processes were also observed holding case locks; terminating the
owned obsolete processes released those locks. This is distinct from corpus size,
query cost and provider latency. Baseline runtime tests are in
[verification](../judges/VERIFICATION.md).

## Maintainer rollout and measurement

Source head is `0012_membership_lookup`; verify the host revision rather than
assuming source availability means deployment. With approved maintenance access,
back up and apply forward migrations using the [deployment runbook](DEPLOYMENT.md).
Do not run shared-host destructive tests, disable RLS or relabel vectors.

Compare restricted-identity plans before/after: lexical, dense and membership
checks; inspect estimates, filters, loops, buffers, spills, locks and candidate
counts. Use bounded `EXPLAIN (ANALYZE, BUFFERS)` only on approved read queries.
Record user role/profile/capture, corpus size, hardware/load, cache and model pins.
Use evidence-based index/statistics changes; coordinate any new migration number.

Measure preparation, encoding, lexical/dense, reranking, expansion, registration,
model tasks and finalization separately, then repeat a fresh case → review → PDF.
A faster fixture or higher timeout does not establish acceptable live performance.
Use the existing performance tests under `src/backend/tests/` with an explicitly
disposable test DSN; never supply the shared deployment DSN to fixture benchmarks.

Query variants now share a materialized authorized projection per branch while
retaining each query's top-30 ranks. One read-only existing-capture probe returned
30 hits in 49.451 seconds versus an earlier logged 114.490-second search; cache
and load differ, so this is not a causal speedup measurement. A fresh live run
hit the 30-second lexical bound once and succeeded on its bounded retry. Runtime
literal validation also batches record/body/membership reads while checking every
record and scope, avoiding hundreds of network round trips.

Evidence reads reuse fetch/mirror metadata only within one authorized call and
batch snapshot membership/scope checks; every returned literal and version hash
is still checked. A read-only 96-record historical-capture projection completed
in 10.198 seconds. This is one probe, not an end-to-end latency guarantee.
