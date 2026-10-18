# Runtime HTTP integration for the frontend owner

The existing React code is unchanged. Read-only reference:
`src/frontend/src/api/index.ts`, `types/contract.ts`. A real client can implement
NavigatorApi using the API below, without exposing DB/model keys. Polling is the
baseline; the backend never runs inference in an HTTP background task.

Every protected request has `Authorization: Bearer <user-token>`. Every mutation
also has a stable `Idempotency-Key` (1–128 visible ASCII characters). Reuse that
key/body after network failure; changed body with the same key returns 409. UUIDs
are opaque strings. Optional X-Request-ID is validated; responses echo a safe ID.
OpenAPI is at `/openapi.json`; DTO source is `src/backend/api/schemas.py`.

| NavigatorApi behavior | HTTP mapping |
| --- | --- |
| listCases | GET `/api/v1/cases?limit=50&offset=0` → CaseSummary[] |
| createCase | POST `/api/v1/cases` `{prompt, profile_id?, run:true}` → 201 IDs + status_url; poll, then GET case |
| runCase | POST `/cases/{id}/runs` `{input_id,profile_id?}` → 202 + status_url |
| getCase | GET `/cases/{id}` → CaseDetail with existing revisions/reasons/turns/evidence |
| sendMessage | POST `/cases/{id}/messages` `{text,expected_revision,kind}`; formatting/focus/identity; 202 + status_url |
| answerFollowUp | POST `/cases/{id}/runs/{run}/answers` `{input_id,question_id,answer}` → 202; question IDs are on the run and followUp turn |
| setSelection | PUT `/cases/{id}/reports/{result}/reasons/{key}/selection` `{selection,expected_result_hash}` → selection_hash |
| setStatus / setCurrentRevision | PATCH `/cases/{id}` `{expected_revision,status? ,current_revision_id?}`; historical input cannot silently replace current intent |
| exportDeck → PDF | POST `/cases/{id}/reports/{result}/reviews` with exact hashes and accepted decision, then POST `/cases/{id}/exports` with result/review IDs, hashes and `format:pdf` → 202 operation URL |
| Export polling | GET `/operations/{operation_id}` → pending/running/committed/failed; committed includes download_url |
| Download | GET `/cases/{id}/exports/{export_id}/download` with auth → application/pdf, safe filename, no-store |
| listActionItems / setActionStatus | GET `/action-items`, PATCH `/action-items/{id}` `{status:open|asked|done}` |
| subscribe | Client-side polling/refetch; no server push subscription yet |

All shortened paths in this table follow `/api/v1`. Also available: GET
`/capabilities`; explicit case cancellation; pack/match/citation inspection;
POST `/cases/{id}/reports` for a new draft from an eligible existing pack; and
GET export metadata. No direct SQL, source publication, confidential upload,
model endpoint, arbitrary tools or checkpoint administration route exists.

Run polling returns `status` queued/running/waiting_for_input/succeeded/failed/
cancelled/superseded; `state` is the stored business-execution state. `stage`
projects interpreting/searching/validating/drafting/done when available, and
`step` is the last actually committed node. No fabricated completion percentage.
On waiting_for_input, display open questions rather than treating it as done.
On failure, error_code is safe; it does not mean there were no experts. On success,
GET the case for the exact revision and citations. A disconnected browser does not
cancel a run. Retry cancellation or mutations with their original idempotency key.

CaseDetail adds `revision`, `inputId`, and `selectionHash`; each BriefRevision adds
`resultHash`, `packId`, `packHash`. Evidence adds `origin` and `reviewStatus`; the
frontend owner needs source badges. Editorial none/kept/rejected remains distinct
from factual support. The backend requires every card reviewed and at least one
kept before an accepted review. Send `expected_result_hash`,
`expected_selection_hash`, decision `accepted`; the response gives review_id.
Selection/result changes invalidate prior export authorization.

Stable reason categories derive from supported subject types (person → people,
project → projects, otherwise groups; adjacent idea → ideas). Unsupported roles
are not synthesized. SimilarCases remains empty until an eligible history dataset
exists. Partial/no-match limitations come from actual pack outcomes. Unavailable
web is visible as a limitation, not a claim of comprehensive online coverage.

Errors use `{schema_version,error:{code,message,retryable,details},request_id}`.
401 requires sign-in/token; 404 conceals unavailable/foreign resources; 409 means
state/hash conflict; 422 gives field/type errors without echoing inputs; 413 is
oversize; 503 means required service/storage unavailable. Never render raw stack
traces or provider responses. On 409 reload the case and preserve unsent text.
CORS uses an explicit server allowlist and bearer headers, not ambient cookies.
