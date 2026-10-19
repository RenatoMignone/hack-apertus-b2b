# Durable workflows

`graph.py` compiles LangGraph; node services coordinate interpretation, parallel
DB/web research, registration, extraction, assessment, freezing and drafting.
`execution.py` enforces budgets/cached outputs; checkpoints resume server-created
threads. Formatting reuses the pack; focus changes research anew. No SQL in nodes.

When a follow-up round returns identical evidence records and entity context,
reuse the prepared claims/assessments, retain unresolved gaps and freeze a partial
pack. Changed passages/context still run preparation. If a draft already failed
against that evidence, unchanged research stops with rejection rather than
repeating generation. All retrieved records are still authorization-validated.

Read the [focused specification](../../../docs/plans/OPERATIONS_PLAN.md) and [module map](../../../docs/plans/MODULE_HANDOFFS.md).
Coordinate shared DTO/schema/configuration changes with their consumers and run
relevant boundary checks against isolated infrastructure.
