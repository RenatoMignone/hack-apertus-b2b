# Case-local public web research

**18 October 2026 · Private keyless SearXNG discovery and isolated Crawl4AI conversion.**

## Selected approach and research

The current implementation is `ingestion/web.py`: robots-aware, IP-pinned public
HTTP acquisition, redirect/DNS/byte/time limits and faithful normalization.
Crawl4AI converts sanitized extracted content to Markdown; page JavaScript and
browser subresources are not executed. This is narrower than a browser crawler.
`SearXNGDiscovery` is now the default: the worker calls our own loopback/private
SearXNG JSON service with explicit DuckDuckGo and Yahoo engines. Search does not
require Chrome, a browser CLI, a subscription or third-party API keys. The service
is metasearch, not an independent index: upstream engines can still fail. Valid
results from an available engine continue with `web_search_partial_engines` when
other engines fail; all-engine failure is unavailable, not no-match. Search snippets
remain URL leads, never factual evidence.
Per-adapter repeated public queries reuse URL leads for five minutes (30 seconds
for partial results), bounded to 128 entries. Source bodies are fetched again;
this is not an evidence cache or a shared-corpus update.

The research and bounded live comparison are in [search evaluation](WEB_SEARCH_EVALUATION.md).
The separate `browser` provider remains a diagnostic alternative: it renders
DuckDuckGo HTML in isolated Playwright/Chrome but encountered a live challenge.
The `brave` provider remains an explicit key-based alternative. There is no hidden
switch between these three configured providers and no public-instance rotation.

Crawl4AI **0.9.5** runs in a separate conversion venv: it requires `xxhash<4`,
whereas locked LangGraph requires `xxhash==4.0.1`. The worker accepts only bounded
sanitized HTML/base URL and returns Markdown through JSON/stdin/stdout. It receives
no backend credentials, does no fetching/LLM extraction, and has a 20-second
subprocess timeout. The parent retains raw fetch observations and provenance.
This also fixes the real Crawl4AI method argument (`input_html`, not `cleaned_html`).
This is controlled acquisition/conversion, not unrestricted JavaScript crawling.

CAPTCHA, HTTP blocking, missing browser/worker assets, changed result markup and
timeouts return unavailable. Only a recognized no-results page returns an empty
result set. Do not use stealth, proxy rotation or challenge-solving fallbacks.

The earlier selection considered [Crawl4AI](https://github.com/unclecode/crawl4ai),
[Scrapling](https://github.com/D4Vinci/Scrapling) and
[Firecrawl](https://github.com/firecrawl/firecrawl). Package/license observations
were dated 18 October; this audit did not recheck vendor versions or terms.
Optional web packages need target-platform runtime checks. Lane C collected
three pilot pages; no exhaustive crawl, configured live discovery or integrated
provider run is claimed. [Collection observations](../team/backbone/RESULTS.md)
retain that limited scope.

## Provision and enable

From the repository root, with the backend venv already prepared:

```bash
uv venv .local/crawl4ai-venv --python .venv/bin/python
uv pip install --python .local/crawl4ai-venv/bin/python -r src/backend/requirements.crawler.lock
```

The crawler lock is an independent Python 3.13/Linux resolution, **not** a
supplemental backend lock. Never install it into the backend venv. Hosted
embeddings still need their existing supplemental lock. Verify both environments
with `uv pip check --python <their-python>`. No browser assets are needed for
SearXNG discovery or the conversion-only worker. Deploy the sidecar and crawler
interpreter on the backend worker host; the core runtime image does not include
them. For a containerized worker, attach it to the search service's private network
and use `http://searxng:8080`; host loopback is only for a host-run worker.

Private env configuration:

```text
RUNTIME_WEB_FACTORY=backend.application.factories:web
WEB_DISCOVERY_PROVIDER=searxng
WEB_SEARCH_URL=http://127.0.0.1:18888
WEB_SEARCH_ENGINES=duckduckgo,yahoo
WEB_USER_AGENT=BernExpertiseNavigator/0.1 (HackApertus public research)
WEB_CRAWL4AI_PYTHON=/absolute/repository/.local/crawl4ai-venv/bin/python
SEARXNG_SECRET=<generate a private random value locally>
```

`SEARXNG_SECRET` is the local service's cryptographic secret, not a provider API
key. Generate it with Python `secrets.token_hex(32)` and store it directly in the
ignored env without printing it or replacing existing secrets. The supplied Compose
requires it. Start only this independent local service:

```bash
docker compose --project-name navigator-search --env-file src/backend/deploy/.env \
  -f src/backend/deploy/search.compose.yaml up -d
# Stop only this sidecar when no longer wanted:
docker compose --project-name navigator-search --env-file src/backend/deploy/.env \
  -f src/backend/deploy/search.compose.yaml down
```

The image is pinned to the tested digest. It binds only to loopback, enables JSON,
and disables its own bot limiter because it is a private backend service. Do not
publish this unauthenticated endpoint to the Internet. It requires no DB/model
credentials and cannot access the evidence DB. No query logging/personal browser
session is part of the application interface. `WEB_ALLOWED_HOSTS` optionally limits
source fetches, not the explicitly configured search service.

Optional browser diagnostics instead require `WEB_DISCOVERY_PROVIDER=browser`,
`requirements.web.lock` and provisioned Playwright Chromium or an absolute
`WEB_BROWSER_EXECUTABLE` (e.g. `/usr/bin/google-chrome`). The browser sandbox stays
on. Explicit `WEB_DISCOVERY_PROVIDER=brave` needs `BRAVE_API_KEY`. Restart API/worker
together with matching settings before starting new runs.

Independent opt-in probe, requiring no DB, model call or corpus publication:

```bash
.venv/bin/python -m backend.ingestion.check_web --env-file src/backend/deploy/.env \
  --query "ARTORG glucose sensor research Bern"
# Probe crawling separately when a search service blocks discovery:
.venv/bin/python -m backend.ingestion.check_web --env-file src/backend/deploy/.env \
  --url https://www.artorg.unibe.ch/research/aihn/research_activities/adaptive_diabetes_management/index_eng.html
```

The probe emits status, public URLs/titles, content lengths/hashes and limitations;
it does not persist sources or send company prompts. Query terms must be public.
The application still requires authorized corpus evidence and a matching profile.
In `RUNTIME_CORPUS_MODE=live`, Eric's per-case ready-evidence capture replaces the
published-snapshot prerequisite; see [live corpus runtime](LIVE_CORPUS_RUNTIME.md).

## Apertus research budget and manual UI testing

Default: **10 candidate URLs per round**, **11 tool operations per run**
(`RUNTIME_MAX_TOOL_CALLS=11`). Discovery consumes one operation; every attempted
page consumes another. The default run therefore attempts at most ten pages total,
including follow-up rounds. Repeated searches leave fewer page slots; failed
fetches also count. Restart API/worker and create a new run to use updated budgets.

The URL cap does not guarantee model fit. Corpus passages and instructions also
consume context. Existing Apertus guards reject calls exceeding **80,000 input
characters** and cap output at **4,096 tokens**. No silent truncation occurs.
The character guard is not an exact token count or a measured quality threshold;
ten long pages can still exceed it after joining corpus evidence. Evaluate
passage selection/batching before raising limits. The current private model
selection remains non-thinking Apertus 70B; no model fallback is introduced.

From repository root, with the SSH tunnel and private configuration ready:

```bash
.venv/bin/python -m backend.deploy.check_runtime --env-file src/backend/deploy/.env --network
# Terminal 1: API
.venv/bin/navigator-runtime --env-file src/backend/deploy/.env serve --host 127.0.0.1 --port 8000
# Terminal 2: worker; coordinate shared queue ownership with Eric first
.venv/bin/navigator-runtime --env-file src/backend/deploy/.env worker
# Terminal 3: existing frontend
cd src/frontend
npm run dev
```

Start the search sidecar using the earlier Compose command if necessary. Open
`http://localhost:5173`, Connect using the local bearer token stored at
`.local/runtime-acceptance/browser-token` (never a model key), create a case and
enter permitted company context/objectives. Chat refines an existing case. Vite
proxies `/api` to port 8000. Keep HTTP mode; explicit mock mode uses synthetic data.

**Current runtime:** the private environment now uses Eric's live corpus mode and
updated principal/profile binding. Publication is optional while ingestion
continues; each case pins its ready-evidence capture. HF query/document encoding
passed (HTTP 200, 768d). Restart API and worker to load the updated private env.
Full real-provider case-to-PDF remains an acceptance check. The independent web
probe and synthetic UI smoke are narrower tests.

## Earlier browser implementation verification — 18 October 2026

- Full backend suite: **194 passed**, no skips, on a dedicated disposable
  PostgreSQL 17.11/pgvector container. It was removed after testing; the shared
  server was not used for tests. Both separate Python environments pass dependency
  consistency checks. These are engineering tests, not research-quality scores.
- Actual sandboxed Google Chrome rendered a synthetic discovery page and returned
  validated URLs. Isolated Crawl4AI converted a synthetic paragraph successfully.
- Actual public ARTORG adaptive-diabetes-management fetch plus Crawl4AI conversion
  completed with **1,300 characters**, a content hash and original observation.
  A LangChain tool smoke joins real Chrome with a synthetic search-result lead
  to that real controlled fetch/converter. No DB registration occurred.
- Live keyless search did **not** pass: DuckDuckGo returned a challenge (HTTP 202
  on a separate diagnostic) and the browser adapter reported unavailable. Brave
  Search also returned HTTP 429 on a preliminary connection check. No challenges
  were bypassed and no hidden provider fallback was used. Actual search-result
  availability from this network remains an operational gate.
- At that checkpoint the private local env enabled the browser factory, installed Chrome path and
  crawler interpreter. The user's deployment `.env.example` is preserved exactly;
  no frontend file, schema, corpus publication or shared service was changed.

Implementation references: [Playwright browser provisioning](https://playwright.dev/python/docs/browsers),
[isolated contexts](https://playwright.dev/python/docs/browser-contexts),
[request routing/service workers](https://playwright.dev/python/docs/network), and
[DuckDuckGo HTML robots policy](https://html.duckduckgo.com/robots.txt).

## Tool contract

LangChain tools expose discovery and controlled fetching; LangGraph owns routing,
parallel DB/web execution, joins and bounded follow-ups. Page tools accept only
public HTTP(S) targets, recheck redirects/DNS against private/internal addresses,
respect access rules and bound bytes/pages/time. Treat fetched content as data,
not instructions; never give a page tool authority to write shared corpus facts.
Only minimal public research terms leave the runtime, not full case prompts.

`FetchedSource`: title, requested URL, canonical URL, normalized content,
`fetched_at`, nullable `published_at`, SHA-256, origin=`web`, and
review_status=`unreviewed`. Retain raw/normalized artifact refs, parser identity,
fetch outcome and extraction spans when storing it. The literal source body
must support every quotation; discovery snippets alone are ineligible.

## Merge and eligibility

Normalize HTTP(S) scheme/host/default ports, remove fragments and known tracking
parameters, retain meaningful query parameters, and use known aliases/final
redirect URLs. Do not collapse HTTP and HTTPS or unrelated query variants by guess.
Look up duplicates in the **whole eligible pinned snapshot**, not only search
hits. If duplicate, retain corpus version; record duplicate/freshness diagnostics
in the research result. No silent snapshot refresh or automatic global ingestion.

Store new pages in a writable, case-owned scope. Source provenance, source-review
status and claim support status are separate. A new source remains visibly
unreviewed even after a claim is supported. Flag-and-allow: a supported claim may
enter the draft without prior human source approval. Editorial selection does
not certify the source or promote it to the shared corpus. Contradictory/stale
material stays explicit, never silently wins because of retrieval rank.

A run pins an immutable case evidence manifest. Pack support must come from that
manifest or its pinned published/live corpus capture; foreign-case, revoked, failed and unsupported
material is rejected. Offline mode records unavailable web research and continues
with the snapshot. Search timeouts can yield partial results without losing DB work.

## Model integration evidence

[LangChain structured output](https://docs.langchain.com/oss/python/langchain/structured-output)
distinguishes provider-native and tool strategies; endpoint support must be
verified. The [Apertus card](https://huggingface.co/swiss-ai/Apertus-v1.5-8B)
provides tool-call serving flags and states thinking-mode tool calling is
unsupported. Use non-thinking calls for tool selection. Implemented clarification pauses use
[LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts).
These sources were checked on 18 October 2026; exact serving revisions remain open.
