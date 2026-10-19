# Safe diagnostics

Timestamped allowlisted events describe stages, timing, counts and failure types.
Optional self-hosted Langfuse receives masked metadata through a bounded queue.
No prompts, source bodies, credentials or raw provider payloads enter traces.
Trace failure cannot block execution; traces are never fact/approval authority.

Read the [focused specification](../../../docs/data/OBSERVABILITY.md) and [module map](../../../docs/plans/MODULE_HANDOFFS.md).
Coordinate shared DTO/schema/configuration changes with their consumers and run
relevant boundary checks against isolated infrastructure.
