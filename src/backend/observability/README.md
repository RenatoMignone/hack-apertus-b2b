# Observability adapters

`tracing.py` implements local Langfuse integration, safe correlation and retrieval
observations. Inputs: allowlisted metadata. Outputs:
bounded nonblocking trace delivery. Mask before callbacks/SDK receive content.

[Observability spec](../../../docs/data/OBSERVABILITY.md) owns this behavior and
self-hosted dependencies. Traces are diagnostics, never facts/checkpoints or case
completion requirements. No hosted tracing fallback or committed keys.
See [deployment](../../../docs/data/DEPLOYMENT.md) for the optional service profile.

The runtime composition root injects this adapter when local Langfuse credentials
are configured. Workflow observations contain allowlisted IDs, stage, duration
and safe outcome fields; prompt/source text is never supplied to tracing callbacks.
See [runtime wiring](../../../docs/team/runtime/HANDOFF.md). The runtime also rejects
automatic external LangSmith tracing; a trace outage does not change a case result.

## Parallel feature routing

[Module handoffs](../../../docs/plans/MODULE_HANDOFFS.md) lists this module's
focused read path, outputs and acceptance checks. [Active questions](../../../docs/project/OPEN_QUESTIONS.md)
own unresolved inputs. Implement scoped behavior against agreed contracts and
fixtures; coordinate shared schema/config changes. Leave `src/frontend/` untouched.
