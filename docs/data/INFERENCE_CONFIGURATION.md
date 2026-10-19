# Apertus inference configuration

Connected development uses **CSCS inference through Keera**, with an explicit
non-thinking **70B** setting for all reasoning tasks:

```dotenv
LLM_NAME=apertus-v1-5-70b
LLM_BASE_URL=https://gateway.keera.ch/api/v1
LLM_API_KEY=<private team key>
DEPLOYMENT_MODE=connected
```

Root [.env.example](../../.env.example) retains the required variable names.
Runtime configuration honors the selected alias without automatic switching.
Any small-model defaults/fixtures in code are not evidence of the active private
runtime; verify the startup `runtime.ready model=...` event.

| Gateway alias | Tool support |
| --- | --- |
| `apertus-v1-5-8b` | Tool-capable explicit alternative |
| `apertus-v1-5-70b` | Tool-capable selected connected model |
| `apertus-v1-5-8b-thinking` | Reasoning only; no tools |
| `apertus-v1-5-70b-thinking` | Reasoning only; no tools |

Use gateway aliases rather than HF artifact IDs. The transport appends
`/chat/completions` to the base URL once, using bearer authentication and explicit
system/user messages with non-streamed replies. Keera keys are private team
credentials; direct CSCS service credentials/URLs are not interchangeable.
[CSCS API documentation](https://docs.cscs.ch/services/inference/api/) describes
the compatible convention; actual gateway behavior must be tested separately.

## Structured tasks and tool execution

`models/reasoning/transport.py` handles requests and safe failure mapping.
`tasks.py` serializes compact context/schema, validates typed output and permits
bounded repair. Services perform interpretation, gap queries, extraction,
assessment, pack proposal, writing and wording assessment. Valid JSON does not
prove source support. LangGraph owns tool execution and branching through
LangChain adapters; model proposals cannot run arbitrary commands or broaden scope.
Thinking aliases are never supplied tools.

Persist task/model configuration and available served identity per run. A gateway
alias does not attest immutable weight revision. Record unknown revisions honestly.
Do not assume native JSON Schema, parallel tools, context length or embeddings
merely because the endpoint is OpenAI-compatible. Embeddings are a separate service.

## Verification and deployment

Authenticated synthetic probes and a real partial case/PDF have used Keera 70B;
see [verification](../judges/VERIFICATION.md). Earlier small-model probes are not
an overall benchmark or fallback policy. Representative accuracy, sustained
quotas, concurrency and deployment cost remain evaluation tasks.

The key stays backend-only, excluded from logs/traces and frontend variables.
Hosted inference requires connected mode. Offline requires separately provisioned
local Apertus serving/assets and disabled external access, with no hosted fallback.

Optional operator `leads` must occur literally in the input. A model-expanded name
that is not a literal quote is omitted from those annotations rather than failing
a clear request. The full original request and its constraints remain available;
this does not create public facts or relax claim/taxonomy validation. Safe
`model.validation_issue` events identify schema fields/types on actual failures.
