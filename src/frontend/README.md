# B2B frontend

React/TypeScript, Vite, Tailwind and Radix Themes. Requires Node 22.18+.

```bash
npm ci
npm run dev
npm test
npm run build
```

HTTP is default; Vite proxies `/api` to localhost:8000. Start API and worker using
[root Make commands](../../docs/data/LIVE_SETUP.md). Separate hosting needs an
explicit public `VITE_API_BASE_URL` / exact CORS or a reverse proxy. Never put
provider/DB/operator secrets in `VITE_*`.

Shared access keeps the operator bearer token in memory; reload reconnects while
server jobs continue. Configured loopback access auto-connects. `NavigatorApi`
implements polling, clarification, revision/selection hashes and authorized export.
Creation opens immediate preparation; case reopening observes the durable run.

`VITE_API_MODE=mock` explicitly selects the scripted HelioSense tour and browser-
local demo state/exports. Restart Vite when changing mode. HTTP failures never
switch to mocks; live tokens/case content do not enter localStorage.

My desk, board and workspace support source inspection, chat modes, history and
review. All cards reviewed plus one kept gates export. Connected PDF/PPTX uses
backend review/operation/download; optional formats/plans/memory are capability-
gated. Historical reports are read-only. Missing metadata remains unknown.

Read [screens](../../docs/plans/FRONTEND_PLAN.md),
[HTTP](../../docs/plans/FRONTEND_BACKEND_API.md) and
[walkthrough](../../docs/judges/DEMO.md). Coordinate consumer/interface edits with
the backend; tests/build verify interaction contracts, not live research quality.
