# Observability adapters

Reserved for local Langfuse integration, safe correlation and stage/model/retrieval
observations. Inputs: allowlisted metadata and permitted masked payloads. Outputs:
bounded nonblocking trace delivery. Mask before callbacks/SDK receive content.

[Observability spec](../../../docs/data/OBSERVABILITY.md) owns this behavior and
self-hosted dependencies. Traces are diagnostics, never facts/checkpoints or case
completion requirements. No hosted tracing fallback, keys or SDK setup now.
