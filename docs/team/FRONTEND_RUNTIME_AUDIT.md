# Frontend/runtime compatibility audit — 19 October 2026

User-authorized follow-up to backend commit `66b86cb`. Frontend integration changes
were explicitly requested; the normal backend-only ownership boundary did not
prevent this audit. No shared migration or ingestion change was performed.

## Fixed interactions

- Free-text clarification works when the server supplies no choices. Only current
  run question IDs are actionable; answers resume the same durable run. New chat
  research is blocked while answers are pending, and initial research disables chat.
- Failed drafting with a current-input frozen pack uses the report endpoint;
  failures without a reusable pack start research. A mutation gets 120 seconds for
  live capture and retains its idempotency key on transport retry.
- Chat explicitly selects research/change focus or rewriting the existing report.
  Wording-only edits reuse the same pack and undergo independent draft assessment.
- History browsing is local and read-only. It cannot replace the active report or
  export/select an older revision. Navigation guards prevent old case responses
  from replacing a newly opened case. Selection writes disable conflicting controls.
- Cards show source quotations from line citations even when entries are empty.
  No-match gaps remain visible. Query lineage has honest labels and a narrow-screen
  text/source fallback; it does not fabricate ontology links.
- Facilities/services reach the infrastructure section through the HTTP schema.
  Optional roles/hierarchy/expertise remain absent unless actually supplied.
- Connection validates schema/polling capabilities; export honors server formats.
  HTTP offers backend PDF only. Demo browser PDF/PPTX remain explicitly demo-only.

## Verification

- **243 backend tests passed**, including disposable PostgreSQL and both facility/
  service HTTP projections; **15 frontend tests passed**, TypeScript/build passed.
- Isolated real API/worker/renderer browser smoke: connect, intake, durable free-text
  clarification, source quotations without entries, review gate, kept selection,
  approved export and authenticated PDF download. Downloaded PDF text was checked.
- Browser formatting created v2 from the exact same frozen pack. Viewing v1 disabled
  selection/export and left v2 active in the database. Reconnecting after a reload
  restored the existing case. Source providers were synthetic for this browser run.
- The separate actual-provider partial report/PDF result is recorded in the
  [backend handoff](BACKEND_RESEARCH_COMPLETION.md). Combined real DB/web UI quality,
  worker restart/resume and target deployment are still open.

The repeatable browser fixture supports `--port 8001` and `--clarify`. Use only an
explicit disposable `NAVIGATOR_TEST_ADMIN_DSN`; never use the shared host. A second
Vite instance can set `VITE_API_BASE_URL=http://127.0.0.1:8001` on port 5174, leaving
ordinary local API/worker services untouched. Its token is synthetic and documented
by the fixture. Cleanup removes its own database/role only.

Build passes with existing large optional demo PDF bundles and an ineffective
mock-export dynamic-import warning. This does not certify demo PowerPoint layout.
