# Application use cases

Own case/input/run operations, authorization, revision checks, reviews, selections
and export requests. Inputs: validated commands plus trusted caller identity.
Outputs: durable resource IDs/views. Use narrow repository/workflow ports;
HTTP response construction belongs to api, workflow ordering to workflows.

Read [case state](../../../docs/data/CASE_STATE_AND_LINEAGE.md) and
[API handoff](../../../docs/plans/FRONTEND_BACKEND_API.md). Persist stage outputs
idempotently; do not hold SQL transactions open during model/network calls.
Concrete use-case files and transaction tooling remain to be implemented.
