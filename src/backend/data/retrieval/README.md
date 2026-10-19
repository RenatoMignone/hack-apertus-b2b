# Retrieval

Read-only strategy comparisons are available through `python -m backend.evaluation`.
Explicit lexical/dense/RRF modes do not call the reranker; lexical does not encode queries.
Default production behavior remains fused retrieval plus its configured reranker.
