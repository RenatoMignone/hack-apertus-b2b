# Frontend — screens, HTTP behavior and demo mode

19 October 2026 · Integrated HTTP client audited against the backend.
[HTTP contract](FRONTEND_BACKEND_API.md) owns transport; [integration evidence](../team/INTEGRATION.md)
separates synthetic checks from pending live acceptance.

## Run and modes

Node 22.18+: `npm ci`, `npm test`, `npm run build`, `npm run dev` from
`src/frontend/`. React/TypeScript, Vite, Tailwind and local assets.
HTTP is the default; `/api` proxies to localhost:8000 in development. Separate
hosting needs an explicit API origin and exact backend CORS settings.
The connection screen stores the operator token in memory only. Safe API errors
remain visible; failures never switch to mocks. Reload requires reconnection;
durable jobs continue and polling resumes.

`VITE_API_MODE=mock` explicitly enables seeded companies and browser-local demo
state (v7). Demo evidence is illustrative; it is not a live research result.

## Screens

Three places: My desk (home), the cases board and a case workspace. Navigation
shows My desk, My cases, New case, and Connected or an explicit Demo menu. The
standalone Action items page stays removed. Backend action-item resources remain available.

| Route | Behavior |
| --- | --- |
| `/` | My desk: quick-start text box (creates and runs a case), *All cases* (status bar, 3 most recent) and *Next steps* derived only from case state: answer the agent's question, review N items, export the brief, record the outcome. Closed and on-hold cases are skipped |
| `/cases` | Cases board: research, review, pitch sent and closed; search, hold and outcome flags |
| `/cases/new` | Permitted-text composer; confidential plans/one-pagers stay outside the app |
| `/cases/:id` | Results, revisions, chat, evidence drawer, selections and export |

Results group people, research groups, projects, infrastructure/services and
adjacent ideas. Cards show citations and optional source-backed role, hierarchy,
expertise and missing-field labels. The new optional fields are populated in demo
fixtures; the current backend does not yet supply all of them. Never infer missing
metadata in the browser. Introduction suggestions do not confirm availability.
Next steps include questions and material coverage limitations even without a
named introduction. Source badges distinguish new case-local web evidence.
The Sankey uses recorded query/evidence links only; missing lineage is unavailable.
Narrow screens show a text/source fallback. No-match caveats remain visible.

Chat explicitly chooses new focus/research or rewriting the existing report.
Blocking questions support free-text answers and use durable question/input/run IDs.
Only the current run’s questions are actionable. Draft failures with an owned pack
retry drafting; earlier failures repeat research. Company context remains attributed to the
operator, separate from public evidence. Backend categories map people, projects, facilities/services and group fallback
from actual subject types. Optional hierarchy/expertise data stays absent unless
supplied by the backend.

## Review and exports

All cards reviewed plus at least one kept gates every export. HTTP PDF uses the
backend's exact displayed result hash, current selection hash, immutable review,
queued export and authenticated download. Browser renderers cannot replace that
approval path. Server PDF remains the authoritative connected output. The UI honors the server’s
formats capability. Older versions are browsed locally as read-only history;
viewing one cannot silently replace the active backend report or its selections.

Demo mode additionally offers browser PDF (pdfmake) and editable PPTX built with
the supplied partner template (JSZip). Assets remain local and challenge-only.
These demo exports are not persisted/review-bound backend exports. HTTP PowerPoint
remains unavailable until backend format approval and artifact persistence exist.
A passing build does not establish PPTX layout quality; larger-file visual and
PowerPoint compatibility acceptance remain separate.

## Contracts and checks

`NavigatorApi` keeps case/run/revision/selection/flag operations, server PDF export
and subscriptions. The HTTP adapter retains action-item and last-opened resource
methods even though their old standalone screens were removed.
`CaseDetail` includes real run/error state and revision/hash extensions.
The evidence drawer shows exact passages, URLs, dates, origins and review flags.

Run transport and export-policy tests, typecheck and the locked build. Use the
isolated synthetic browser smoke for integrated interaction checks; an authorized live capture or published
profile plus real providers is required for live acceptance.
[Status](../project/STATUS.md) owns deployment gates and current measured results.

Demo mode seeds a hero case for the pitch: GlucoWave is not on the board at start and
is created live from the *Glucose sensor* example, written in lay terms, then refined
through a follow-up answer and an exclusion. Run sheet: [DEMO_SCRIPT.md](../project/DEMO_SCRIPT.md).
