# Public-source ingestion

Implemented acquisition/build adapters; [current setup](../../../docs/data/LIVE_SETUP.md)
owns deployment gates. The [backbone handoff](../../../docs/team/backbone/HANDOFF.md)
records the original lane results.

- `normalize.py`: faithful HTML/public-PDF body, headings, exact Unicode/page
  spans and publication metadata. Scanned PDFs without text fail; no OCR.
- `registry.py`: idempotent sources/families and reviewed versioned vocabulary.
- `mesh.py` / `classification.py`: official MeSH categories/subcategories plus
  concrete subjects. At most three topic families, five specific subjects and
  four attributes each. Parents are derived, not extra topic slots. Meaning,
  negation and exact support matter; unknowns can remain unclassified.
- `pipeline.py`: exact-input embeddings, unchanged-input cache reuse, reviewed
  supported knowledge and explicit immutable publication; current application
  migration head is `0007_frontend_lifecycle`.
- `web.py`: robots-aware IP-pinned HTTP and Crawl4AI conversion without page JS.
  Discovery is explicitly configured; offline/unconfigured tools are unavailable.
- `searxng_discovery.py`: default keyless search through our private SearXNG JSON
  service, explicit engines, bounded replies, validated URL leads and partial-engine
  diagnostics. No browser needed; upstream blocking is still possible.
- `browser_discovery.py` / `browser_results.py`: optional DuckDuckGo HTML discovery
  through isolated Playwright Chromium, fixed search origin and validated links.
  Network acquisition reuses SafeHTTP; the rendering context is offline, with
  page JS/subresources disabled. CAPTCHA/blocks/changed markup are unavailable.
- `crawl4ai_markdown.py` / `crawl4ai_worker.py`: bounded conversion in a separate
  crawler venv, without backend secrets or dependency conflicts. No arbitrary
  commands, page scripts, LLM extraction or model downloads.
- `evaluation.py`: unique-entity, reviewed, intent-balanced Recall@10.

`python -m backend.ingestion --help` exposes collect, mesh-import, benchmark and
build. DB commands check schema, never migrate. Hosted embeddings use
`requirements.hosted.lock`; `local-models` remains optional. Default keyless research
uses the SearXNG sidecar and core HTTP client plus `requirements.crawler.lock` in
a dedicated venv; never combine it with the backend lock. `requirements.web.lock`
adds Playwright only for the optional browser adapter.
`EMBEDDING_BACKEND=hf` selects the same encoder as runtime queries and makes
`--model-path` unnecessary for benchmark/build. Supply the pinned tokenizer,
private HF token and shared verified JSON from the [HF handoff](../../../docs/data/HOSTED_EMBEDDINGS.md).
No confidential company-plan intake.

Follow [web setup and the independent public probe](../../../docs/data/WEB_RESEARCH.md)
to provision the browser/converter. Discovery returns URL leads; controlled fetch
produces source text and provenance. A search snippet cannot become evidence.

## Build manifest

`build --sources` reads a JSON list. Entries contain `observation` (relative path
to collect-output JSON), `origin`, `families`, `registry_ref`, and optional
`reviewed_claims`, `mesh_tags`, `specific_subjects`, `tag_reviewer`.

Reviewed claims contain supported `identity`, `entity_type`, `label`, `predicate`,
`reviewer`, exact `span`, and one `typed_literal` (`type`/`value`) or
`object_identity`. Relationship targets must already exist in the same scope.
MeSH tags contain `code` and `span` (`char_start`, `char_end`, `text`, optional
`heading_path`/`page`). Subjects contain `name`, `kind`, `span`, plus up to four
attributes with `name`, `value`, `span`. These do not create new MeSH branches
or additional schema entity types. Model suggestions stay pending until reviewed.

`--publish` is opt-in and requires reviewed support and all source families.

## Previous boundary

Bulk ingestion remains separate from the original case-data change. Case-time
fetching uses self-hosted Crawl4AI through LangChain tools and LangGraph, with a
separate URL discovery provider. [Web research](../../../docs/data/WEB_RESEARCH.md)
owns tool limits, source flags and deduplication. `data/repositories/research.py`
implements persistence and corpus URL preference, not a scraper/search service.
Use faithful normalized text, raw artifacts and exact spans via existing corpus
ports. Confidential company documents remain outside allowed intake.

## Parallel feature routing

[Module handoffs](../../../docs/plans/MODULE_HANDOFFS.md) lists this module's
focused read path, outputs and acceptance checks. [Active questions](../../../docs/project/OPEN_QUESTIONS.md)
own unresolved inputs. Implement scoped behavior against agreed contracts and
fixtures; coordinate shared schema/config changes. Leave `src/frontend/` untouched.
