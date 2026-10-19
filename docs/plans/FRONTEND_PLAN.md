# Browser application

React/TypeScript, Vite, Tailwind and Radix Themes implement the B2B interface.
HTTP is the default. `VITE_API_MODE=mock` selects a clearly scripted local demo;
HTTP failures never switch modes. Node 22.18+ is required.

| Route | Behavior |
| --- | --- |
| `/` | My desk: dark quick-start composer, recent cases and state-derived next steps |
| `/cases` | Clickable case board, search, research/review/pitch/closed status, hold/outcome controls |
| `/cases/new` | Permitted-text intake and examples |
| Case preparation | Immediate pending view while the server creates the case; prompt stays memory-only |
| `/cases/:id` | Draft/results, chat, source drawer, progress, read-only history and review/export |

My desk, board and workspace share `NavigatorApi`. Shared-server Connect holds a
bearer token only in memory; loopback access mode auto-connects using the server's
existing identity. Reload/reopening observes the durable run rather than creating
another one. Polling backs off when unchanged and aborts observation on navigation.

Chat distinguishes research/focus changes from wording-only rewrites. Blocking
questions support free text and exact durable question/run IDs. A draft retry can
reuse its pack. Source drawers show literal quotations, URL/date, corpus/web origin
and review status. Cards show only supplied source-backed metadata; optional
hierarchy/expertise fields are not fully populated by the backend. Direct/adjacent
labels and material caveats remain visible. Search diagrams use recorded lineage,
with a text/source fallback on small screens or missing links.

Review every card and keep one before export. HTTP uses exact-hash backend review,
queued rendering and authenticated download. Optional PPTX, manual plans and
own-case memory are capability-gated. Historical reports cannot mutate the current
revision. Demo browser PDF/PPTX and localStorage are explicitly separate fixtures;
HelioSense is the current hero scenario, not a live company-research result.

For setup use [quickstart](../judges/QUICKSTART.md); exact transport is in
[HTTP](FRONTEND_BACKEND_API.md). Frontend checks are `npm test` and `npm run build`.
