# Hybrid retrieval adapters

Search the same authorized snapshot through independent lexical and vector
branches, fuse unique ranks with RRF, optionally rerank and expand bounded
supported context. Record actual query/evidence lineage and limitations.
Taxonomy keywords never exclude otherwise eligible dense matches.

Default runtime search isolates SQL branches with savepoints. A statement timeout
can retain the other branch with an explicit coverage limitation; both failing or
any non-timeout SQL error remains a failure. Explicit evaluation strategies never
silently degrade.

Read the [focused specification](../../../../docs/data/RETRIEVAL_SPEC.md) and [module map](../../../../docs/plans/MODULE_HANDOFFS.md).
Coordinate shared DTO/schema/configuration changes with their consumers and run
relevant boundary checks against isolated infrastructure.
