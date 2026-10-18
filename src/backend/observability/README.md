# Observability adapters

`tracing.py` implements local Langfuse integration, safe correlation and retrieval
observations. Inputs: allowlisted metadata. Outputs:
bounded nonblocking trace delivery. Mask before callbacks/SDK receive content.

[Observability spec](../../../docs/data/OBSERVABILITY.md) owns this behavior and
self-hosted dependencies. Traces are diagnostics, never facts/checkpoints or case
completion requirements. No hosted tracing fallback or committed keys.
See [deployment](../../../docs/data/DEPLOYMENT.md) for the optional service profile.
