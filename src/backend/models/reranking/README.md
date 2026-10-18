# Reranking adapter

Read [retrieval](../../../../docs/data/RETRIEVAL_SPEC.md) and
[model/build configuration](../../../../docs/data/BUILD_AND_OPERATIONS.md).
BGE-reranker-v2-m3 is a candidate, not a resolved artifact or measured winner.

Implement `Reranker.score(query, passages)` from `contracts/data.py`, returning
one finite relevance score per passage in the same order. Respect pair/token
budgets, deterministic tie handling and explicit service errors. Reranking is
not a claim-entailment validator. It cannot change evidence text or permissions.
