# HTTP interface

FastAPI serves `/api/v1`; `/openapi.json` and `api/schemas.py` define exact
payloads. The React `NavigatorApi` HTTP adapter maps these to browser types.
Backend service ports are in [service interfaces](SERVICE_CONTRACTS.md).

## Access and transport

Shared deployments use `Authorization: Bearer <operator token>`. Its SHA-256
digest maps server-side to a principal, namespace and trusted DSN. The browser
keeps the raw token in memory. Optional `RUNTIME_LOCAL_ACCESS=true` permits
loopback testing with one existing identity binding, guarded by host/origin/
forwarded-request checks; shared deployments keep it false.

Mutations require `Idempotency-Key`; retry the same key/body after transport
failure. Changed bodies with the same key conflict. Expected revisions and hashes
reject stale writes. Development Vite proxies `/api` to port 8000; separate
origins need exact CORS configuration. Provider/DB credentials never reach clients.

## Resources

All paths below follow `/api/v1`.

| Endpoint | Purpose |
| --- | --- |
| `GET /capabilities` | API compatibility, local access mode, enabled output/features; not full provider health |
| `GET /cases`, `POST /cases` | Paginated owned summaries; create input and optionally queue research |
| `GET /cases/{id}`, `PATCH /cases/{id}` | Current/history projection; guarded lifecycle updates |
| `POST /cases/{id}/runs` | Queue a researched run for the intended input/profile |
| `GET /cases/{id}/runs/{run}` | Actual state, concurrent activity, clarification and safe errors |
| `POST /cases/{id}/runs/{run}/answers` | Resume exact question/input/run |
| `POST /cases/{id}/runs/{run}/cancel` | Explicit cancellation |
| `POST /cases/{id}/messages` or `/inputs` | Formatting, focus or identity edit with expected revision |
| `GET /cases/{id}/runs/{run}/matches` | Frozen supported-pack projection |
| `GET /cases/{id}/evidence-packs/{pack}` | Authorized pack and hash |
| `GET /cases/{id}/evidence/{evidence}` | Authorized literal source/support |
| `POST /cases/{id}/reports`, `GET /cases/{id}/reports/{result}` | Draft from eligible pack; exact revision/hash |
| `PUT /cases/{id}/reports/{result}/reasons/{key}/selection` | Keep/reject decision bound to displayed result hash |
| `POST /cases/{id}/reports/{result}/reviews` | Immutable approval of exact result/selection hashes |
| `POST /cases/{id}/exports` | Reviewed PDF or enabled PPTX → operation URL |
| `GET /operations/{id}` | Pending/running/committed/failed artifact operation |
| `GET /cases/{id}/exports/{export}` and `/download` | Metadata and reauthorized artifact bytes |
| `GET /action-items`, `POST /action-items`, `PATCH /action-items/{id}` | Owned follow-up notes/status, no automatic messages |
| `PUT /cases/{id}/business-context` | Enabled explicit manual plans; new input/review cycle |
| `POST /cases/{id}/memory` | Enabled explicit opt-in own-case indexing |

## Client behavior and evidence

Creation opens an immediate preparation view while the command captures corpus
membership. The worker runs research; the browser polls with backoff and stops
observation on navigation. Closing the browser does not cancel execution.
Run status is separate from board status. Activity lists actual concurrent work,
not fabricated completion percentages. Resume uses existing run identity.

Reasons link claim IDs to exact evidence IDs, passages, URLs and origin/review
badges. Recorded search lineage is shown when available. Missing hierarchy,
expertise, roles and contacts remain absent; clients cannot infer them. Historical
reports are read-only. Formatting reuses a pack; changed focus researches anew.

All cards reviewed plus one kept gates approval/export. Exact current result and
selection hashes, accepted review and source access are rechecked by the server,
worker and download route. HTTP never falls back to browser/mock exports.
Optional formats/manual plans/memory appear only when capabilities permit them.

Errors contain a safe stable code, message, retryable flag and request ID.
401 reconnects; 404 conceals foreign resources; 409 reloads stale state; 422 is
validation; 413 is size; 502 invalid model output; 503 unavailable infrastructure.
A failed service is not no-match. Never expose raw SQL/provider bodies to users.


## Browser recovery

Observation reads use bounded transient retries and stop on navigation or rejected
credentials. A reconnect reloads run state; completed work is returned directly.
Case/session operation guards discard obsolete responses. State conflicts reload
current data without replaying selections or edits. Typed chat/answers remain in
memory through reconnect; full reload restores saved server state only.

Export retries reuse the accepted operation or uncertain submission key within the
current authenticated session and exact hashes. This reference is memory-only;
a full reload may require a new render. Server review and download authorization
remain mandatory. Safe retryability/request IDs reach diagnostics; raw error
messages/details are not rendered. See the [acceptance receipt](../project/FRONTEND_RECOVERY.md).
