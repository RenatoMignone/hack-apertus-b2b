# Keyless search selection

18 October 2026. User requests a working alternative to challenged browser search.
Measurements below are bounded local tests, not guarantees about future engine
availability, exhaustive coverage or retrieval quality. No shared DB was touched.

## Decision

Use **our own SearXNG sidecar**, with explicit DuckDuckGo/Yahoo engines, behind the
existing LangChain discovery tool. Keep LangGraph orchestration, controlled
source fetching, isolated Crawl4AI conversion and provenance unchanged. Chrome
is not required by the default search path. SearXNG provides a maintained JSON
interface and aggregation; it does not remove upstream dependency or blocking.
Retain the already implemented DB retrieval branch when optional web fails.

```text
Public capability terms → LangChain tool → private SearXNG → ranked URL leads
  → controlled HTTP fetch → isolated Crawl4AI → case-local, unreviewed evidence
  → existing extraction/support assessment → report evidence pack
```

## Alternatives assessed

| Option | Fit / observation | Decision |
| --- | --- | --- |
| Change Chrome to Brave/another CLI | Our adapter's network acquisition uses SafeHTTP before browser rendering; replacing the browser alone does not change that blocked request | Not a fix for current failure |
| Raw DuckDuckGo/Brave HTML | DDG challenge; Brave HTTP 429 in earlier probes | Keep optional diagnostics; not default |
| DDGS metasearch library | Maintained multi-backend library, no key for supported scraping engines; still subject to their limits. Not installed or live-tested here | Viable smaller alternative, but SearXNG offers separately deployable JSON service and engine diagnostics |
| Private SearXNG | Local service and real relevant results passed; selected engines configurable | Selected, with failure reporting |
| Public SearXNG instances | Many disable JSON; availability and policies belong to another operator | Do not rotate through public instances as application infrastructure |
| Mwmbl own-index API | Keyless request returned HTTP 200 / 27 results in 9.13s; broad glucose results did not establish institution-specific coverage | Interesting optional source, not primary discovery |
| Institutional search/sitemaps/link crawling | ARTORG publishes UniBE's search form; actual direct ARTORG fetch works. Covers known domains without general-search dependence, but requires maintained discovery/indexing | Complement Eric's corpus pipeline; not unrestricted web search |
| Crawl4AI/Scrapling/Firecrawl alone | Fetch/extract known pages; this does not itself supply a broad independent search index. Crawl4AI's hosted search is a separate keyed service | Keep Crawl4AI for source processing |

## Local SearXNG experiment

An isolated loopback Docker instance used official image digest
`sha256:8bdd9aa136b2dc3b9332cf24714fa34a375b8a1949a1201ec900c24d7378596e`.
Only public research terms were sent. Engine checks for the same ARTORG/glucose
query: DuckDuckGo returned 10 results and Yahoo 7, with relevant institutional
links; Brave reported too many requests; Qwant access denied; Wikipedia returned
no results; Bing's 10 results were off-topic. The installed image did not expose
Mojeek, so its attempted selector fell back to defaults and is **not** a Mojeek
measurement. The deployed configuration therefore enables only DDG/Yahoo.

Combined-engine follow-ups:

| Public query | Latency | Results / inspected observation |
| --- | --- | --- |
| `site:artorg.unibe.ch adaptive diabetes management` | 1.14s | 10; expected ARTORG research page first |
| `Diabetes Center Berne research projects services` | 0.91s | 10; DCB projects page second |
| `University Bern glucose sensing research experts` | 0.63s | 10; DCB sensing/monitoring page first, UniBE department page fourth |

These three requests reported no engine errors. A subsequent real application
probe using the final sidecar reported a partial-engine failure but still returned
five ARTORG links, fetched three real pages and converted them through Crawl4AI
(1,300 / 1,734 / 139 characters), with content hashes and original observations.
`web_search_partial_engines` was retained in the tool output. This is an actual
discovery → fetch → conversion run, without synthetic search results or DB writes.
It is not a complete model-to-PDF acceptance run or a Recall@10 benchmark.

The updated full backend suite passed **211 tests**, no skips, using disposable
local PostgreSQL 17.11/pgvector; that test container was removed. The maintained
search sidecar remains local on port 18888. Earlier multi-engine evaluation
containers are temporary and removed after measurement. No shared DB, frontend
source or user deployment example was modified by this search task.

## Operations and remaining limits

[Web setup](WEB_RESEARCH.md) owns the actual configuration and repeatable probe.
Use only public query terms. No CAPTCHA solving, stealth/proxy rotation or paid
fallback is configured. HTTP 200 from SearXNG is insufficient: parse result and
engine error fields. Complete failure is unavailable, not a fabricated no-match.
Partial errors remain visible alongside usable fetched sources. Search snippets
are not evidence and source status remains unreviewed until the normal workflow.

Monitor and repeat a few known queries from the eventual worker host. If both
engines fail, continue with authorized corpus retrieval and an explicit web gap.
Only maintaining our own relevant index removes dependence on external search
providers; even then individual source websites may be unavailable.

## Primary references

- [SearXNG search API](https://docs.searxng.org/dev/search_api.html): JSON configuration, requests and public-instance limitations.
- [Open WebUI's SearXNG integration](https://docs.openwebui.com/features/chat-conversations/web-search/providers/searxng/): established agent/UI search integration using a private JSON endpoint.
- [LangChain SearXNG tool reference](https://reference.langchain.com/python/langchain-community/tools/searx_search/tool): existing ecosystem integration; our bounded adapter preserves this project's own ports.
- [SearXNG engine failures](https://docs.searxng.org/admin/settings/settings_search.html): CAPTCHA/access-denied/rate-limit suspension.
- [Official container deployment](https://docs.searxng.org/admin/installation-docker.html).
- [DDGS maintained backends and interface](https://github.com/deedy5/ddgs).
- [Crawl4AI SDK/self-hosted versus hosted capabilities](https://docs.crawl4ai.com/): hosted search requires its separate service.
- [Crawl4AI domain discovery](https://docs.crawl4ai.com/core/domain-mapping/): sitemaps and other domain-scoped sources.
- [Mwmbl official search implementation](https://github.com/mwmbl/mwmbl/blob/main/mwmbl/tinysearchengine/search.py): keyless v1 route and separate API-key handling for other routes.
