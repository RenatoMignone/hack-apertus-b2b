# Workflow coordination

`checkpoints.py` implements an authorized per-run PostgreSQL saver port. Future
LangGraph composition owns small stage adapters, budgets, clarification
pause/resume, cancellation and recovery. Inputs: authorized command and pinned
run references. Outputs: durable stage results, questions and resource IDs.
Workflow ordering uses service ports, not HTTP handlers or embedded SQL.

Read [operations](../../../docs/plans/OPERATIONS_PLAN.md),
[case persistence](../../../docs/data/CASE_STATE_AND_LINEAGE.md) and
[processing boundaries](../../../docs/plans/REPORT_PROCESSING_BOUNDARIES.md).
Canonical stage records live in application PostgreSQL; checkpoints resume work.
The agreed graph/stage behavior is in the processing contract; executable nodes,
state schema and service ports still need implementation. [Module handoffs](../../../docs/plans/MODULE_HANDOFFS.md)
separates graph work from models, tools, evidence/report services and HTTP.
Use LangGraph/LangChain for all agentic behavior; no SQL or framework HTTP objects
in nodes. Fixtures at service boundaries allow independent feature development.
