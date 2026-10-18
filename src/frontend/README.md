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
clarifications, exact report/selection hashes, authenticated PDF download,
persisted hold/outcome flags and action notes. Chat defaults to focus/research;
formatting-only editing is also available through the backend API. Source badges
distinguish new web research; absent lineage is explicitly unavailable.

For the original seeded demo only, set `VITE_API_MODE=mock` in an ignored
`.env.local` and restart Vite. Its Markdown export and localStorage are demo-only.
An HTTP failure never switches to mocks. The connection token and live case
content are never saved by the frontend to localStorage.
