# Workflow coordination

Own future LangGraph composition, small stage adapters, budgets, clarification
pause/resume, cancellation and recovery. Inputs: authorized command and pinned
run references. Outputs: durable stage results, questions and resource IDs.
Workflow ordering uses service ports, not HTTP handlers or embedded SQL.

Read [operations](../../../docs/plans/OPERATIONS_PLAN.md),
[case persistence](../../../docs/data/CASE_STATE_AND_LINEAGE.md) and
[processing boundaries](../../../docs/plans/REPORT_PROCESSING_BOUNDARIES.md).
Canonical stage records live in application PostgreSQL; checkpoints resume work.
Graph nodes for evidence preparation and report generation remain to be mapped.
