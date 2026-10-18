# Apertus reasoning adapter

Implemented in lane B against A's service contracts `77bf4f8` + `1216c23`.
See the [merged integration](../../../../docs/team/INTEGRATION.md); the
[original B handoff](../../../../docs/team/intelligence/HANDOFF.md) retains provenance.

`KeeraChatModel` is an async LangChain model using bounded non-streaming Chat
Completions through injected HTTP transport. `ModelSettings` defaults to the
supplied Keera URL and 8B alias; `application.factories` injects `LLM_NAME`, `LLM_BASE_URL`, `LLM_API_KEY`.
No env-file loading, hard-coded secrets, automatic model fallback or database work.
Remote inference is unavailable offline; explicit loopback/local serving is allowed.

`StructuredTasks.run` sends a fixed task/schema, validates output and references,
and permits one repair with sanitized validation diagnostics. No native JSON Schema
support is assumed. `propose_tools` validates only allowed function names/arguments
and returns proposals; A's LangGraph owns execution. Thinking aliases reject tools.
Requests, retries, input characters, reply bytes, output tokens and deadline are
bounded. An optional verified input-token limit requires A's matching chat-template
token counter; characters are not claimed as tokenizer counts.

Credentials and provider bodies stay out of errors; tracing is disabled inside
the adapter. Optional receipts contain only task/model, timing and usage. The
explicit `FixtureChatModel` is for tests/demo injection and is never a real-mode
fallback. Cancellation propagates; a direct LangChain adapter invocation avoids
the installed core's cancellation aggregation bug and hidden tracing/cache paths.

Core dependencies are in the shared manifest/lock. Run focused tests
with `PYTHONPATH=src python -m pytest src/backend/tests/intelligence -q`.
The opt-in `backend.tests.intelligence.benchmark` uses synthetic non-confidential
fixtures only; [comparison findings](../../../../docs/team/intelligence/MODEL_COMPARISON.md)
record limitations rather than claiming model quality.
