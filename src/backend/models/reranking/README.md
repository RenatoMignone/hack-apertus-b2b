# Cross-encoder reranking

Provision pinned assets/configuration explicitly. Score full intent against
original passages plus separate headings, using exact bounded windows and the
model’s own tokenizer. Record windows/scores; unavailable reranking retains RRF
with a limitation. Reranking does not alter source text or embedding space.

Read the [focused specification](../../../../docs/data/RERANKING.md) and [module map](../../../../docs/plans/MODULE_HANDOFFS.md).
Coordinate shared DTO/schema/configuration changes with their consumers and run
relevant boundary checks against isolated infrastructure.
