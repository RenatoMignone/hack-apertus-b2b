# Frontend/backend recovery receipt

Measured 19 October 2026 on `codex/frontend-backend-recovery`; integrated into
`main` after merging the latest retrieval-performance changes. No backend endpoints, retrieval SQL, migrations or shared-host settings
changed.

## Behavior

- Status observation retries transient reads with three bounded backoff retries;
  the existing per-request transport retry and deadlines remain. Explicit
  nonretryable responses and authentication failures stop observation. Reconnect
  reads the current run before deciding whether to observe or retry failed work;
  a completed run never becomes a new research command.
- Navigation cancels observation requests/delays, not accepted server jobs.
  Component/operation ownership rejects late responses, including A → B → A and
  session replacement. Latest list refreshes supersede older responses.
- Revision conflicts reload authoritative state without replaying edits, selections
  or approvals. Unsent chat/clarification text remains in component memory through
  failures, chat closure and reauthentication; it is not persisted across a full
  browser reload. Saved reports, questions and selections reload from the server.
- Connection interruption, clarification, failed research, failed drafting and
  valid no-match have different recovery actions. Prior reports remain available.
- Accepted export operations and uncertain submission idempotency keys remain in
  adapter memory for the authenticated session and exact report/selection hashes.
  Repeated clicks share one operation. Changed content requires fresh review.
  A full reload loses this in-memory operation reference; later export still
  revalidates all hashes but may submit a new render. No browser storage is added.
- Safe error code, retryability and validated request ID are retained. Export
  errors are visible inside the modal; request IDs can be copied. Raw server
  messages/details, provider bodies and credentials are not shown by the adapter.
  Session expiry opens a reconnect overlay and stops failed observation; successful
  authentication reloads current state and clears obsolete notices.

## Verification

- **39 transport/helper tests and 18 React interaction tests passed.** Cases include
  transient/unavailable reads, nonretryable/401 responses, navigation, duplicate
  clicks, stale revisions, clarification, model rejection, no-match, session
  replacement, export reconnection and safe diagnostics.
- TypeScript and production build passed. Existing bundle-size and ineffective
  dynamic-import warnings remain.
- **304 backend tests passed** against explicitly disposable local PostgreSQL in
  50.60 seconds, including review/export guards and checkpoint recovery. Existing
  pytest warning remains.
- Browser acceptance used a separate disposable scripted API/worker with PostgreSQL
  checkpoints. Verified clarification → refresh/reconnect → answer → report;
  stale selection refresh with unsent text retained; reviewed PDF download;
  injected 401/reconnect retaining text; and four injected export-status 503s.
  Export retry succeeded with **one POST export and five operation reads**.
- A fresh actual-Apertus 70B isolated fictional match passed: two assessed reasons,
  review/PDF, wording revision and stale-download rejection in **63.271 seconds**.
  This HTTP acceptance is separate from the browser fault-injection checks.

After integration with `18ef3a6`, all **310 backend tests** and **57 frontend tests**,
TypeScript and production build passed again on the combined tree. No shared-host
migration or configuration was performed by this integration.

These checks establish local integration/recovery, not real-corpus quality,
shared-host retrieval performance or deployment acceptance.

## Reproduce

Run `npm ci`, `npm test` and `npm run build` inside `src/frontend`.
Backend regressions require an explicit disposable `NAVIGATOR_TEST_ADMIN_DSN`;
run `python -m backend.tests.run` from the repository root.

For browser faults, start the existing smoke harness with a disposable DSN:

```sh
python -m backend.tests.runtime.smoke --port 8014 --clarify --postgres-checkpoints
```

Then inside `src/frontend` run:

```sh
VITE_API_MODE=http VITE_API_BASE_URL= npm run dev -- --config tests/browser/vite.recovery.config.mjs --host 127.0.0.1 --port 5175 --strictPort
```

Use only the harness's fictional cases and `synthetic-browser-smoke` test token.
The test-only Vite proxy forwards to loopback 8014. Before an action, place a JSON
rule in ignored `.local/recovery/fault.json`, for example:

```json
{"path":"/operations/","method":"GET","remaining":4,"status":503}
```

This replaces the next four matching status reads with safe synthetic errors.
Retry PDF export after the bounded failure; `.local/recovery/counts.json` records
export submissions and operation reads without request bodies or case identifiers.
Set the rule to `{}` to disable faults. For authentication, target the test case's
path with one 401 and `"code":"authentication_required"`, then reconnect.
The helper is test infrastructure, not a production API or deployment option.

Actual-model reproduction uses the existing isolated route in
[quickstart](../judges/QUICKSTART.md#optional-actual-apertus-with-isolated-fictional-evidence).
Private receipts and screenshots stay under ignored `.local/recovery/`.
