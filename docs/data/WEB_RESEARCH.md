# Case-local public web research

**18 October 2026 · U8/D16 design; persistence only, no live scraper/search adapter.**

## Selected approach and research

Recommend self-hosted [Crawl4AI](https://github.com/unclecode/crawl4ai) for Python
browser-backed page extraction and LLM-ready Markdown. Its README lists v0.9.5
(14 October 2026) and Apache-2.0 licensing. This is a suitability decision, not a
measured benchmark. [Scrapling](https://github.com/D4Vinci/Scrapling) is an
alternative with adaptive selectors, HTTP/browser fetchers and BSD-3-Clause
licensing. [Firecrawl](https://github.com/firecrawl/firecrawl) offers an integrated
API/service; its repository distinguishes AGPL-3.0 server code from cloud
features. No package is installed by this persistence-only change.
URL discovery is a separate `SearchProvider` port; do not assume installing a
scraper supplies an independent web index. Provider credentials/selection remain
a later integration input. Disabled adapters return explicit unavailable status.

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
manifest or its published snapshot; foreign-case, revoked, failed and unsupported
material is rejected. Offline mode records unavailable web research and continues
with the snapshot. Search timeouts can yield partial results without losing DB work.

## Model integration evidence

[LangChain structured output](https://docs.langchain.com/oss/python/langchain/structured-output)
distinguishes provider-native and tool strategies; endpoint support must be
verified. The [Apertus card](https://huggingface.co/swiss-ai/Apertus-v1.5-8B)
provides tool-call serving flags and states thinking-mode tool calling is
unsupported. Use non-thinking calls for tool selection. Future pauses use
[LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts).
These sources were checked on 18 October 2026; exact serving revisions remain open.
