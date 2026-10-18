# Application use cases

Own case/input/run operations, authorization, revision checks, reviews, selections
and export requests. Inputs: validated commands plus trusted caller identity.
Outputs: durable resource IDs/views. Use narrow repository/workflow ports;
HTTP response construction belongs to api, workflow ordering to workflows.

Read [case state](../../../docs/data/CASE_STATE_AND_LINEAGE.md) and
[API handoff](../../../docs/plans/FRONTEND_BACKEND_API.md). Persist stage outputs
idempotently; do not hold SQL transactions open during model/network calls.
Concrete use-case files and transaction tooling remain to be implemented.

## Parallel feature routing

[Module handoffs](../../../docs/plans/MODULE_HANDOFFS.md) lists this module's
focused read path, outputs and acceptance checks. [Active questions](../../../docs/project/OPEN_QUESTIONS.md)
own unresolved inputs. Implement scoped behavior against agreed contracts and
fixtures; coordinate shared schema/config changes. Leave `src/frontend/` untouched.
