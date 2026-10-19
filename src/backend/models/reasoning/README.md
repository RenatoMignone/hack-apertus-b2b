# Apertus reasoning

Transport uses explicit Keera/base URL/key/model configuration. Structured task
services serialize compact context/schema, validate outputs and repair within
bounds. Interpretation, extraction, support and wording have separate tasks.
LangGraph owns agentic loops; the adapter cannot execute arbitrary tools.

Read the [focused specification](../../../../docs/data/INFERENCE_CONFIGURATION.md) and [module map](../../../../docs/plans/MODULE_HANDOFFS.md).
Coordinate shared DTO/schema/configuration changes with their consumers and run
relevant boundary checks against isolated infrastructure.

Optional private receipts distinguish model calls from validation/repair events,
with run IDs, attempt numbers, timing and token usage. They exclude prompts and
response bodies. A failing diagnostics callback never blocks application work.
