# Collection and normalization specification

**18 October 2026 · Collection reference; implemented subset and deferred crawler features distinguished below.**
This is the acquisition substage of [Phase 1](../../plans/INGESTION_PLAN.md), not
a competing phase definition. Start with the [visual reference](../../architecture.html).
The Phase 1 shared contract owns document/evidence/chunk schemas; this file owns
faithful extraction and crawl behavior. Code belongs under `src/`.
The [data-layer spec](../DATA_LAYER.md) owns PostgreSQL persistence and build gates.

Implemented now: explicit single-URL collection, safe HTTP, faithful HTML/text-PDF
normalization, registry/MeSH import, embedding benchmark and reviewed corpus build/
publication. See the [CLI README](../../../src/backend/ingestion/README.md).
Broad persistent crawling, conditional-fetch scheduling, OCR and generic portable
sidecar/JSONL packaging below remain design targets, not a claim of implemented
commands. Existing `ops.ingest_jobs` is not a persistent crawl frontier; the unused
frontier table was retired at 0005.

## 1. Inputs and source configuration

Load a versioned domain profile plus the draft [source registry](sources.yaml).
Do not hardcode Bern/diabetes/source selectors into the engine. Current source
priorities and verified discovery observations are in
[PILOT_SCOPE.md](../../challenge/PILOT_SCOPE.md). The partner workbook contains
42 actual URL rows; retain workbook/sheet/row/hash lineage. Seeds are discovery
candidates, not blanket access or completeness guarantees.

Per-source configuration:

| Group | Fields / behavior |
| --- | --- |
| Identity | Stable source ID, organization, required-family memberships, enabled/priority |
| Scope | Seeds, exact hosts, exact paths/path prefixes, deny patterns, language hints and content types |
| Adapters | Optional directory/link/parser/renderer adapter, selectors and version |
| Limits | Depth/page/PDF counts, bytes, requests/second, shared-host concurrency, timeout/retry/run budgets |
| Policy | Robots decisions, published restrictions, review status/reason/date and retention/redistribution notes |

One administrative document owner may have multiple source-family memberships.
Deduplicate downloads without losing institutional attribution. Do not count
ARTORG twice as all UniBE coverage. New domains/sources reuse these contracts.

## 2. Discovery and access

1. Seed a persistent bounded frontier from registry/workbook candidates.
2. Resolve relative URLs; normalize host/scheme/default ports/dot segments;
   drop fragments for fetch identity and configured tracking parameters.
   Preserve semantic queries such as language, institute IDs and PDF downloads.
3. Treat canonical tags as hints only. Keep distinct language URLs/documents,
   recording official alternatives without inventing translations.
4. Inspect robots for each origin and known published restrictions before
   content fetch. The user authorizes public robots-allowed collection; there
   is no blanket manual-per-origin approval gate. Actual ambiguity/blocks pause
   that origin for review. Permission to collect is not permission to redistribute.
5. Check allowed host/path, safe scheme/port and resolved destination IP before
   every request and redirect. Reject private/loopback/link-local targets and
   DNS-rebinding risks; the same policy applies to browser subrequests/assets.
6. Follow scoped links, downloads and sitemap entries under bounded traversal.
   Record unregistered external links as candidates; do not automatically fetch.
   Use a clear project-controlled user agent/contact. Honor Retry-After and
   stricter host rules; start around one request/second and two connections/host.
7. Stop on authentication, CAPTCHA, paywall or repeated blocking. No bypass or
   state-changing form submission. A renderer is an optional permitted extraction
   fallback, not a way around restrictions.

## 3. Fetch and raw preservation

- Record requested/final URL, redirect chain, status, headers/MIME/encoding,
  ETag/Last-Modified, timestamp, raw hash/size and errors/retries.
- Bound compressed/decoded bytes, redirects, time and attempts. Verify MIME and
  signature; an HTML error at a PDF URL is not a valid PDF.
- Save original bytes atomically before extraction. Preserve prior raw versions;
  persist frontier/job status for idempotent resumption.
- Use conditional requests; `304` reuses compatible stored artifacts. If raw
  bytes changed but normalized body did not, retain fetch history without
  inventing a new body version.
- Parser/config changes reprocess stored raw bytes without network. Retire a
  source only under a configured permanent-unavailability policy, not one
  transient failure; retain permitted history and explicit stale/error states.

## 4. Extraction and evidence

| Input | Processing | Output / limits |
| --- | --- | --- |
| HTML | Main-body extraction with headings, lists, links, tables and Unicode fidelity; remove navigation/cookie clutter | Body-only `clean.md`, page metadata, outlinks and diagnostics; generic parser plus explicit site adapters |
| Text PDF from public research source | Preserve reading order, page/section maps, text and tables | Page-located body/spans and table sidecars; flag unreadable/missing pages |
| Scanned PDF / image | Verified OCR adapter later, with engine/language/version and quality | Labeled derived text + page/image locator, not guaranteed literal original text; otherwise unsupported |
| Complex table/media | Preserve structured sidecar and raw locator | No fabricated cells or visual interpretation mixed into faithful body text |

Do not ask an LLM to rewrite, summarize, fill or translate canonical body text.
Model enrichment/visual interpretation is separate. Metadata absent from the
source is null; crawler `retrieved_at` is not the source's publication date.

Every evidence/chunk span uses Unicode character offsets into the **body**, not
front matter, with exclusive end and `body[start:end] == text`. Preserve page
ranges, headings and mapping to raw artifact/version. A chunk is contiguous;
embedding context prefixes are separate from quoted evidence.

Initial tunable chunk settings: 400–650 tokens, 60–100 overlap, respecting
paragraph/list/table/page boundaries. Phase 1 owns tokenizer/embedding settings.
Original language remains searchable; translations and summaries are derivations.

## 5. Artifacts and state

```text
controlled-data/                       # outside public artifacts unless licensed
  raw/<document>/<raw-version>/...
  normalized/<document>/<body-version>/clean.md
  normalized/<document>/<body-version>/metadata.json
  normalized/<document>/<body-version>/outlinks.json
  normalized/<document>/<body-version>/sidecars/...
  export/<run>/documents.jsonl
  export/<run>/chunks.jsonl
  export/<run>/manifest.json
```

Storage path is configurable; these are planned artifacts, not existing output.
PostgreSQL `corpus`/`ops` tables track sources, fetches, raw/body versions and
jobs. A durable crawl frontier/link inventory would need a separately implemented
contract; no separate SQLite state store is selected.
JSONL points to immutable artifacts, with optional literal text export.
Include sidecars/locators in portable packages. Validate typed schemas and hashes.
Legacy `version_id` maps to shared `document_version_id` at one adapter boundary.
Public web records require actual source URLs; never fabricate one for user text.

Outlinks retain href/anchor, referring page/version, scope and rejection reason.
A hyperlink is not proof of a real-world affiliation or collaboration.

## 6. Quality, safety and reporting

Measure body length, headings/links, parser warnings, duplicates, table failures,
PDF pages with text, OCR status and provenance completeness. Very short/boilerplate
content can trigger review; do not blindly delete valid short directory entries.
Differentiate extraction quality from later enrichment confidence.

Scraped text is untrusted data: never execute its instructions, change policies,
leak secrets or initiate arbitrary tools. Sanitize artifact paths. Limit retained
professional/personal content to relevant facts and recorded retention/rights.
Workshop transcripts, branding and confidential company plans are not crawl data.

Run manifest: versions/profile, dates, source IDs, artifact paths/checksums,
per-source failures, counts for attempted/fetched/extracted/new/updated/unchanged/
blocked/failed/needs_review/duplicate/index-eligible. Report actual counts only.
The UI must distinguish a failed source from no supported expertise.

## 7. Commands and acceptance scenarios

The working CLI exposes `collect`, `mesh-import`, `benchmark` and `build`
(with explicit `--publish`). Validation/dry-run, persistent bounded crawl/resume,
general offline reprocessing/export and audit commands remain later work.
Optional package/model assets belong in the dependency inventory; OCR and a
browser acquisition fallback are not implemented.

Use reusable offline HTML/PDF fixtures for:

| Scenario | Required behavior |
| --- | --- |
| Relative links / semantic queries | Resolve exactly; preserve content-bearing parameters; reject off-scope targets |
| Robots/terms ambiguity / redirect/IP safety | Record block/review and stop affected fetch; no bypass |
| 429/503 / 304 / timeouts | Bounded polite retry, compatible cache reuse and transparent failure |
| HTML error at PDF URL / broken parser | Explicit failed extraction, never synthetic successful content |
| HTML structure / PDF pages/tables | Preserve meaningful structure and exact citation reconstruction |
| German/French/other configured languages | Preserve original text/diacritics and language alternatives |
| Long pages / offsets / overlapping chunks | Contiguous spans, exact equality and deterministic IDs |
| Duplicate links / repeat runs / parser change | No duplicate versions; raw history preserved; offline reprocessing works |
| Injected instructions / unsafe paths | Inert source text and safe file boundaries |
| Export round trip | Reconstruct evidence, sidecars, metadata and source/version references |

Review representative samples across all required families, including public
PDFs where collected. Live smoke tests are additional evidence; fixture tests
must not require internet. Phase 1 then performs enrichment/index publication
and the domain-specific evaluation gates. This specification does not authorize
application implementation during a documentation task.
