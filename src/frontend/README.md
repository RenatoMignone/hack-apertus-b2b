# Frontend workspace

Browser UI (Vite + React + TypeScript + Tailwind), currently running on **seeded
mock data**: it is not connected to the backend. Screens, data contract and demo
data are described in [FRONTEND_PLAN.md](../../docs/plans/FRONTEND_PLAN.md).

```text
npm install
npm run dev     # http://localhost:5173
npm run build
```

The UI talks to the backend only through the `NavigatorApi` interface in
`src/api/index.ts`, which `src/api/mockApi.ts` currently implements. To integrate,
implement it over the HTTP routes in
[frontend/backend handoff](../../docs/plans/FRONTEND_BACKEND_API.md); the two still
need to be reconciled. Never connect the browser directly to storage/models or
expose backend credentials.
