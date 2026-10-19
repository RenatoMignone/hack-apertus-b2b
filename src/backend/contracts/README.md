# Contracts and ports

`data.py` defines storage/search/model records; `pipeline.py` defines interpretation,
claim/assessment, pack and draft types; `services.py` defines async reasoning,
backbone, web and renderer interfaces. Preserve canonical IDs, exact provenance,
version/hash pins and typed errors. Contracts do not import concrete adapters.

Read the [focused specification](../../../docs/plans/SERVICE_CONTRACTS.md) and [module map](../../../docs/plans/MODULE_HANDOFFS.md).
Coordinate shared DTO/schema/configuration changes with their consumers and run
relevant boundary checks against isolated infrastructure.
