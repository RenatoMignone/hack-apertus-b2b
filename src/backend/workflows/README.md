# Workflow coordination

`graph.py:build_graph` compiles the executable LangGraph case pipeline. `nodes.py`
coordinates interpretation, blocking clarification and independent database/web
research. `evidence_nodes.py` joins results, persists canonical IDs, assesses support,
freezes the evidence pack and requests an assessed draft. Formatting edits reuse
the existing pack; focus/identity changes research again.

`execution.py` enforces the pinned deadline, cached stage outputs and safe tracing.
`research.py` wraps C's web discovery/fetch as LangChain tools and prefers pinned
corpus evidence when merging duplicate URLs. B owns model semantics; C owns
retrieval, source registration and provenance. Workflow ordering uses typed
service ports, without HTTP objects or embedded SQL.

`checkpoints.py` provides authorized sync/async PostgreSQL savers. The worker uses
server-created thread IDs, `interrupt`/`Command(resume=...)`, and durable application
outputs for recovery. Checkpoint setup is explicit; runtime startup never migrates.

Read [operations](../../../docs/plans/OPERATIONS_PLAN.md),
[case persistence](../../../docs/data/CASE_STATE_AND_LINEAGE.md) and
[processing boundaries](../../../docs/plans/REPORT_PROCESSING_BOUNDARIES.md).
Canonical stage records live in application PostgreSQL; checkpoints resume work.
The implemented [runtime handoff](../../../docs/team/runtime/HANDOFF.md) documents
limits, factories and tests. [Module handoffs](../../../docs/plans/MODULE_HANDOFFS.md)
separates graph work from models, tools, evidence/report services and HTTP.
Use LangGraph/LangChain for all agentic behavior; no SQL or framework HTTP objects
in nodes. Fixtures at service boundaries allow independent feature development.
