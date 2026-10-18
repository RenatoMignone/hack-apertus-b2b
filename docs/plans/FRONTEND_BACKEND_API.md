# Frontend ↔ backend HTTP handoff

**18 October 2026 · Draft integration contract, not a running API.** U7 selects
HTTP separation. Routes/projections below are a proposed v1 handoff; agree and
export a machine-readable schema when implementation starts. No HTTP framework,
authentication provider, frontend framework or port is selected.

## Integration boundary

Use a configurable backend base URL and `/api/v1` prefix. Same-origin hosting is
the simplest initial deployment; separate frontend hosting requires an explicit
backend origin/CORS allowlist. Never expose model/database/Langfuse credentials.
Authentication/session/CSRF details depend on the later hosting/auth choice;
authorization of every resource is mandatory and cannot trust client owner IDs.

The UI needs permitted text intake, progress, clarification, structured matches
with citations, report revisions, selection/review and downloads. No confidential
PDF upload endpoint is planned. Public research PDFs use controlled ingestion.

Long retrieval/model/export work returns `202 Accepted` with stable IDs and a
status URL. Polling is the baseline; SSE/WebSockets are deferred. Show actual
stage/limitations, not invented completion percentages. Browser disconnection
does not cancel a run; cancellation is explicit.

## Proposed resource surface

Paths are relative to `/api/v1`. These project existing logical records rather
than introduce a second evidence schema or database design.

| Method / route | Input / purpose | Successful response |
| --- | --- | --- |
| `GET /capabilities` | Discover enabled features | `200`: deployment mode, schema versions, formats and optional features; no secrets |
| `POST /cases` | Permitted message/context and domain profile ID | `201`: case and immutable input revision IDs |
| `GET /cases/{case_id}` | Read authorized case overview | `200`: current revision pointers and run summaries |
| `POST /cases/{case_id}/inputs` | New message/edit, base input/result revision IDs | `201`: new input/dialogue revision; earlier revisions retained |
| `POST /cases/{case_id}/runs` | Input revision ID; server resolves/validates profile and snapshot | `202`: run ID, pinned input revision and status URL |
| `GET /cases/{case_id}/runs/{run_id}` | Poll durable work | `200`: state, stage, outcome/limitations, questions and available pack/result IDs |
| `POST /cases/{case_id}/runs/{run_id}/answers` | Question ID, target input revision, permitted answer | `202`: answer ID and resumed run status URL; stale answers fail |
| `POST /cases/{case_id}/runs/{run_id}/cancel` | Stop new work | `202`: cancellation requested; poll for acknowledgment |
| `GET /cases/{case_id}/runs/{run_id}/matches` | Inspect available validated matches | `200`: typed entities, supported fields, fit/relevance reasons, source links and limitations |
| `GET /cases/{case_id}/evidence-packs/{pack_id}` | Inspect frozen eligible pack | `200`: authorized pack view/hash, versions, support and gaps |
| `GET /cases/{case_id}/evidence/{evidence_id}` | Inspect passage; run ID required as query context | `200`: literal text, source URL/locator, document version and dates; server checks run membership |
| `POST /cases/{case_id}/reports` | Pack ID, base result revision for edits, permitted instruction | `202`: report run/job ID and status URL; eligible ready pack required |
| `GET /cases/{case_id}/reports/{result_revision_id}` | Read exact report revision | `200`: sections, claim/citation references, manifest, validation/review state |
| `POST /cases/{case_id}/reports/{result_revision_id}/reviews` | Revision/hash, selections and approve/request-changes decision | `201`: immutable review; unsupported claims cannot be approved into facts |
| `POST /cases/{case_id}/exports` | Approved result/review IDs and supported format | `202`: export ID and status URL |
| `GET /cases/{case_id}/exports/{export_id}` | Poll rendering | `200`: state, bound result/review/template and available download URL |
| `GET /cases/{case_id}/exports/{export_id}/download` | Download authorized artifact | `200`: file with content type/name; no raw path or unrestricted storage key |

Report status uses the same durable run-status projection. Report work must bind
to its case, pack and result lineage; resuming the workflow versus creating a
child run is still to be mapped in [processing design](REPORT_PROCESSING_BOUNDARIES.md).
Automatic research → draft chaining, if later enabled, reuses the report use case
and cannot bypass the frozen-pack gate. No direct SQL/model/prompt/checkpoint
endpoints are exposed to the frontend.

## Response projections and state

JSON records include `schema_version`, stable IDs and appropriate UTC dates.
Opaque IDs are not authorization tokens. Run responses expose:

```text
case_id, run_id, input_revision_id, status, stage,
outcome, limitations[], questions[], evidence_pack_id?, result_revision_id?,
snapshot_id, updated_at, links
```

Proposed transport `status`: `queued`, `running`, `waiting_for_input`, `succeeded`,
`failed`, `cancelled`. Cancellation request time is separate from acknowledgment.
`stage` projects the existing [case workflow](OPERATIONS_PLAN.md#2-caserun-state-and-contracts);
do not replace its durable state machine with a competing HTTP state machine.
`outcome` is absent while undecided, then `complete`, `partial` or `no_match`.
A successful partial/no-match assessment differs from a technical failure.
Waiting runs supply question IDs and required/optional flags.

Match views include person/unit IDs, roles/affiliations, units, expertise, projects,
infrastructure/services, fit explanation and citations where supported. Missing
values stay explicit. Separate direct/adjacent fit from evidence strength. Do not
expose raw model context, internal trace payloads or storage credentials.

Reports follow [output structure](OUTPUT_REPORT_STRUCTURE.md), with citations next
to supported assertions and separate validation/review states. Pack views retain
literal evidence versus claims, attributed input and generated hypotheses.
List pagination is stable within a pinned run; cursor and field-level JSON
schemas remain implementation follow-ups.

## Errors, concurrency and UI behavior

- Consistent errors: `schema_version`, `error.code`, safe `message`, `request_id`,
  `retryable`, optional field/revision details. No secrets, stack traces or
  unauthorized resource details.
- `400` malformed request; `422` invalid fields; `401` authentication needed;
  `403`/non-disclosing `404` per access policy; `404` unavailable resource;
  `409` stale revision/invalid stage; `429` limits; `503` required service unavailable.
  Trace-only outages cannot turn successful case work into a failure.
- Mutations accept `Idempotency-Key` scoped to caller/case/operation. Same key/body
  returns the same operation; different body under the same key returns `409`.
  HTTP deduplication complements durable stage keys, never replaces them.
- Edits, answers and reviews carry base revisions. On `409`, reload/present the
  current revision; never silently overwrite a colleague's work. Busy/duplicate
  run policy is enforced server-side before scheduling.
- Preserve unsent input on network failure. Retry with the same mutation key,
  then poll the returned resource. Do not start inference on every UI render.
- Answers target displayed questions/revisions. Display partial/no-match coverage
  and disabled offline features. Review/download binds to a specific revision.

Before implementation, agree OpenAPI/JSON projections, caller/session integration,
size limits, pagination and retry windows. Future contract fixtures must cover
success, clarification, partial/no-match, stale revisions, access denial and
export-not-ready. This scaffold includes no schema file, mock server or routes.
