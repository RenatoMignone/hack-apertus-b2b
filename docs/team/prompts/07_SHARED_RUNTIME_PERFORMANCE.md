# Eric: shared database performance and migration 0012

Read `AGENTS.md`, `docs/team/RUNTIME_FEEDBACK_AND_SEARCH.md`,
`docs/data/CAPTURE_PERFORMANCE.md`, `docs/data/LIVE_CORPUS_RUNTIME.md` and the
current migration code. Preserve your ingestion work, private configuration,
source identities, vectors, grants, RLS, artifacts and monitoring.

## Ownership and delivery

Your scope is shared-host database rollout and measured database performance.
Renato owns current API/worker/lease, source-registration, model-adapter and
frontend integration changes. Do not independently rewrite those files or the
frontend. Coordinate any needed new migration number with Renato before writing it.

**Renato's changes are currently local, not pushed.** Fetching main alone does
not supply migration 0012. Obtain the exact reviewed migration file or the
migration-only `.local/runtime-handoff/0012_membership_lookup.patch` from Renato
through the team's existing transfer channel. Preserve local changes and apply
with `git apply --check` before `git apply` on an appropriate checkout. If 0012
already exists with different contents, stop and reconcile the collision; never
overwrite or stamp a revision. Do not apply the patch if main already contains
the identical file. Shared host was last verified at `0011_capture_performance`.

## Observed problem

Renato's real run logged:

- Case capture: 28.546 seconds; another attempt hit the 30-second SQL timeout.
- Interpretation: 35.027 seconds, including a second structured-output request.
- Six query embeddings together: 1.368 seconds.
- Six sequential hybrid query pairs: lexical approximately 7–14 seconds each,
  dense approximately 11 seconds each; search total 120.296 seconds.
- Web fetching: 14.683 seconds for ten attempted pages, with three failed pages.
- Source registration: cancelled after 192.488 seconds.

These are peer log measurements, not a controlled before/after benchmark. The
application had an N+1 document-alias loop and a lease heartbeat that waited for
the case write lock. Renato has patched both locally, plus bounded runtime
lock/idle waits and batched case summaries. Do not attribute the whole delay to
Apertus, embeddings or hardware, and do not duplicate those application fixes.

## Execute

1. Confirm checkout contents, current revision, backup/readiness and active
   application sessions. Coordinate a short application submission pause. Preserve
   ingestion/watchdogs. Stop only coordinated stale application sessions, never
   all database connections or another developer's work.
2. Review and apply `0012_membership_lookup` through the normal maintainer
   `navigator --env-file PRIVATE_MAINTAINER_ENV db-migrate` workflow. It replaces
   correlated snapshot membership policies with an uncorrelated visible-snapshot
   set. It changes no data, columns, vectors, identities or grants; snapshot RLS
   still applies. Its DDL lock timeout is three seconds. If blocked, identify the
   blocker and coordinate; do not disable RLS or silently raise every timeout.
   Do not run migrations as an application user or manually stamp Alembic.
3. Verify the revision and the four policies on `corpus.snapshot_documents`,
   `corpus.snapshot_entities`, `corpus.snapshot_claims` and
   `retrieval.snapshot_chunks`. On disposable infrastructure run owner isolation,
   scope revocation, live snapshot and retrieval checks. Never run destructive
   integration tests against the shared navigator database.
4. Inspect statistics, index definitions/validity and query plans under the
   restricted runtime role, its real principal/namespace and an authorized pinned
   snapshot. Compare EXPLAIN before/after; run bounded read-only EXPLAIN ANALYZE
   for one coordinated representative lexical and dense query, avoiding an
   unbounded full benchmark while ingestion is active. Superuser plans do not
   establish runtime behavior. Record actual rows, loops, buffers, spills and
   timing, including RLS membership evaluation. Verify rather than assume a GIN
   scan or usable vector index: previous 0011 EXPLAIN did not choose GIN.
5. If stale planner statistics contribute, perform targeted ordinary ANALYZE
   during the agreed window. Investigate any remaining repeated scope/manifest
   work, disk spills or full distance scans before proposing changes. Keep exact
   scope/snapshot/config eligibility and independent lexical/vector candidates.
   Do not add a generic HNSW index blindly: prove compatibility with the actual
   vector type/dimension, embedding config, filtered snapshot query and recall.
   Any further schema/index change needs a coordinated migration and disposable
   validation; no embedding/model substitution, re-ingestion or broad grants.
6. Measure capture separately. 0012 targets membership visibility and is not a
   guaranteed cure for capture creation or all dense-search costs. Confirm that
   the deployed capture function matches 0011, inspect its joins/triggers on a
   disposable representative copy or coordinated permitted test, and report
   remaining cost without dropping literal/hash/scope checks.
7. Return the exact revision, policy verification, before/after evidence, remaining
   bottlenecks and a short peer restart/acceptance handoff. Renato restarts API
   and worker to activate his local fixes, then runs one fresh permitted case
   through structured results, human review and actual PDF/PPTX where available.
   Keep fresh-case acceptance separate from recovery of an already expired run.

Record results in the focused runtime/performance handoff. Never commit credentials
or raw company context. This prompt authorizes the coordinated database rollout,
not publishing unrelated work or changing Renato's frontend/runtime files.
