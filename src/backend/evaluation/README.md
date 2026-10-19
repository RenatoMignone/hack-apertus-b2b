# Retrieval evaluation

`python -m backend.evaluation --help` compares lexical, dense, RRF and optional
reranking against an existing authorized capture. The candidate suite has no gold
labels; independent expected typed entities are required for scores. Preserve pins,
source references, timing and failures; outputs stay in ignored private storage.

Read the [focused specification](../../../docs/challenge/EVALUATION.md) and [module map](../../../docs/plans/MODULE_HANDOFFS.md).
Coordinate shared DTO/schema/configuration changes with their consumers and run
relevant boundary checks against isolated infrastructure.
