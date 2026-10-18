# Phase 1 — Ingestion, taxonomy and memory

**18 October 2026 · Implementation plan; nothing built or measured.**
Start with the [stacked visual diagrams](../architecture.html) and
[architecture/deployment contract](ARCHITECTURE.md). This plan owns the shared
records and memory interfaces. [Phase 2](OPERATIONS_PLAN.md) consumes them.

Initial stack to validate: Apertus v1.5 8B / optional 70B, BGE-M3, Weaviate,
BGE-reranker-v2-m3 and LangGraph. Endpoints, revisions, hardware, taxonomy
contents and corpus performance remain unverified. Code belongs in `src/`.

## 1. Pipeline and boundaries

```text
Domain profile + source registry
  → discover → scope/access checks → fetch raw bytes
  → extract/normalize → quality checks + exact evidence spans
       ├→ Apertus concept/entity/claim candidates → validation/entity resolution
       └→ original source chunks → BGE-M3 vectors
  → staged Weaviate hybrid index + canonical evidence/claim store
  → evaluate → immutable published snapshot
```

The collector preserves source content. Model enrichment is a separate recorded
derivation. Memory includes artifacts and claims as well as rebuildable indexes.
Case-specific company research reuses this pipeline in an isolated case scope.
Branding/template files and workshop transcripts are not research-corpus evidence.

## 2. Domain-independent configuration and precedence

The engine is reusable across medicine, robotics and other domains. A versioned
profile supplies sources/families, geography, languages, taxonomy/aliases,
optional entity/predicate extensions, validation/ranking settings and evaluation
fixtures. Never hardcode pilot concepts or institutions in core processing.
Changing domains may require re-enrichment and rebuilding RAG indexes; use the
[rebuild matrix](ARCHITECTURE.md#rag-rebuild-rules), not a second pipeline.

Current requirements still apply: Bern healthcare pilot, UniBE + ARTORG + DCB,
source-backed claims, purposeful Apertus use and deployment outside cantonal ICT.
The [pilot scope](../challenge/PILOT_SCOPE.md) owns medical focus and source seeds;
this plan owns shared contracts; [collection detail](../data/ingestion/INGESTION_SPEC.md)
owns deterministic acquisition. The YAML is a draft profile input, not proof of
live access or a working collector. Preserve the root template and `LLM_*` names.

## 3. Acquisition

- Import the [partner workbook](../provided_material/README.md): **42 actual rows**,
  including DCB, despite its Notes count of 71. Retain sheet/row/hash provenance;
  use the URL column, then verify hosts/redirects. Extend from links and sitemaps.
- Prioritize diabetes technology across all three required families, including
  UniBE beyond ARTORG. Additional organizations require evidenced Bern activity.
- Public HTML first, linked public PDFs next. Preserve original languages;
  English descriptions/translations are separate derivations.
- Enforce host/path/redirect/IP scope, robots and published restrictions, quotas,
  time/byte/retry budgets and shared-host rate limits. Public robots-allowed
  collection is authorized; no blanket manual approval for every origin.
  Actual ambiguity/blocks require review; redistribution remains separate.
- Save raw bytes, URLs, headers/MIME, timestamps, hashes, failures and discovery
  lineage. Source-family membership can overlap; downloads need not duplicate.

## 4. Extraction and faithful evidence

HTML/text-PDF parsers preserve headings, lists, tables, links, page/section maps
and language. Keep tables/media in sidecars where necessary. Scans require a
verified OCR adapter with quality/provenance flags; unsupported media stays
explicit. A model receiving an image does not establish native PDF-upload support.
Endpoint modalities remain unverified and are not prerequisites for this design.

Normalized body excludes generated metadata/summaries. Each literal span obeys
`body[char_start:char_end] == text` with Unicode offsets and exclusive end.
Keep extraction and raw versions distinct, including parser configuration.
OCR/visual transcription is a labeled derivation, not a guaranteed literal quote.

## 5. Versioned taxonomy

Review a small pilot vocabulary before accepting classifications. Each concept
has a stable ID/version, definitions/inclusions/exclusions, multilingual labels,
reviewed synonyms/ambiguous aliases, broader/narrower and separately related
concepts, optional external mappings with provenance/terms, and deprecation maps.

Use general facets: domain, capability, method/technology, application, service
and collaboration need. Location/affiliation remain sourced claims. Entity types
are person, unit, project, infrastructure, service and company; they are not
concept labels. Allow multi-label, ambiguous and unmapped content. Proposed new
concepts require review. Missing labels must not hide otherwise valid evidence.

## 6. Enrichment and validation

| Step | Input → output | Rules |
| --- | --- | --- |
| Classification request | Exact bounded passages + IDs/locators, metadata/hash, language and relevant fixed taxonomy definitions → `ClassificationRequest` | Source text is untrusted data; application owns instructions. Include neighboring context; record which sections were processed. |
| Apertus 8B | Request → document types, concept assignments, entity/claim candidates, missing fields and evidence-linked plain descriptions | Keep factual claims separate from lay explanations and suggested adjacent uses. Do not silently truncate or classify only a generated summary. |
| Mechanical checks | Candidate → schema/ID/label/span validation | Exact quotes and valid JSON do not establish semantic support. |
| Semantic/identity checks | Candidate + original context → accepted, unknown, conflict or needs_review | Explicit identifiers/compatible affiliations support merges; name similarity is insufficient. No invented contact, geography, clinical suitability or availability. |
| Bounded fallback | One repair attempt, unresolved ambiguity/conflict/context failure → optional 70B with the same evidence plus diagnostics | Apply identical checks; retain both derivations/routing reason. Unavailable 70B leaves explicit limitations/pending work. |
| Persistence | Validated output → separate derivation and claim records | Store model/prompt/taxonomy/settings, hashes, coverage, time and errors; preserve original evidence. |

Budget with the actual tokenizer/template. Do not equate a related concept with
a synonym or store a possible transfer as an existing project. Evaluate 8B-only
versus fallback on independently reviewed samples; model self-confidence is not
an acceptance signal.

## 7. Shared contract v1 — owned here, consumed by Phase 2

Implement typed schemas and JSON Schema exports in `src/`. Every record carries
`schema_version`; runs/manifests also pin `domain_profile_id` and
`domain_profile_version`. Core contracts are domain-independent; new domain
fields use versioned extensions. IDs are opaque to consumers; references must resolve within
the selected snapshot or its explicitly attached case evidence collection.

### 7.1 Records

- **Document:** `document_id`, `document_version_id`, `source_id`,
  `source_family_ids`, `source_kind`, `scope_id`, `access_policy_id`,
  `requested_url`, `final_url`, `language`, `title`, publication/update dates
  when present, `retrieved_at`, raw/body hashes, extraction/configuration versions,
  artifact paths, `quality_status`, warnings. Public web records require a source
  URL; approved case artifacts use an internal locator and never a fabricated URL.
- **EvidenceSpan:** `evidence_id`, document/version IDs, literal `text`,
  `char_start`, `char_end`, `heading_path`, page range, raw/media locator,
  `extraction_method`. Chunk context prefixes are separate from literal text.
- **Chunk:** `chunk_id`, document/version IDs, ordered evidence IDs,
  literal `text`, body offsets, title, heading path, source URL/page range,
  language, organization/location claim references, classification derivation
  IDs, validated topic labels, access/scope IDs, chunker/configuration hash,
  `context_prefix` and `embedding_text` kept separate from quoted evidence.
  A chunk is a contiguous body span; overlapping chunks do not create new facts.
- **EmbeddingRecord:** chunk ID, embedding-input hash, model/revision, tokenizer
  revision, dimensions, normalization/truncation policy, vector artifact hash,
  index-build ID and vector. Vectors are not source facts or classifier output.
- **ConceptAssignment:** subject document/entity ID, `concept_id`,
  `taxonomy_version`, `evidence_ids`, `mapping_kind` (direct/related),
  `validation_status`, derivation ID and ambiguity notes.
- **Entity:** `entity_id`, type, evidenced labels/aliases, claim IDs and
  source-family memberships. Locations and affiliations are claims, not defaults.
- **Claim:** `claim_id`, subject, predicate, object entity or literal value,
  `evidence_ids`, observed/source dates, validation/conflict status and derivation
  ID. Suggestions are stored separately from factual claims.
- **CaseMemoryRecord:** `case_id`, permitted summary, public company entity ID
  if resolved, needs, taxonomy assignments, selected entity IDs, outcome with
  date/evidence when known, access policy, review state and provenance. Missing
  outcomes stay unknown. Synthetic cases are explicitly labeled.
- **Derivation:** input IDs/hashes, model and prompt/configuration identifiers,
  taxonomy version, output hash, timestamps, validation status and errors.
- **SnapshotManifest:** `snapshot_id`, domain-profile/schema/taxonomy versions, included
  document/entity/claim IDs, index versions, embedding/tokenizer identifiers if
  used, source coverage/failures, snapshot date and artifact checksums.

### 7.2 Memory read interface

These are logical functions; an in-process implementation is sufficient.

```text
get_snapshot(snapshot_id | latest) -> SnapshotManifest
resolve_concepts(text, language, taxonomy_version) -> candidates + ambiguities
search_evidence(query_text, concept_ids, filters, snapshot_id, access_context)
    -> ranked EvidenceHit[] + coverage + warnings
search_entities(query_text, concept_ids, entity_types, filters,
                snapshot_id, access_context) -> ranked EntityHit[]
search_cases(query_text, concept_ids, filters, snapshot_id,
             access_context, exclude_case_id) -> ranked CaseHit[]
get_evidence(evidence_ids, snapshot_id, access_context) -> EvidenceSpan[]
get_entity(entity_id, snapshot_id, access_context) -> Entity + Claims
```

Every hit includes stable IDs, supporting evidence IDs, individual retrieval
scores, ranking-method version and limitations. Filters include source family,
language, geography, date and validation status. Access filtering happens before
ranking and before snippets are returned. Case similarity and expertise
relevance have separate score namespaces; neither is a probability of success.

Phase 2 resolves `latest` once per run, pins the returned snapshot and uses its
taxonomy version throughout. Unsupported schema versions fail explicitly.
Case-specific evidence is attached through an immutable case evidence manifest;
the run records both that manifest ID and the shared snapshot ID.

An `EvidenceHit` transfers `chunk_id`, document/version IDs, literal text,
evidence IDs/locators, source URL, language, supporting claim/entity IDs,
validation state, snapshot ID and separate hybrid/reranker score fields. The
consumer can fetch neighboring passages or full sections by ID without losing
the original passage. A claim is supported by its spans, not merely the hit rank.

Conversation turns additionally reference `case_id`, `input_revision_id`,
`result_revision_id`, parent revision, user instruction and affected filters or
selections. These belong to case state, never to the public source/taxonomy.
User edits can change emphasis or request further evidence; they cannot rewrite
the underlying evidence, create public facts or mutate shared snapshots.

### 7.3 Write and publication interface

```text
stage_documents(artifacts, provenance, scope_id, access_policy_id) -> ingest_job
enrich(ingest_job, taxonomy_version, model_config) -> validated records
stage_case_memory(reviewed_case_record, access_context) -> reviewable revision
publish(validated_records, index_config) -> immutable SnapshotManifest
```

Case operations do not mutate shared memory directly. Reviewed case records and
approved public research enter these same validation/publication interfaces.
Retain original evidence alongside summaries; generated output is never its own
sole factual source. Authorization revocation/deletion overrides historical
snapshot access and invalidates affected caches/index entries.

## 8. Memory implementation and indexing

### 8.1 Component ownership and persistent artifacts

Implement Python modules under `src/`. Raw files, full `clean.md`, page/table
sidecars, classification JSON, claims, taxonomy and embedding manifests remain
in the versioned artifact store. SQLite may retain crawl/job state, provenance
and manifests; it is no longer the proposed primary search database.

**Weaviate** stores searchable source chunks, metadata and externally generated
**BGE-M3** dense vectors. Its BM25F lexical index plus vector search provides
hybrid retrieval. Use bring-your-own vectors and explicit query vectors; do not
enable an unrelated default hosted vectorizer. BGE-M3's learned sparse and
multi-vector modes are not required for this initial design: Weaviate BM25F is
the lexical branch, BGE-M3 dense vectors the semantic branch.

**BGE-reranker-v2-m3** consumes query/passage pairs at retrieval time and emits
relevance scores. It does not generate corpus embeddings. **LangGraph** owns
bounded workflow state, transitions, follow-up questions and checkpoints; the
corpus remains in artifact storage/Weaviate. A checkpoint stores evidence IDs
and revisions, not an unversioned replacement copy of the knowledge base.

### 8.2 Data envelope passed between ingestion stages

Each stage emits a validated artifact and a small reference envelope:

```json
{
  "schema_version": "1.0",
  "ingest_run_id": "<run>",
  "document_id": "<stable-document>",
  "document_version_id": "<immutable-version>",
  "scope_id": "<public-or-case-scope>",
  "access_policy_id": "<policy>",
  "input_artifacts": [{"id": "<input-id>", "sha256": "<hash>"}],
  "output_artifacts": [{"id": "<output-id>", "sha256": "<hash>"}],
  "stage": "<normalize|classify|chunk|embed|index>",
  "configuration_hash": "<stage-config-hash>",
  "status": "<accepted|needs_review|failed>",
  "warnings": []
}
```

This is a shape illustration, not real output. Stages retrieve artifacts by ID
through authorized storage access. Send models actual bounded source text and
its locators; a local path or URL alone is not a model-readable document. Use
checksummed IDs rather than repeatedly passing raw binary files between workers.

The handoffs are:

1. **Fetch → normalize:** raw artifact ID/bytes, URL/headers/hash and fetch policy.
   Output full faithful body, metadata and page/section maps.
2. **Normalize → classify:** `ClassificationRequest` with contextual evidence
   spans and fixed taxonomy. Output separate validated classifications/claims.
3. **Normalize + validated enrichment → chunk:** body spans remain literal;
   attach topic/claim references only where supported. A document-wide label is
   not proof that every chunk expresses it. Missing/uncertain labels must not
   remove otherwise valid source text from search.
4. **Chunk → embed:** deterministic title/heading context plus original chunk
   text, its input hash and BGE-M3 configuration. Never embed only a classifier
   summary. Original DE/FR/EN (and IT where available) wording remains searchable.
5. **Chunk + embedding → Weaviate:** stable object identity, source text,
   provenance/filter metadata and one supplied dense vector. Validate every
   object acknowledgement and failed batch item before publishing a snapshot.
6. **Published snapshot → operations:** manifest/index-build IDs and section 7
   interfaces; no application consumer depends on storage-specific object shape.

### 8.3 Chunk and embedding preparation

Use heading/paragraph/page boundaries and contiguous offsets. Start around
400–650 BGE-M3 tokens with 60–100 overlap for long sections, as tunable initial
settings. Include title/heading context in the embedding budget. The model card
documents 1,024 dimensions and up to 8,192 tokens; validate the loaded revision
and configured serving limit instead of silently truncating to defaults.

Pin BGE-M3 revision, tokenizer, normalization and encoding settings for both
documents and queries. Reject dimension/non-finite-value mismatches. Record
reranker pair-token limits separately and reduce passage windows explicitly
with evidence offsets when necessary. Apertus has its own tokenizer/processor/
chat template for classification/synthesis; those counts are not interchangeable.

### 8.4 Weaviate representation and snapshot publication

Use a source-chunk collection per index build, or an equivalently isolated build
namespace. Each object has a deterministic UUID derived from the application
chunk ID and build identity, while retaining those IDs as properties. Store:

- `document_id`, `document_version_id`, `chunk_id`, `snapshot_id`/build ID.
- Original `text`, `title`, `heading_path`, language and body offsets.
- Source/final URLs, PDF page range, evidence IDs and artifact-manifest reference.
- Supported organization/location claim references and source-family IDs.
- Topic/document-type labels, their scope and classification validation state.
- Scope/access IDs, retrieval/source dates and extraction-quality status.
- Embedding model/revision/input hash and the supplied dense vector.

Configure BM25F over original text/title/heading properties, not opaque IDs,
hashes or generated summaries. Validate multilingual tokenization/analyzers on
German/French/English examples; test Italian as an extension. Configure vector
search for the matching dense space and explicit query-vector delivery.

Do not duplicate unbounded nested evidence graphs in each object. Resolve claim
references from the canonical store. Document DTO-to-Weaviate property mapping
and serialize compound fields explicitly rather than assuming arbitrary JSON
can be indexed. Distinguish source-extraction quality from enrichment quality:
valid source text with uncertain labels may be searchable, while unsupported
claims remain excluded from accepted results.

Build in staging; verify counts/checksums, references, vectors and hybrid smoke
queries before switching the application manifest pointer. No cross-store
transaction is assumed. Failed publication keeps the old snapshot and records
partial batch errors. All reads enforce the pinned build plus access policy;
revocation overrides historical access. Retiring a source removes its objects
from new builds while preserving permitted historical artifacts.

### 8.5 Information handed to agentic retrieval

LangGraph receives a `QueryPlan`: permitted original request, resolved company
context, user priorities/exclusions, conversational revision IDs, taxonomy
version, candidate concepts, explicit reliable filters, snapshot ID and budgets.
Keep original lay wording alongside scientific expansions and their origin;
generated expansion terms are hypotheses rather than company facts.

1. Embed the retrieval query with the pinned BGE-M3 configuration. Send both its
   original/contextual query text and dense vector to Weaviate hybrid search.
2. Retrieve 30 candidate source passages initially, with score metadata and
   provenance. Use reliable access/snapshot/explicit constraints as filters;
   classification labels are hints/boost signals, not mandatory topic filters.
3. Pass the contextual query plus each original passage to BGE-reranker-v2-m3;
   retain IDs and provenance in application state. Start with eight passages in
   the synthesis evidence pack, expanding if important support is missing.
4. Check support and coverage; optionally fetch neighboring sections or search
   again. Allow at most three retrieval rounds per run initially, plus time,
   token and model-call budgets. Ask the user a follow-up when a material
   ambiguity cannot be resolved from permitted context, then resume from a
   checkpoint. Do not keep cycling until a confident-looking answer appears.
5. Pass the frozen `ReportEvidencePack` defined in
   [ARCHITECTURE.md](ARCHITECTURE.md#evidence-pack-the-report-generation-gate) to
   synthesis: current intent/company facts, needs, accepted matches, argument
   derivations, optional numerical/case records, literal passages, locators,
   sources, conflicts, coverage and missing evidence. Use 8B initially; 70B is optional for difficult synthesis
   if access/resources permit. Validate answer claims against the pack.

Thirty candidates/eight context passages are initial passage budgets, not an
eight-entity result cap. Gather sufficient evidence to produce up to ten unique
experts/units for Recall@10; eight passages may support fewer or multiple entities.
If insufficient, use the bounded follow-up retrieval or disclose the limit.
Keep hybrid and reranker scores separate and never present either as a calibrated
probability. Labels cannot hide relevant unlabeled research groups.

### 8.6 Revision handoff back to memory

When the user requests a different focus, Phase 2 stores the instruction and a
new result revision. Formatting/emphasis changes reuse accepted evidence;
changed needs, exclusions or missing factual coverage produce an updated
`QueryPlan` and bounded retrieval. A user-suggested group is a retrieval lead,
not an accepted claim. Shared memory changes only through the reviewed Phase 1
publication interface. Never train or update taxonomy/embeddings automatically
from a conversational correction.

### 8.7 Technical references checked 18 October 2026

- [Apertus v1.5 8B model card](https://huggingface.co/swiss-ai/Apertus-v1.5-8B):
  model-family reference; no taxonomy-specific classification accuracy established.
- [Weaviate hybrid search](https://docs.weaviate.io/weaviate/search/hybrid):
  configurable BM25F/vector fusion.
- [Bring your own vectors](https://docs.weaviate.io/weaviate/starter-guides/custom-vectors):
  externally generated corpus/query vectors.
- [BGE-M3 model card](https://huggingface.co/BAAI/bge-m3): multilingual embedding
  modes, dimensions and context limits.
- [BGE-reranker-v2-m3 model card](https://huggingface.co/BAAI/bge-reranker-v2-m3):
  multilingual query/passage relevance scoring.
- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview):
  stateful orchestration, persistence and human interaction.

Capabilities in documentation do not establish performance on this taxonomy or
corpus. Pin actual packages/model revisions and verify deployment/license details
during implementation; no hosted inference URL is inferred from a model card.

## 9. Refresh and rebuild

Use conditional requests and hashes to skip unchanged work. Separate raw fetch,
normalized body, enrichment and index versions. Parser changes reuse raw bytes;
taxonomy changes trigger affected enrichment; embedding/chunker changes rebuild
compatible indexes. Preserve history and apply a configured permanent-unavailability
policy rather than retiring a source on one temporary failure. Revoke access in
historical builds/caches when required. See the architecture rebuild matrix.

Historical cases enter only through reviewed eligible records; no corpus is
supplied. Keep synthetic fixtures labeled. Generated reports cannot become their
own sole factual evidence or silently update shared taxonomy/embeddings.

## 10. Acceptance gates

1. Schemas/profile/registry validate; required families and missing prerequisites
   are explicit. No endpoint or taxonomy assumptions are invented.
2. HTML/public-PDF samples retain raw bytes, sidecars, exact spans and source
   provenance. Track fetched/extracted/enriched/indexed/rejected counts separately.
3. Independent checks cover synonyms, negation, ambiguous identity, missing
   fields, labels and supported claims. Review the 8B/70B routing policy.
4. Staged publication verifies IDs/checksums/vector inputs, dimensions, batch
   failures, access filters and cross-store references before switching snapshots.
5. Phase 2 can retrieve exact evidence with compatible query vectors. Freeze
   snapshot/taxonomy/query versions for [evaluation](../challenge/EVALUATION.md).
6. Exercise a second profile with fixtures and an index rebuild/rollback without
   changing core orchestration. Measure domain quality separately.

Use offline fixture tests for scope/redirects/robots, query parameters, encoding,
PDF/OCR flags, tables, prompt injection, offsets, duplicate content, conditional
requests, revocation and failed publication. Ensure unlabeled relevant text
remains retrievable, summaries never replace evidence, and edits reach retrieval.

## 11. Collection integration

The [collection spec](../data/ingestion/INGESTION_SPEC.md) now covers acquisition
only, not an alternative phase definition. Use code under `src/`, current pilot
families, config-driven source adapters and shared-host limits. Map any legacy
`version_id` to `document_version_id` at one typed boundary; preserve chunk IDs,
locators and sidecars. Never confuse source, enrichment and index versions.

## 12. Deployment and remaining inputs

The [architecture contract](ARCHITECTURE.md#target-architecture-mandatory) owns
component placement, the proposed air-gapped primary target, cloud alternatives,
dependency inventory and disconnected-run proof. No deployment has been tested.
Collection is connected; isolated case runtime must bundle models, evidence,
indexes, taxonomy/profile, UI and rendering assets without remote fallbacks.

Await the user's endpoint/hardware handoff, reviewed taxonomy and partner gold
examples. Historical-case data remains independently absent. Record actual
choices in [decisions](../project/DECISIONS_AND_OPEN_QUESTIONS.md).
