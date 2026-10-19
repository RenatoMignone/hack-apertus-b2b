# Case-local web research

Connected research runs beside database retrieval through LangGraph and LangChain
tools. **Private SearXNG discovers URLs; controlled HTTP fetch obtains original
content; isolated Crawl4AI converts sanitized content.** This path needs no Chrome
CLI or third-party search API key. It does require a private sidecar secret.

## Behavior

SearXNG is metasearch using explicit DuckDuckGo/Yahoo engines, not an independent
index. Partial-engine results retain a limitation; all-engine failure is unavailable,
not no-match. The adapter caches URL leads briefly (five minutes; 30 seconds for
partial results), not source evidence. Snippets are never factual support.

`SafeHTTP` enforces robots, public-address/IP-pinned requests, bounded redirects,
DNS/bytes/time and faithful normalization. Page scripts/subresources are not run.
Crawl4AI 0.9.5 performs bounded conversion in a subprocess, without backend secrets,
network retrieval or LLM extraction. A separate environment avoids its xxhash
constraint conflicting with LangGraph's lock.

Canonical deduplication prefers pinned corpus versions, including aliases. New
pages remain `origin=web`, `review_status=unreviewed`, case-scoped and subject to
literal and semantic assessment. `FetchedSource` includes title, requested/canonical
URL, content/hash, fetched date and nullable publication date. Fetch time is not
publication time. No automatic shared-corpus promotion occurs.

## Provision

```bash
uv venv .local/crawl4ai-venv --python .venv/bin/python
uv pip install --python .local/crawl4ai-venv/bin/python -r src/backend/requirements.crawler.lock
```

Do not install that lock into the backend environment. Configure privately:

```dotenv
RUNTIME_WEB_FACTORY=backend.application.factories:web
WEB_DISCOVERY_PROVIDER=searxng
WEB_SEARCH_URL=http://127.0.0.1:18888
WEB_SEARCH_ENGINES=duckduckgo,yahoo
WEB_USER_AGENT=BernExpertiseNavigator/0.1 (HackApertus public research)
WEB_CRAWL4AI_PYTHON=/absolute/repo/.local/crawl4ai-venv/bin/python
SEARXNG_SECRET=<private random sidecar secret>
```

Run `make docker` or `make all` after dependencies/settings exist. SearXNG binds
loopback; never publish its unauthenticated JSON endpoint. A containerized worker
needs a private network and `WEB_SEARCH_URL=http://searxng:8080`; host paths and
loopback do not automatically work inside containers.

```bash
.venv/bin/python -m backend.ingestion.check_web --env-file src/backend/deploy/.env --query "ARTORG glucose sensor research Bern"
```

This explicit public probe uses no DB/corpus or model call. Restart API/worker after
configuration changes. An empty web factory disables web; the limitation remains
visible. Offline mode forbids it.

## Budget and alternatives

Default: ten page attempts per round, eleven total tool operations per run
(discovery plus attempted pages). Follow-up rounds share that budget; failed fetches
consume it. Ten is a bounded model/context choice, not a search-engine limit.
Time, text and model-token limits still apply. The graph finalizes partial supported
work when resources are insufficient.

The optional `browser` adapter uses provisioned Playwright/Chromium and
`requirements.web.lock`; live DuckDuckGo HTML encountered an anti-bot challenge.
The `brave` adapter needs `BRAVE_API_KEY`. Neither is an automatic fallback.
CAPTCHA/HTTP blocks/timeouts are unavailable; no challenge bypass or public-instance
rotation is used. SearXNG live pilot queries returned leads, but combined real
DB/web report quality remains a separate [acceptance](../judges/VERIFICATION.md).
