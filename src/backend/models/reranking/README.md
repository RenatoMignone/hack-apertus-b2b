# Reranking adapter

`local.py` implements `LocalReranker.score` and local-files-only `load_reranker`.
It checks exact revision/runtime/tokenizer identity and per-pair token limits;
no silent truncation or implicit model download. Missing service availability is
explicit. The [lane handoff](../../../../docs/team/backbone/HANDOFF.md) lists gates.

Read [retrieval](../../../../docs/data/RETRIEVAL_SPEC.md) and
[model/build configuration](../../../../docs/data/BUILD_AND_OPERATIONS.md).
BGE-reranker-v2-m3 is a candidate, not a resolved artifact or measured winner.

The adapter implements `Reranker.score(query, passages)` from `contracts/data.py`, returning
one finite relevance score per passage in the same order. Respect pair/token
budgets, deterministic tie handling and explicit service errors. Reranking is
not a claim-entailment validator. It cannot change evidence text or permissions.
