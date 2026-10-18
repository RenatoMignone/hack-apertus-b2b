# Server settings and domain profiles

`settings.py` reads database/checkpoint/artifact settings and accepts an explicit
database URL for per-identity runtime bindings. `runtime.py:RuntimeSettings` reads
the HTTP/worker identity bindings, injected factories, profile, model endpoint,
budgets, CORS and optional local Langfuse settings. Secret fields are excluded from
representations. Runtime rejects hosted inference in offline mode and automatic
external LangSmith tracing. Individual B/C adapters must also enforce offline mode.

Root [.env.example](../../../.env.example) and the backend example contain public
Keera settings, a team-key placeholder and integrated factory/version fields.
Keep `LLM_NAME`, `LLM_BASE_URL`, `LLM_API_KEY`; an explicit alias is honored and
pinned per run. `EMBEDDING_CONFIGURATION` points to verified ModelConfiguration JSON;
`EMBEDDING_MODEL_PATH` contains already-provisioned local assets. Optional reranking
uses the equivalent `RERANKER_*` fields. These must match the published snapshot;
legacy model-name/dimension hints alone cannot configure an index. See the
[integration handoff](../../../docs/team/INTEGRATION.md).

`application.factories:{reasoning,backbone,web,pdf}` implements the shared loader
signature. Optional web needs explicit `BRAVE_API_KEY`, `WEB_USER_AGENT` and an
enabled factory; `WEB_ALLOWED_HOSTS` optionally narrows public targets. Offline
uses only loopback/`apertus`/`llm` endpoints and disables web. `RUNTIME_PDF_LOGO_PATH`
is explicit in the container; local examples assume commands run at repo root.

Read [provider settings](../../../docs/data/INFERENCE_CONFIGURATION.md),
[model/build configuration](../../../docs/data/BUILD_AND_OPERATIONS.md) and
[profiles](../../../docs/plans/ARCHITECTURE.md#data-independent-core-and-configurable-domain-profile).
Pin model/taxonomy/profile versions; do not copy source registries or secrets
into graph nodes. The config integrator coordinates new parsed keys and bootstrap
wiring; each feature documents what it requires. All credentials stay backend-only.
