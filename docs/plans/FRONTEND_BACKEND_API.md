# Frontend and backend HTTP contract

18 October 2026. Implemented FastAPI `/api/v1` and React `NavigatorApi` HTTP
adapter. `/openapi.json` and `src/backend/api/schemas.py` are the machine-readable
authority. [Integration status](../team/INTEGRATION.md) records tests and live
deployment gates. Backend modules communicate through typed in-process ports.

## Authentication and transport

Every protected request uses an operator `Authorization: Bearer ...` header.
The server maps its SHA-256 token digest to a DB principal, namespace and trusted
DSN name. No browser-provided owner, DB/model keys, anonymous production user or
ambient cookie authentication. The frontend keeps its token in memory only.

Mutations include `Idempotency-Key`; a transport retry reuses the same key/body.
A conflicting body returns 409. API requests are short commands/reads; a separate
worker owns execution. Poll actual stages without invented percentages. Closing
the browser does not cancel research; explicit cancellation is a separate command.
Same-origin `/api` is the default; separate hosting needs exact CORS origins.

## Implemented surface

Paths below follow `/api/v1`. Full request/response fields are in OpenAPI.

| Method / path | Behavior |
| --- | --- |
| `GET /capabilities` | Mode, configured adapters and export formats; configuration is not a provider health check |
| `GET /cases?limit=100&offset=0` | Authorized summaries; client paginates |
| `POST /cases` | `{prompt,profile_id?,run:true}` → 201 IDs/status URL; creation atomically queues research |
| `GET /cases/{id}` | CaseDetail: revisions, literal evidence, durable clarification turns, `revision`, `inputId`, `selectionHash`, latest `currentRun` |
| `PATCH /cases/{id}` | `{expected_revision,status?,current_revision_id?,on_hold?,outcome?}`; stale writes fail |
| `POST /cases/{id}/runs` | `{input_id,profile_id?}` → 202 new run; client reuses/polls an existing active run |
| `GET /cases/{id}/runs/{run}` | queued/running/waiting_for_input/succeeded/failed/cancelled/superseded; actual stage, questions and safe error |
| `POST /cases/{id}/messages` (or `/inputs`) | `{text,expected_revision,kind,profile_id?}` → 202; kind formatting/focus/identity |
| `POST /cases/{id}/runs/{run}/answers` | Exact `{input_id,question_id,answer}` → 202 resume/status URL |
| `POST /cases/{id}/runs/{run}/cancel` | Explicitly cancel execution |
| `GET /cases/{id}/runs/{run}/matches` | Supported frozen-pack output; no obsolete matches table |
| `GET /cases/{id}/evidence-packs/{pack}` | Authorized pack/hash |
| `GET /cases/{id}/evidence/{evidence}?run_id=...` | Exact authorized source passage; optional pack binding |
| `POST /cases/{id}/reports` | New draft from an eligible pack, expected revision and writing instruction |
| `GET /cases/{id}/reports/{result}` | Exact report projection; `resultHash`, `packId`, `packHash` |
| `PUT /cases/{id}/reports/{result}/reasons/{key}/selection` | Selection plus expected result hash → current selection hash |
| `POST /cases/{id}/reports/{result}/reviews` | Exact result/selection hashes and accepted/rejected decision → immutable review ID |
| `POST /cases/{id}/exports` | Result/review IDs, both hashes and format pdf → 202 operation URL |
| `GET /operations/{id}` | Durable pending/running/committed/failed export; authenticated download URL when ready |
| `GET /cases/{id}/exports/{export}` | Export metadata |
| `GET /cases/{id}/exports/{export}/download` | Authorized PDF bytes, safe filename and no-store |
| `GET /action-items` | Authorized questions, roles, statuses and optional answer notes |
| `POST /action-items` | `{case_id,question,ask_role}`; stores an operator task, sends no message |
| `PATCH /action-items/{id}` | `{status,answer?}`; status open/asked/done |

## UI and evidence rules

Board statuses are researching/in_review/pitch_sent/closed. On hold is an
independent flag; visit/no_interest is a closed-case outcome. Migration 0007
preserves existing combined statuses; legacy PATCH status aliases remain accepted.
Run state and board status are separate. Historical input revisions remain readable;
they cannot silently become the current company intent.

Every reason resolves through supported claim IDs to exact evidence IDs.
Evidence exposes origin corpus/web and reviewStatus curated/unreviewed; semantic
claim support does not certify the source. Missing facts stay unknown. Historical
similar-case scores stay empty without an authorized dataset/method. Detailed
Sankey lineage is unavailable until real recorded links are projected.

All reason cards reviewed plus at least one kept gates PDF. The client binds
selection/export to the report hash actually displayed; the server rechecks exact
current result, selection, approval and access before/after rendering/download.
Company introduction is attributed operator context. PDF includes only kept
reasons, their sources and material caveats. PPTX remains later work.

Errors contain safe code/message/request ID, never raw provider/SQL details.
401 requires reconnecting; 404 does not disclose another owner; 409 requires
refresh/review; 422 is field validation; 413 is size; 502 is invalid model output;
503 is service/storage unavailable. Failure never becomes an invented no-match.
HTTP failure never switches to mock data. Chat defaults conservatively to focus;
explicit formatting-only API edits reuse the pack and reassess the wording.

## Latest UI compatibility — 18 October 2026

Board-as-home replaces the desk/action pages; backend action resources remain.
Optional `ReasonEntry.unitPath`, `expertise`, `Reason.missingFields` and the
`infrastructure` category are frontend additions, with demo fixtures. Current
backend projections omit those optional fields and do not yet classify
infrastructure separately. Supply them only from assessed evidence in a future
coordinated contract change; omission must not be replaced by invented metadata.
HTTP PDF remains the reviewed server artifact; browser PDF/PPTX are explicit demo
features. Connected PPTX requires a new supported format plus the same immutable
review/export gates, not client generation from an unapproved projection.
