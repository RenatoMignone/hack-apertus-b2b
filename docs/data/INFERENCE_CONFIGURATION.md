# Apertus inference: CSCS through Keera

**18 October 2026 · U9 supplied endpoint/model list; unauthenticated route checked.**
This owns provider connection details. [Model/build contracts](BUILD_AND_OPERATIONS.md)
own identity, compatibility and pinned configuration; [module handoffs](../plans/MODULE_HANDOFFS.md)
route implementation. No live inference adapter or authenticated test exists yet.

## Team connection

| Setting | Value |
| --- | --- |
| Provider / gateway | CSCS inference, through Keera Gateway |
| `LLM_BASE_URL` | `https://gateway.keera.ch/api/v1` |
| `LLM_NAME` | `apertus-v1-5-8b` (default) |
| `LLM_API_KEY` | Team-specific key, supplied privately after check-in |

Request the team key from **Sabine Wildemann on-site/Discord**, per the user-supplied
hackathon instructions. This is a team action; no message was sent by the agent.
Copy root [.env.example](../../.env.example) to an ignored `.env`, or use the
[backend developer example](../../src/backend/.env.example) for team-host tunnels.
Never put the key in frontend variables, committed examples, traces or screenshots.

| Keera served model ID | Tools | Intended routing |
| --- | --- | --- |
| `apertus-v1-5-8b` | Yes | Default typed interpretation/extraction/drafting and tool selection |
| `apertus-v1-5-8b-thinking` | No | Optional reasoning-only task; no tools/tool_choice supplied |
| `apertus-v1-5-70b` | Yes | Optional bounded fallback, configured explicitly |
| `apertus-v1-5-70b-thinking` | No | Optional reasoning-only fallback |

Use these exact gateway aliases, not Hugging Face artifact IDs. The direct CSCS
service has a different URL, model naming and key provisioning. Do not replace
the hackathon gateway with it or assume the keys are interchangeable.

## HTTP convention and examples

Use the OpenAI-compatible **Chat Completions** convention: bearer authorization,
`messages` with system/user/assistant/tool roles, explicit `model`, and
`stream: false` for the first adapter. SDK/framework base URL includes `/api/v1`;
append `/chat/completions` or `/models` exactly once. The convention is supported
by [CSCS's API documentation](https://docs.cscs.ch/services/inference/api/);
Keera-specific authenticated payload behavior still needs the team-key smoke test.
Do not assume `/responses`, native JSON Schema, parallel tools, streaming usage,
max context, token-count routes or embeddings from the base URL alone.

With `.env` already loaded into the process environment:

```bash
curl --fail-with-body --silent --show-error \
  "${LLM_BASE_URL%/}/models" \
  -H "Authorization: Bearer $LLM_API_KEY"
```

```python
# Reference request, not installed/wired application code.
import os
import httpx

response = httpx.post(
    os.environ["LLM_BASE_URL"].rstrip("/") + "/chat/completions",
    headers={"Authorization": "Bearer " + os.environ["LLM_API_KEY"]},
    json={
        "model": os.environ["LLM_NAME"],
        "messages": [
            {"role": "system", "content": "Answer briefly using supplied public context."},
            {"role": "user", "content": "What is a continuous glucose monitor?"},
        ],
        "stream": False,
    },
    timeout=60.0,
)
response.raise_for_status()
answer = response.json()["choices"][0]["message"]["content"]
```

The future LangChain adapter uses the same base URL/key/model (for example a
compatible chat client); LangGraph owns tool execution and branching. Validate
returned arguments and JSON with our contracts. A tool-call response proposes
work; the graph executes an allowed tool and returns a tool result. Never parse
or execute arbitrary code from model output. Thinking variants have no tools.
Endpoint JSON/grammar support must be measured before selecting a structured
output strategy; use bounded validation/repair rather than assuming it exists.

## Verification and deployment limits

- An unauthenticated GET to `/api/v1/models` returned **401** on 18 October 2026.
  This establishes route reachability/auth protection, not authorized model access.
- `/docs` and `/openapi.json` returned the Keera control-panel HTML shell, not a
  public OpenAPI schema; `/api/v1/openapi.json` returned 404. Public web search
  did not establish a separate gateway API specification. Treat CSCS examples
  as protocol guidance and the supplied Keera aliases as the hackathon authority.
- With a real team key, test model listing, one permitted chat, one harmless tool
  round trip on 8B, no-tool thinking behavior if used, typed-output reliability,
  errors/quotas and timeout/retry behavior. Do not print the key or full case text.
- Hosted Keera is a **connected runtime** dependency. The offline target needs a
  separately configured local Apertus server and packaged model assets; it cannot
  call Keera. Never claim the hosted configuration proves air-gapped operation.
- Gateway alias is a served identity, not an immutable weight revision. Record
  returned model/version information when available and label revision unknown
  until CSCS/organizers confirm it. No made-up commit hash or verified flag.

## Current parallel-build model comparison

The existing 8B default is a provisional baseline, not a benchmark-backed choice
over 70B. It is not a 7B model. For hosted connected reasoning, evaluate the supplied
70B alias first on extraction, semantic assessment and drafting; compare grounded
quality, schema reliability, latency and actual team quotas with 8B. Prefer 70B
when that measured trade-off fits the case budget. Both remain configurable via
LLM_NAME; only the runtime integrator changes shared defaults after the comparison.
No key-based benchmark or 70B performance advantage has been established here.
