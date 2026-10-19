# Frontend workspace

Browser UI (React/TypeScript/Tailwind), connected to the authenticated HTTP API by
default. Requires Node **22.18+**. Screens are described in
[FRONTEND_PLAN.md](../../docs/plans/FRONTEND_PLAN.md); current deployment gates are
in the [integration handoff](../../docs/team/INTEGRATION.md).

```text
npm ci
npm run dev     # http://localhost:5173
npm test
npm run build
```

Start API and worker using the [backend README](../backend/README.md). The Vite
development proxy sends `/api` to localhost:8000. For separate hosting set public
`VITE_API_BASE_URL` and exact backend CORS origins; production can reverse-proxy
`/api` to the backend. Static preview needs this proxy or an explicit API origin.
Enter an operator bearer token at Connect. It stays in memory, so reload requires
reconnecting; server jobs continue independently and active run polling resumes.
Do not put tokens, model keys or database credentials in `VITE_*` or git.

`NavigatorApi` is implemented by `api/httpApi.ts`: real run polling, durable
clarifications, exact report/selection hashes, authenticated PDF/PPTX download when provisioned,
persisted hold/outcome flags and action notes. Chat explicitly selects new focus/research or rewriting the existing report.
Blocking clarification supports free text and server choices; it resumes the same
run. Failed drafting retries the existing frozen pack instead of retrieving again. Source badges
distinguish new web research; absent lineage is explicitly unavailable.

For the original seeded demo only, set `VITE_API_MODE=mock` in an ignored
`.env.local` and restart Vite. Its browser PDF/PowerPoint exports and localStorage are demo-only. The board is
home; the standalone desk/action screens were removed. All cards must be reviewed
and at least one kept for export. HTTP mode uses server-authorized exports;
optional PPTX, manual company plans and own-case comparison require backend activation. Hierarchy/expertise/missing-field displays are optional and are not yet fully
populated by the backend. Facilities/services use their actual entity categories.
History browsing is read-only; selection/export applies only to the current report.
No-match results retain their caveats. The connection checks API compatibility and
server export formats; unavailable features stay hidden.
An HTTP failure never switches to mocks. The connection token and live case
content are never saved by the frontend to localStorage.

Manual plans use explicit operator confirmation and start a new input/review cycle.
Case comparison requires a real permitted case and exact reviewed report; no demo
case is automatically indexed. Institution labels outside the pilot use a neutral
badge. See [rich outputs](../../docs/data/RICH_OUTPUTS.md) and
[own-case memory](../../docs/data/CASE_MEMORY.md).


19 October integration: `feat/my-desk` includes the latest `ui-polish`. Official Radix Themes supplies common controls, menus, status selects, navigation and export dialogs; Tailwind owns layout. Local testing auto-connects when the backend enables loopback-only `RUNTIME_LOCAL_ACCESS`; shared servers retain bearer access. Creation immediately opens a preparation route (prompt remains memory-only); active case polling backs off and stops when leaving. See [runtime feedback/acceptance](../../docs/team/RUNTIME_FEEDBACK_AND_SEARCH.md).
