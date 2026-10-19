# Retrieval

Read-only strategy comparisons are available through `python -m backend.evaluation`.
Explicit lexical/dense/RRF modes do not call the reranker; lexical does not encode queries.
Default production behavior remains fused retrieval plus its configured reranker.


Full-text search uses constant language-specific tsqueries to avoid per-row parsing and enable GIN lookup where planner/RLS permit it and preserves max rank across ingestion projections. Membership RLS is optimized by migration 0012, preserving visible snapshots/owner/grants. SQL statements are bounded to 30 seconds. See [runtime feedback and rollout](../../../../docs/team/RUNTIME_FEEDBACK_AND_SEARCH.md).
