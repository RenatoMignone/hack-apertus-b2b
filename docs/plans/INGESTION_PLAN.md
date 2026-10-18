# Phase 1 — Ingestion, taxonomy and memory

**18 October 2026 · Collection/build design; PostgreSQL persistence implemented, live acquisition/model adapters pending.**
Start with the [stacked visual diagrams](../architecture.html) and
[architecture/deployment contract](ARCHITECTURE.md). This plan owns the shared
records and memory interfaces. [Phase 2](OPERATIONS_PLAN.md) consumes them.

Selected stack: PostgreSQL + pgvector, LangGraph PostgreSQL checkpoints and
self-hosted Langfuse; Apertus v1.5 8B / optional 70B, EmbeddingGemma 2 candidate
and BGE reranking. U9 supplies Keera aliases/base URL and the EmbeddingGemma 2
reference; exact revisions/runtime packages, measured hardware and actual reviewed
taxonomy remain open. [Data-layer specs](../data/DATA_LAYER.md) own physical
implementation; this plan owns logical contracts. Code belongs in `src/`.

## 1. Pipeline and boundaries

```text
Domain profile + source registry
  → discover → scope/access checks → fetch raw bytes
  → extract/normalize → quality checks + exact evidence spans
       ├→ Apertus concept/entity/claim candidates → validation/entity resolution
       └→ original source chunks → configured embedding vectors
  → staged PostgreSQL full-text/pgvector build + canonical evidence/claim records
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

The [data-layer router](../data/DATA_LAYER.md) owns storage/build specifications.
Raw files, normalized bodies and sidecars remain in artifact storage; PostgreSQL
holds canonical evidence, claims, taxonomy, jobs, cases and version manifests.
PostgreSQL full-text search and pgvector store the rebuildable retrieval view.
Independent lexical/vector results are fused with RRF, then BGE reranking scores
query/passage pairs. Full-text ranking is not BM25 and does not gate vector search.

LangGraph's PostgreSQL saver owns graph checkpoints in a separate database;
Langfuse observes through a local integration and its own services. Neither
framework's internal records replace canonical evidence or business case state.
The [schema](../data/RELATIONAL_SCHEMA.md), [case state](../data/CASE_STATE_AND_LINEAGE.md)
and [tracing](../data/OBSERVABILITY.md) specs define physical boundaries. Exact
model/tokenizer artifact sources remain deferred, with roles/configuration
contracts in [build and operations](../data/BUILD_AND_OPERATIONS.md).

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
   text, its input hash and the resolved embedding configuration. Never embed
   only a classifier summary. Original DE/FR/EN (and IT where available) wording
   remains searchable.
5. **Chunk + embedding → PostgreSQL:** stable chunk/version identity, literal text,
   lexical projection, scope/provenance and one supplied dense vector/config.
   Validate transactional writes, references and build completeness before
   publishing a snapshot; no successful publication from partial batch errors.
6. **Published snapshot → operations:** manifest/index-build IDs and section 7
   interfaces; no application consumer depends on storage-specific object shape.

### 8.3 Chunk and embedding preparation

Use heading/paragraph/page boundaries and contiguous offsets. Start around
400–650 embedding-model tokens with 60–100 overlap for long sections, as tunable
settings. Count title/heading and role-template context in the actual loaded
embedding tokenizer budget; exact tokenizer source/limit remains deferred.

EmbeddingGemma 2 is the initial candidate, with a provisional 768-dimensional
build. Required input/output/configuration fields are in the
[model contract](../data/BUILD_AND_OPERATIONS.md#model-roles-and-required-interfaces).
Reject unresolved configurations, invalid vectors, silent truncation and mixed
spaces. Query/document role templates can differ while sharing one pinned model
configuration. Apertus and the BGE reranker have separate compatible tokenizers
and budgets; Apertus token IDs are not passed to the embedding model.

### 8.4 PostgreSQL representation and snapshot publication

The [relational schema](../data/RELATIONAL_SCHEMA.md) owns physical tables/keys:
canonical records in `corpus`, vocabulary in `taxonomy`, chunks/embeddings/lexical
projections in `retrieval`, case records in `cases`, jobs in `ops`. LangGraph and
Langfuse have separate framework databases. Preserve the logical IDs of section 7.

Use explicit snapshot/build membership, foreign keys, scoped references and
validated JSONB extensions. Build lexical projections over original title,
headings and body with appropriate language configuration; vectors reference
the exact embedding input/config hash. Uncertain labels must not hide valid text.
Full search/fusion behavior belongs to the [retrieval spec](../data/RETRIEVAL_SPEC.md).

Stage artifacts/rows and validate evidence, vectors, coverage and eligibility
before publication. Atomically update the active profile pointer in PostgreSQL;
existing runs remain pinned. No transaction spans artifact storage, checkpoints
and tracing. Use idempotent jobs and reconciliation under the
[publication/recovery contract](../data/BUILD_AND_OPERATIONS.md#transactional-publication-and-artifacts).
Failed publication retains the old snapshot; revocation overrides old access.

### 8.5 Information handed to agentic retrieval

LangGraph receives a `QueryPlan`: permitted original request, resolved company
context, user priorities/exclusions, conversational revision IDs, taxonomy
version, candidate concepts, explicit reliable filters, snapshot ID and budgets.
Keep original lay wording alongside scientific expansions and their origin;
generated expansion terms are hypotheses rather than company facts.

1. Embed contextual queries with the pinned embedding configuration. Execute
   PostgreSQL lexical and pgvector cosine searches independently over eligible
   evidence, then fuse their ranks; keyword matches never gate semantic matches.
2. Keep 30 fused unique candidate passages initially, with score metadata and
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

- [pgvector](https://github.com/pgvector/pgvector): cosine search, optional HNSW
  and combination with PostgreSQL full-text search/RRF.
- [PostgreSQL text search](https://www.postgresql.org/docs/current/textsearch-controls.html):
  `tsvector`, text-search configurations and lexical ranking; not native BM25.
- [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence):
  framework-owned PostgreSQL checkpoints, distinct from application knowledge.
- [Langfuse integration](https://langfuse.com/integrations/frameworks/langchain)
  and [self-hosting](https://langfuse.com/self-hosting): callbacks, custom traces
  and required auxiliary services.

The [focused build spec](../data/BUILD_AND_OPERATIONS.md) records model roles and
required resolved configurations. Exact model/tokenizer sources/revisions remain
intentionally deferred. Documented interfaces do not establish endpoint access,
corpus quality, package compatibility or successful deployment.

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

## U8 runtime contracts

Existing source/read contracts above remain valid. New case processing DTOs
are implemented in `src/backend/contracts/pipeline.py`; frontend projections
are in `contracts/frontend.py`. [Case processing](REPORT_PROCESSING_BOUNDARIES.md)
owns interpretation/assessment/pack/draft stages. [Web research](../data/WEB_RESEARCH.md)
selects Crawl4AI for future case-time fetches; this does not settle bulk ingestion.
