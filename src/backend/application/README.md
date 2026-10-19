# Application services

Coordinates authorization, transactions, case/input/run lifecycle, queue leases,
reviews and exports. `bootstrap.py` / `factories.py` compose typed adapters. Worker
execution is separate from HTTP requests. Pure reads and lease renewal avoid
long mutation locks; writes retain ownership/revision checks.

Read the [focused specification](../../../docs/plans/OPERATIONS_PLAN.md) and [module map](../../../docs/plans/MODULE_HANDOFFS.md).
Coordinate shared DTO/schema/configuration changes with their consumers and run
relevant boundary checks against isolated infrastructure.
