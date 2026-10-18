# Reasoning adapter

Read [provider settings](../../../../docs/data/INFERENCE_CONFIGURATION.md) and
[model identity](../../../../docs/data/BUILD_AND_OPERATIONS.md). Default Keera ID
is `apertus-v1-5-8b`; preserve the `LLM_*` environment interface. Tool-selection
calls use non-thinking variants. Start with bounded non-streaming Chat Completions;
verify structured-output behavior with the team key before relying on it.

Inputs: task/schema version, permitted messages/context and allowed tool schemas.
Outputs: validated task result or validated tool proposal, usage and safe error.
Task DTOs are in `contracts/pipeline.py`; a general task port is not implemented
yet. Define that small interface with consumers before wiring it. LangChain owns
model adapters; LangGraph owns loops/tools. Add fixture tests for malformed JSON,
repair limits, auth/rate/timeouts, and forbidden tools on thinking models.
