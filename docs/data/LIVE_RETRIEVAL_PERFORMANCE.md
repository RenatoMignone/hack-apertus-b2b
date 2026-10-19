# Live retrieval performance acceptance — 19 October 2026

The failing capture now completes six-input SQL retrieval in **6.04–7.43 seconds**
in three final measurements, with exact dense ranking. Both original branches
previously exceeded their 30-second statement timeout, including with one input.
The complete RRF adapter returned 30 hydrated, evidence-linked hits in **6.93 s**
(another run: 9.54 s), without timeout limitations. These measurements exclude
cached query encoding and optional reranking, and do not certify a complete report.

[Machine-readable acceptance receipt and sanitized plan trees](../evaluation/retrieval-performance-20261019.json)
retain every final sample, baseline failure, membership digest and rollout state.
Raw prompts, vectors, SQL predicates, credentials and private corpus bodies are
excluded. Source code and schema changes must both be deployed for these results.

## Identity, pins and conditions

- Actual connection/session identity: `dev_ren`, ordinary runtime role, neither
  superuser nor BYPASSRLS. Principal comes from Renato's existing private binding;
  namespace `artorg_trial_20261018`. No administrator impersonation for benchmarks.
- Run `64e4d8dd-bcd5-4518-ab93-3f39c6cc95c2`, case
  `ac2a15f4-6805-458a-a6f5-76988f04393f`, owning live capture
  `9e62e820-4814-4883-baeb-207e1dcfa93e`: **144,268 chunks**.
- Identical build/configuration and real HF EmbeddingGemma 2 vectors (768d),
  cached once for SQL comparisons. One original request versus that request plus
  the first five interpretation search terms, matching the runtime query inputs.
- Shared Windows/WSL2/Docker host, PostgreSQL 17/pgvector. Ingestion continued;
  caches were not flushed. Separate diagnostic EXPLAIN reruns warmed later samples.
  Measurements are sequential, not concurrent with the disposable regression run.
- Host inspection found no blocking sessions in the inspected samples. PostgreSQL
  was initially nearly idle, then roughly one busy CPU during retrieval; ClickHouse
  also consumed CPU in a later sample. VM memory available was about 4 GiB of
  7.67 GiB. A 1.24-second diskstats sample observed five completed I/Os averaging
  about 5 ms; this small sample cannot establish general disk performance.
  Host/ingestion contention is possible, not proven absent or the primary cause.

The same private credentials used a local `127.0.0.1:5432` route on the DB host;
Renato's usual tunnel configuration remains unchanged. Apertus and web were not
called and are not implicated by these SQL failures.

## Diagnosis and implementation

Snapshot membership alone completed in about 0.17 s. Original full eligibility
timed out at 15 s before ranking. Statistics contained 31 common snapshot IDs but
not this newly captured ID. The remaining selectivity estimated **one row**, even
though the actual membership was 144,268. Fresh captures can encounter this before
automatic analysis thresholds are reached, so a one-off ANALYZE is insufficient.
Correlated embedding-ID/chunk-ID consistency joins further collapsed estimates.
Plans consequently chose repeated index/nested-loop work, including RLS checks.

Migration **0013_retrieval_scope_sets**, following 0012, adds a stable, fixed-search-
path SECURITY DEFINER set of readable scope IDs with exactly the existing
`can_access(scope,false)` principal/session-role/namespace/active/revocation checks.
SELECT policies use this set once per statement; embedding/search projections use
a hashable set of caller-visible chunk IDs. Write policies, owning-case/live-capture
checks, RLS, role flags and table grants are retained. Only the intended existing
runtime/application roles can execute the new function.

The runtime now validates capture/build/live-run pins once, materializes only the
caller-visible snapshot membership and analyzes that transaction-local relation.
It then prepares the shared authorized eligibility relation once for both branches,
retaining every acceptance, source-family, language, exclusion and embedding identity
predicate. At 1,024+ members only this staging statement discourages nested loops;
the previous setting is restored immediately (or by savepoint rollback on error).
Work memory is bounded to 32 MB per operation for the transaction. Temp relations
are dropped on commit, and reserved-name collisions fail closed.

The final eligibility EXPLAIN uses hash joins and completes in about 0.91 s despite
the remaining correlated join estimate of one row. Embedding vectors are **not**
copied into a temporary heap. An intermediate implementation did that and suffered
a 40.79-second six-input outlier under changing I/O/cache conditions; it was removed.

Lexical matching now uses a union of constant-language queries **before** staging
projections, then permits indexed per-query ranking through a temporary GIN index
over authorized matches. Search-configuration hashes, English/German/French/Italian/
simple rules, maximum rank across projections, per-query top 30, deterministic ties
and query lineage remain intact. The final small match sets legitimately use
sequential scans; index existence is not claimed as index usage. The global GIN
cannot safely push non-leakproof `@@` below RLS, and no operator is marked leakproof.
Lexical matching never prefilters dense eligibility.

Dense ranking reads validated immutable embeddings once in a materialized statement
and computes exact cosine top 30 for each input. No ANN index was deployed: HNSW/
IVFFlat filtering can change eligible recall and needs a separately measured filtered
recall evaluation. Exact search now meets this capture's latency target without
changing embedding space or relevance. More inputs still add real ranking cost.

## Before and after

Original source `bb82e1b`, schema 0012: lexical one/six inputs timed out at
30.35/30.36 s; dense one/six timed out at 30.69/30.30 s (SQLSTATE 57014).

Final source plus schema 0013, two sequential repeats:

- **One input:** shared eligibility 1.39 / 0.96 s; lexical stage/rank 1.06 / 0.95 s;
  exact dense 1.32 / 0.92 s; SQL component sum **3.77 / 2.82 s**.
- **Six inputs:** shared eligibility 0.88 / 0.91 s; lexical stage/rank 1.24 / 1.14 s;
  exact dense 3.92 / 4.26 s; SQL component sum **6.04 / 6.31 s**.
- Independent checked-in benchmark CLI replay: one input **3.86 s**; six inputs
  **7.43 s** (eligibility 1.31, lexical 1.26, dense 4.85 s).

Each branch including shared eligibility is comfortably below 30 s in these final
samples. SQL component sums exclude diagnostic reruns, digest queries, encoding,
candidate hydration, reranking and other report stages. The full adapter timing
above includes pins, fusion, hydration and lineage, with cached embeddings and no
reranker. No timeout was raised or suppressed to obtain these figures.

## Correctness and security

Independent original eligibility predicates, factored at stable scope/pin level,
produced the identical 144,268-chunk digest as prepared retrieval. The unfactored
original eligibility still timed out at 30 s even after migration: policy changes
alone do not fix the runtime plan. Final repeated lexical/dense rank-score hashes
are stable for one and six inputs; exact old/new ranks and scores are also compared
on disposable databases. This is a correctness/performance check, not a gold-label
expert relevance benchmark.

Disposable tests cover cross-owner case/capture denial, revoked scopes, spoofed
principal, exclusions, exact ranks/scores, lineage, temp cleanup/collision, large
20,004-chunk membership and join-setting restoration. Existing default-branch
savepoint/survivor tests and strict evaluation failure tests remain in force.
Actual `dev_ren` checks confirm scope sets equal the old function for every scope,
foreign-principal spoofing is denied and wrong-namespace access returns nothing.
No foreign-owner case currently exists on the live DB, so live cross-owner case
probing is unavailable; that negative case is exercised on disposable DBs.
Regression tests never target `navigator` and no broad privilege was granted.
Final regression: **303 backend tests passed** in 177.51 s on disposable
PostgreSQL/pgvector. One existing pytest-asyncio deprecation warning remains.

## Deployment and Renato restart

The shared host is already at **0013_retrieval_scope_sets**, applied on 19 October
2026 with a **3-second lock timeout**, after a verified schema-only archive. The
migration changes functions/policies only; no corpus rows, indexes or role grants
were rewritten. Role flags were identical and no inspected data count decreased;
repeating the upgrade was a no-op. There is no automatic startup migration.
The migration requires no database or ingestion restart.

After pulling the fix, stop **your API and worker** with Ctrl+C and restart both
from your repository root using the same private environment as before:

```powershell
git pull --ff-only origin main
# Terminal 1 (Windows host's Renato bundle):
.\.venv\Scripts\navigator-runtime.exe --env-file .local\runtime-access\renato\.env serve --host 127.0.0.1 --port 8000
# Terminal 2:
.\.venv\Scripts\navigator-runtime.exe --env-file .local\runtime-access\renato\.env worker
```

For Renato's separate checkout with an activated environment and private `.env`,
the equivalent commands are `navigator-runtime --env-file .env serve --host
127.0.0.1 --port 8000` and `navigator-runtime --env-file .env worker`. Keep the
existing tunnel and operator binding. Do not copy maintainer credentials.
If local uncommitted work prevents fast-forward, preserve it before integrating;
do not reset the shared ingestion/private checkout. The fix was prepared in a
separate worktree from updated main for exactly that reason.

Start a **fresh case** after restart: the failed durable run can retain terminal
stage outputs. Fresh case → Apertus/report → reviewed PDF is the remaining operator
acceptance step; this receipt proves the previously failing real database retrieval
path, not a new complete model/report run. Use the
[benchmark CLI](../../src/backend/evaluation/README.md#live-sql-performance-reproduction)
to repeat SQL measurements without creating cases or modifying the corpus.
