# Frontend workspace

Reserved for the browser UI. Framework, internal folders, styling, build system
and implementation are deliberately undecided; no frontend files are scaffolded.

The browser communicates exclusively through the backend's HTTP API. Start with
[frontend/backend handoff](../../docs/plans/FRONTEND_BACKEND_API.md) for proposed
routes, input/output views, polling, questions, revisions, review and downloads.
Agree the typed API before parallel UI/server implementation. Never connect the
browser directly to storage/models or expose backend credentials.
