# Frontend and backend HTTP contract

Live ingestion development (18 October, authorized by Eric): backend
`RUNTIME_CORPUS_MODE=live` uses the existing HTTP contracts. New runs capture ready
readable chunks without publication. The server authorizes each immutable case
capture. Review, citations and PDF gates bind exact evidence/result hashes.
New runs see later ingestion; resumes/wording edits retain their capture.
`live_corpus_incomplete_coverage` is an explicit research limitation. No frontend
transport change is required. See [deployment](../data/LIVE_CORPUS_RUNTIME.md).

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
HTTP failure never switches to mock data. Chat explicitly selects focus/research
or formatting-only edits; formatting reuses the pack and reassesses the wording.

## Current UI compatibility — 19 October 2026

Board-as-home replaces the desk/action pages; backend action resources remain.
Optional `ReasonEntry.unitPath`, `expertise`, `Reason.missingFields` and the
`infrastructure` category are supported by the frontend. Backend projections
classify actual facility/service subjects as infrastructure. They omit the
optional hierarchy/expertise fields; supply those only from assessed evidence,
never inferred browser metadata.
HTTP PDF remains the reviewed server artifact; browser PDF/PPTX are explicit demo
features. Connected PPTX requires a new supported format plus the same immutable
review/export gates, not client generation from an unapproved projection.

## 19 October additive backend fields

Run status includes `failure_detail` with safe `failed_stage`, `model_task` and
`validation_issues` (schema field/type only). Provider bodies/prompts/credentials
are omitted. Existing generic error handling remains compatible.

The existing `trace` now uses code-owned `pack.coverage.search_trace` for new
results: original input → actual query → exact canonical supporting evidence.
These are retrieval paths, not invented ontology concepts or calibrated weights.
Older packs without recorded paths retain their empty/unavailable trace. Wording
edits reuse the original pack/trace. Frontend source files were not changed.

## 19 October frontend compatibility audit

The user authorized frontend integration changes. Connection verifies schema 1,
polling transport and server format capabilities. Only connected PDF is exposed
when configured. Mutations allow 120 seconds for live capture; a transport retry
retains its idempotency key. Read requests retain a 30-second timeout.

Clarifications provide free text even when `choices=[]`; only IDs from the current
run are actionable. New focus messages are blocked while an answer is pending.
Chat explicitly selects `focus` or `formatting`; formatting reuses the frozen pack.
A failed run with a current-input `pack_id` retries `POST /reports` with that pack
and current case revision. A failure without a reusable pack starts new research.

History selection changes only the browser’s viewed revision. Older reports are
read-only; no `PATCH current_revision_id` is sent merely to inspect history.
Selection/export still bind the current result hash and reviewed selection hash.
Cards resolve sources from both line and entry citations, including empty entries.
No-match coverage/gaps remain visible. `facility`/`service` subjects map to the
additive `infrastructure` reason category. Optional structured fields stay absent.

## Optional own-case memory — backend addition, 19 October 2026

See [API, eligibility and score semantics](../data/CASE_MEMORY.md). The backend
returns `memory.available/eligible` and existing `revisions[].similarCases`.
Frontend owner: offer an explicit permitted/non-synthetic opt-in only after exact
review, call POST `/cases/{id}/memory` with the documented attestations/revision/
result hash, and allow opt-out. Hide controls when unavailable. Display score as
an uncalibrated similarity index out of 100, not a percentage probability; show
index date/differences. New fields are additive; no frontend files were changed.

Domain profiles: entries retain the current `institution` badge enum and add
optional `institutionLabel` for the exact supported institution outside the pilot.
Render that label with a neutral badge when institution=Other. See
[domain configuration](../data/DOMAIN_PROFILES.md). Backend fields are generic;
existing frontend files remain unchanged.

## Implemented rich feature controls — user-authorized integration, 19 October

The frontend now implements the memory opt-in/out controls above, exact reviewed
hash checks, generic `institutionLabel`, manually confirmed business plans and
server-reviewed PPTX. Earlier frontend-owner handoff notes described the state at
the preceding checkpoints; these additions are now connected. No mock fallback.

`PUT /cases/{id}/business-context` takes expected_revision, confirmation and a
full replacement `values` object; returns a run/status_url. Saving creates a new
input/report review cycle. Values and limits: [rich outputs](../data/RICH_OUTPUTS.md).
Case detail adds `businessContextAvailable`, `businessContext`, `memory` and
`exportFormats`; absent/unavailable features stay hidden. The transport refuses
manual updates from an unseen revision. Current report company facts include
explicitly attributed frozen plans, not model-extracted business data. Export
uses format-specific MIME/filename and the same exact review gates as PDF.
