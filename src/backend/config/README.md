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
`EMBEDDING_BACKEND=hf` uses `EMBEDDING_ENDPOINT_URL`, secret `HF_TOKEN`,
`EMBEDDING_MODEL_REVISION` and hash-checked `EMBEDDING_TOKENIZER_PATH`; local mode
uses `EMBEDDING_MODEL_PATH`. Both build and runtime use `load_configured`; hosted
mode is forbidden offline. [HF handoff](../../../docs/data/HOSTED_EMBEDDINGS.md)
owns the verified configuration. Optional reranking
uses the equivalent `RERANKER_*` fields. Embedding settings must match the live capture or published snapshot;
legacy model-name/dimension hints alone cannot configure an index. See the
[integration handoff](../../../docs/team/INTEGRATION.md).

`application.factories:{reasoning,backbone,web,pdf}` implements the shared loader
signature. Optional web uses a private SearXNG JSON service by default with
`WEB_DISCOVERY_PROVIDER=searxng`, `WEB_SEARCH_URL`, explicit `WEB_SEARCH_ENGINES`,
`WEB_USER_AGENT` and an enabled factory. No third-party API key or browser is
required for this default. The independent local sidecar uses a locally generated
`SEARXNG_SECRET` for its own cryptography, not a search subscription.
Optional provider `browser` uses Playwright;
`WEB_BROWSER_EXECUTABLE` optionally selects an absolute installed Chrome path;
otherwise provision Playwright Chromium. `WEB_CRAWL4AI_PYTHON` points to the
dedicated crawler venv, isolated because Crawl4AI and LangGraph currently require
incompatible xxhash versions. Install the separate web/crawler locks following
[web setup](../../../docs/data/WEB_RESEARCH.md). Explicit provider `brave` instead
requires `BRAVE_API_KEY`; there is no automatic provider fallback.
`WEB_ALLOWED_HOSTS` optionally narrows fetched sources, not the search service. Offline
uses only loopback/`apertus`/`llm` endpoints and disables web. `RUNTIME_PDF_LOGO_PATH`
is explicit in the container; local examples assume commands run at repo root.

Read [provider settings](../../../docs/data/INFERENCE_CONFIGURATION.md),
[model/build configuration](../../../docs/data/BUILD_AND_OPERATIONS.md) and
[profiles](../../../docs/plans/ARCHITECTURE.md#data-independent-core-and-configurable-domain-profile).
Pin model/taxonomy/profile versions; do not copy source registries or secrets
into graph nodes. The config integrator coordinates new parsed keys and bootstrap
wiring; each feature documents what it requires. All credentials stay backend-only.

`RUNTIME_CORPUS_MODE=live` retains Eric's per-case ready-evidence capture;
`published` retains the reviewed-release path. Both need the accessible domain
profile and matching encoder configuration. `RUNTIME_LIVE_TAXONOMY_ID` is only
needed when the profile lacks a taxonomy pin. See [live runtime](../../../docs/data/LIVE_CORPUS_RUNTIME.md).

[Local reranker setup](../../../docs/data/RERANKING.md) pins assets/runtime separately
from embeddings. Changing reranker weights does not re-encode the corpus.

`domain.py` validates a pinned profile’s `configuration.domain` vocabulary; it
does not filter vector eligibility. Optional flags `CASE_MEMORY_ENABLED` and
`RUNTIME_RICH_OUTPUTS_ENABLED` default false until maintainer migrations/assets.
`RUNTIME_PPTX_TEMPLATE_PATH` is an explicit deployment asset path.

`RUNTIME_CAPTURE_TIMEOUT_SECONDS` (default 30, range 1–120) bounds the synchronous
corpus-preparation SQL separately from the research deadline. Existing stricter
statement timeouts are preserved and command failures roll back. See
[capture performance](../../../docs/data/CAPTURE_PERFORMANCE.md).


Optional `RUNTIME_LOCAL_ACCESS=true` permits tokenless loopback testing with exactly one existing identity binding; shared deployments keep false. CLI rejects non-loopback binding and disables proxy-header trust. See [local access and runtime feedback](../../../docs/team/RUNTIME_FEEDBACK_AND_SEARCH.md).
