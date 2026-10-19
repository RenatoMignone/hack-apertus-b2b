# Public acquisition and builds

Controlled HTTP observations → faithful HTML/public-PDF text and exact spans →
canonical versions/chunks → compatible embeddings → reviewed knowledge and builds.
`python -m backend.ingestion --help` exposes collect, mesh-import, benchmark and
build. `review_cli` dry-runs decisions unless explicitly applied. Publication is
opt-in. Case-time tools never automatically publish shared facts.

Case-time page I/O uses three bounded concurrent tasks and deterministic result
ordering. SafeHTTP serializes requests per host, including robots and redirects;
concurrency does not bypass policy checks, request spacing or run budgets.

Read the [focused specification](../../../docs/data/ingestion/INGESTION_SPEC.md) and [module map](../../../docs/plans/MODULE_HANDOFFS.md).
Coordinate shared DTO/schema/configuration changes with their consumers and run
relevant boundary checks against isolated infrastructure.
