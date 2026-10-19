# Runtime feedback, search latency and local testing

19 October 2026. User-authorized frontend/backend integration on `main`.
`feat/my-desk` was merged; it already includes the latest `ui-polish` demo changes.
The separate frontend ownership rule remains the default for future backend tasks;
this integration was explicitly authorized by the user.

## Findings and changes

Peer-side read-only inspection verified shared revision `0011_capture_performance`.
An application full-text query had been active for 688 seconds; several concurrent
case operations were waiting for tuple/transaction locks. This does not prove
hardware is the cause. Successful GET status polling was drowning out useful logs.

- **Search:** constant per-language full-text branches avoid repeated query parsing
  and provide fixed keys for the existing GIN index where the planner/RLS allow it,
  preserving the ingestion language configurations (English/German/French/Italian
  and simple), exact matching/rank aggregation and all eligibility checks. Keywords
  and vector candidates remain independent and fuse using the existing RRF.
  Query variants, top limits and the configured models remain unchanged. Live
  ownership no longer extracts a large manifest per candidate after validating the
  pinned capture. Retrieval SQL has a 30-second per-statement bound; it does not
  silently return a truncated corpus on timeout.
- **Membership policy:** migration `0012_membership_lookup` replaces correlated
  membership visibility checks with an uncorrelated visible-snapshot set, allowing
  a hashed subplan. Caller RLS still checks namespace/live-case ownership; source
  scope grants, revocation and write checks remain. No tables, columns, source data,
  vectors or grants are added/removed. No re-ingestion or re-embedding is required.
- **Reads:** runtime status/detail authorization checks no longer acquire case
  write locks. Mutation paths retain locks, current-input checks and review gates.
  Case listing uses four batched summary queries regardless of page size, rather
  than loading/validating every historical report for each card. Opening a report
  retains its full evidence and integrity checks. Summary/detail share one projection.
- **Web deduplication:** pinned corpus documents and aliases are read together in
  one lookup, replacing one alias query per document for every candidate URL.
  Canonical URL comparison, scope checks and pinned-corpus preference remain.
  A pure duplicate lookup no longer locks the case/run for writing; recording
  sources still checks and locks the active run before writes.
- **Lease renewal:** heartbeat authorization reads owner/current input without
  taking the case write lock; lease mutation still requires the same worker and
  an unexpired running job. This prevents registration's write lock from
  starving its own worker lease. Cancelled/superseded inputs remain rejected.
- **Progress:** bounded `runtime.progress.*` receipts reuse `ops.stage_attempts`;
  they are not evidence or job queue entries. Start/finish record actual stages.
  `/runs/{id}` exposes concurrent `activity` entries (`step`, `started_at`) and
  the current step. Completed/failed/superseded runs expose no active activities.
  Worker restart refreshes a restarted activity's timestamp. Interrupted progress
  is diagnostic; checkpoint/committed stage output remains the recovery authority.
- **Browser:** submit navigates immediately to `/cases/starting/{requestId}` while
  the existing server command prepares its capture. The prompt/promise stays in
  memory, not URL/storage/history. The real case URL is substituted after acceptance.
  Refreshing that transient route requires checking My cases before resubmission.
  Preparation is honest waiting feedback, not a claim of asynchronous DB capture.
- **Polling:** unchanged run state backs off from 1.2 to at most 5 seconds. Actual
  progress resets the interval. Leaving an active workspace stops its observation
  without cancelling server work. Reopening observes the same run. Concurrent
  detail requests are coalesced. Card bodies and an explicit menu open the workspace;
  missing briefs offer a start/resume action. Desk steps include running/failed cases.
- **Components:** official Radix Themes controls, navigation, badges, menus, status
  select, preparation/progress surfaces and export dialog sit on the existing
  Tailwind layout. Bern logo, routes, review/export constraints and source drawers
  remain. Dialog Escape/focus handling and reduced-motion support are preserved.

## Console logging

`navigator-runtime serve` and `worker` configure timestamped INFO logs. Restart both.
The API reports command start/end with request ID and duration, slow/error reads,
and run progress changes. Successful repetitive case/run/operation polling access
lines are filtered; errors and mutations remain visible.

The worker reports stage start/end/failure, cache reuse, model task/model/attempt,
model usage counts, embedding batches, each lexical/vector query, reranking,
backbone calls and fetched-page counts. Async activities emit a waiting heartbeat
every 10 seconds. Example (illustrative):

```text
2026-10-19 10:00:00 INFO backend.runtime | stage.started run_id=... stage=retrieve.1
2026-10-19 10:00:00 INFO backend.runtime | embedding.started query_count=6
2026-10-19 10:00:01 INFO backend.runtime | retrieval.lexical.started attempt=1
2026-10-19 10:00:02 INFO backend.runtime | retrieval.lexical.completed elapsed_ms=...
```

API and worker are separate processes: model details appear in the **worker**
terminal. To retain both logs, pipe each command through `tee` to ignored local
files. Times use the process host's local time. Payloads, company prompts, source
bodies, keys, DSNs and provider error bodies are not console fields. No Langfuse
availability is required. `uvicorn` invoked directly needs its own logging setup;
the documented CLI configures these defaults.

Worker preparation also logs named `worker.database` tasks (configuration,
marking the run, checkpoint authorization, initial state and completion) plus
`worker.checkpoint_read`. Lease failure logs its error class before cancelling
the operation. Quiet idle queue polling and successful lease renewals stay quiet.
Model payload/schema JSON uses compact separators, preserving all values and
validation. `model.validation_failed` distinguishes a required repair from an
exhausted repair without printing validation input or provider content. The
reported interpretation took two requests, not a switch away from Apertus 70B.

The supplied logs measured 35.027 seconds interpretation (including repair),
1.368 seconds batched embeddings, 120.296 seconds search across six sequential
lexical/vector pairs, 14.683 seconds web fetching and 192.488 seconds registration
before cancellation. These are observations from the old running worker, not
post-fix latency claims. Application hot paths and shared database plans need
separate verification. Do not claim that 0012 guarantees fast exact dense search.

## Suspended-process incident and runtime safeguards

During the operator's next test, read-only inspection found two obsolete local
API/worker processes in Linux stopped state, alongside the current processes.
An idle transaction had held a case lock for over 30 minutes; the new worker's
preparation and other requests queued behind it. The obsolete processes received
TERM followed by CONT so their pending termination could run. They exited and
their connections/locks cleared. Current API/worker, SSH and ingestion were left
running; no shared database session was explicitly terminated or migrated.
The newer run subsequently reached interpretation, web fetching and retrieval;
this observation is not a claim that its full report/export succeeded.

Runtime composition now creates API/worker database connections with at most
**5 seconds lock wait** and **60 seconds idle inside a transaction**, preserving
stricter existing server policies. A suspended client cannot indefinitely retain
its transactional locks. Active model calls should not have open SQL transactions.
Ingestion/migration engines and separate checkpoint credentials are unchanged.
These settings require an API/worker restart; they do not change role/global
database defaults. Existing retrieval/capture statement bounds still apply.

Stop a terminal service with **Ctrl+C**, not Ctrl+Z. Ctrl+Z suspends it while
leaving sockets/transactions alive. Inspect `jobs -l` and `ps` before starting
another copy; `fg` followed by Ctrl+C stops the selected suspended job. Never
kill every PostgreSQL session or another developer's services as cleanup.

## Local access without token entry

Set in the ignored backend env:

```dotenv
RUNTIME_LOCAL_ACCESS=true
```

Exactly one existing server-controlled identity binding is required. The API must
bind to `127.0.0.1`, `::1` or `localhost`. CLI disables proxy-header trust. Tokenless
requests require a loopback client/Host and, if present, loopback Origin; forwarded
headers and other hosts/origins are rejected. PostgreSQL role, namespace, scope
checks and case ownership remain. This is not anonymous access to a shared host.
The frontend probes capabilities automatically and connects without a token.

Shared/non-loopback deployments leave the flag false (the committed examples'
default). Existing bearer authentication remains supported. Invalid supplied tokens
are rejected even in local mode. No model/database credential moves to the browser.
Renato's ignored private env has this flag enabled; teammates choose their own mode.

## Verification and limits

- 284 backend tests passed on disposable PostgreSQL/pgvector, including local-access
  boundaries, read-under-write-lock, progress, existing owner/revocation/recovery
  and review/export checks. Never run this suite against the shared host.
  Added real PostgreSQL checks cover bounded lock waits, preservation of stricter
  policies, release of a simulated suspended transaction's locks, summary/detail
  equivalence and a fixed query count without historical-report hydration.
  A duplicate-lookup regression check confirms one alias query and completion
  while another transaction holds the case write lock; existing alias preference,
  canonicalization and isolation tests remain included.
  The lease regression renews while the case is write-locked and rejects a wrong
  worker/cancelled run. Latest frontend tests/build also pass after restoring the
  operator's preferred dark quick-start panel; research behavior is unchanged.
- 24 frontend transport/policy tests passed; TypeScript and production build passed.
- Restricted-role retrieval over **20,004 synthetic chunks** returned 30 hits in
  **1.871 seconds**, with the hashed membership subplan confirmed. One query, fixture
  vectors, local PostgreSQL, no real embedding/reranker/model call: this is not a
  live throughput or retrieval-quality benchmark.
- Browser acceptance results are recorded below after the final check. Browser
  synthetic transport and mock data do not establish live research quality.
- A read-only EXPLAIN of the new lexical query on the shared **0011** server
  selected existing chunk/projection indexes, **not the GIN index**. No retrieval
  was executed by that probe. Re-check after the membership migration; do not
  claim a measured production GIN speedup from the rewritten query alone.
- Shared migration/real-corpus latency and a fresh full Keera research run remain
  separate acceptance steps. Apertus inference, embedding hosting, reranker cold
  start and sequential policy-controlled web fetching still take time. Web remains
  bounded to ten pages; a component library does not accelerate remote services.

## Eric's rollout

1. Preserve ingestion work/private configuration and update from integrated
   `main`, including runtime commit `88f5b75`. The user authorized publication
   after this integration and verification; confirm the commit is in your checkout.
2. Coordinate a brief pause of application submissions and use the approved
   maintainer command: `navigator --env-file PRIVATE_MAINTAINER_ENV db-migrate`.
   Confirm `0012_membership_lookup`; lock wait remains three seconds. Do not widen
   grants, disable RLS or stop ingestion/watchdogs. No shared migration ran here.
3. Restart each developer's API and worker to remove old code/unbounded queries;
   coordinate only explicitly identified stale application sessions if necessary.
4. Restart Vite after dependency installation (`npm ci` in `src/frontend`). Check
   local access and `/capabilities`, submit one permitted case, and measure each
   new diagnostic stage through review/export. Keep existing source IDs/pins and
   inspect expected coverage, revocation/owner boundaries and prior reports.

Full copyable maintainer task: [Eric's runtime performance prompt](prompts/07_SHARED_RUNTIME_PERFORMANCE.md).
Remote refs were fetched twice during this follow-up: `origin/main` remained
072f099, `feat/my-desk` 065bf28 and `ui-polish` f690464 were already ancestors of
local main. No new UI commits needed merging. The only newly discovered branch,
`codex/b2b-delivery-docs` f53c4bc, edits judge/root submission documents. The user's
subsequent instruction to merge everything authorized integrating that branch too;
both desk and B2B decisions were retained as D28/D29. Existing work was preserved.

### Final browser checks

Chrome desktop/mobile checks passed with explicit synthetic/mock providers:
card-body navigation, menu Open case, export blocked until review, Escape dialog
close, 390px desk without horizontal overflow, local capability auto-connect with
no bearer header, concurrent retrieval/fetch labels, and leave/reopen observing
one run without a duplicate creation. A delayed synthetic create response took
two seconds; the preparation route appeared in 0.045 seconds. No browser page
errors occurred. Screenshots/temporary diagnostics are ignored under `.local/`.
This does not establish production latency or a live report's factual quality.
