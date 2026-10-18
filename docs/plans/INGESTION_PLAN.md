# Phase 1 — Source ingestion, taxonomy and memory

**Date:** 18 October 2026. **Status:** implementation proposal; no implementation
or measured results. The two-phase boundary is a user decision. The user has
specified an initial architecture to validate: Apertus 1.5 8B/70B, BGE-M3,
Weaviate, BGE-reranker-v2-m3 and LangGraph. Exact deployments, revisions and
corpus-specific performance remain unverified; taxonomy contents are not yet defined.

**Companion:** [Phase 2 — Case operations](OPERATIONS_PLAN.md).
This file owns the shared data and memory contracts consumed by Phase 2.

**Current scope decisions:** [selected pilot](../challenge/PILOT_SCOPE.md), based on the user's
18 October answers and public-source investigation. Diabetes technology is the
pilot, English the output baseline, and DE/FR/IT support an extension. Endpoint
and deployment details will be supplied before development.

## 1. Outcome and scope

Build a repeatable pipeline that collects permitted source material, preserves
evidence, maps its meaning into a team-defined taxonomy, extracts supported
entities and claims, and publishes a searchable, versioned memory snapshot.

```text
Reviewed sources → raw artifacts → normalized documents and evidence spans
                 → Apertus 8B classification → validation → 70B fallback if needed
                 → exact source chunks → BGE-M3 dense vectors
                 → Weaviate BM25F + vector index → published memory snapshot

Phase 2: request + context → LangGraph → hybrid retrieval → BGE reranking
         → evidence validation → answer/report → user edits or follow-up dialogue
```

Collection and normalization are deterministic. Apertus enrichment is a separate,
recorded derivation; it must never overwrite the source representation. Memory
is the durable evidence store plus rebuildable retrieval indexes, not merely
conversation history or a vector database.

Phase 2 reads published snapshots to understand a company case, research context,
retrieve matches and generate a reviewed PowerPoint. Case-specific public web
research may reuse this pipeline but starts in a case-scoped collection.

## 2. Authority and relationship to existing documentation

- **Requirement:** [challenge brief](../challenge/CHALLENGE_BRIEF.md) and
  [product requirements](../challenge/PRODUCT_REQUIREMENTS.md): Bern life sciences/medicine,
  UniBE + ARTORG + Diabetes Center Berne coverage, source-supported results,
  purposeful Apertus v1.5 use and independent deployment.
- **User decision, 18 October 2026:** Phase 1 includes taxonomy processing and
  memory publication; Phase 2 implements the previously described case workflow.
- **Detailed collection reference:** [existing ingestion spec](../data/ingestion/INGESTION_SPEC.md).
  Its old “Phase 1” is now the collection/normalization substage of this plan.
  Its exclusion of classification and indexes does not apply to this expanded
  phase. Keep its faithful extraction, provenance and crawl-policy requirements.
- **Precedence for implementation:** use this plan for phase boundaries, shared
  contracts and the corrections in section 11. Treat the existing
  [source registry](../data/ingestion/sources.yaml) as a draft requiring revision, not
  verified coverage or an approved live crawl configuration.

Implementation code belongs under `src/`; working plans remain under `docs/`.
Preserve the root submission files and `LLM_NAME`, `LLM_BASE_URL`, `LLM_API_KEY`.

## 3. Source scope and acquisition

### 3.1 Required collection order

1. Start with the verified discovery seeds in [PILOT_SCOPE.md](../challenge/PILOT_SCOPE.md),
   including ARTORG research, DBMR Bally Lab and DCB `/en/projects/`. Import the
   [partner workbook](../provided_material/README.md) as the initial discovery map:
   42 actual entries, including ARTORG and DCB. Its Notes count of 71 is
   inconsistent; do not invent missing entries. Retain workbook/sheet/row
   provenance, use column C URLs, prioritize healthcare and extend discovery
   under per-origin robots/access rules. Treat DCB as a separate origin/family.
2. Collect research units, professional profiles, projects, capabilities,
   infrastructure and services across all three source families.
3. Start expansion from partner-provided references already captured locally;
   add healthcare institutions/companies with evidenced Canton of Bern activity.
   Do not treat international partners/competition participants as Bern-local.

Prioritize glucose monitoring, automated insulin delivery and supporting
digital tools. Public web pages are primary, linked public PDFs secondary.
Collect German/French/Italian material where useful without translating the
canonical evidence; English descriptions are separate derived records. Apply
bounded quotas for safe execution, not an invented fixed user coverage limit.

Do not substitute general UniBE directory pages or extra institutions for
ARTORG/DCB coverage. Report source-family membership separately from the single
administrative owner of a document; one page may support multiple families.
National expertise is not automatically Bern-local expertise.

### 3.2 Registry and policy

Validate source IDs, seeds, allowed hosts, exact paths, path prefixes, exclusions,
content types, language hints, adapters, quotas and shared host rate limits.
Record terms review status, reviewer, date, reviewed URLs and restrictions.
The user authorizes collection of public content allowed by robots; a separate
manual approval for every origin is not required. Automatically inspect robots
and known published restrictions, recording actual blocks/ambiguities for review.
The draft registry's `block_unreviewed_terms: true` and blanket pending-state
gate must be revised to this policy before implementation; do not relabel pending
terms as reviewed. Redistribution rights remain distinct from collection access.

Check scope, robots and destination IP safety before requests and redirects.
Apply the same policy to browser requests and downloaded assets. Preserve
semantic query parameters; reject forbidden navigation rather than silently
rewriting its meaning. Bound response bytes, decoded bytes, processing time,
PDF pages, retries and total run time. Persist retryable work for resumption.

## 4. Preserve raw material and normalize evidence

Store original bytes, requested/final URLs, response metadata, fetch time, raw
hash and collection-policy decisions. Extract HTML and text PDFs first; add
OCR for scans with engine/version, language, page provenance and quality flags.
Preserve headings, lists, tables, links and original language. Store complex
tables or media as referenced sidecars and include them in exports.

Keep body-only normalized text separate from generated metadata and summaries.
An evidence span must satisfy `body[char_start:char_end] == text`, using Unicode
character offsets and an exclusive end. Keep page/section locators and the
mapping back to the exact raw artifact. OCR or visual transcription is derived
text with its method recorded, not a guaranteed verbatim original quote.

Image/audio support and native PDF upload are distinct capabilities. The
[official Apertus 1.5 70B model card](https://huggingface.co/swiss-ai/Apertus-v1.5-70B)
documents text/image/audio input; actual endpoint support remains unverified.
If visual interpretation is used, retain it as a separate derived artifact with
page/image locators and validation status. Do not insert it into faithful text.

## 5. Define and version the taxonomy

The team must supply/review the initial taxonomy before enrichment is accepted.
Start with a small controlled vocabulary covering the pilot; do not require a
graph database or a comprehensive medical ontology to begin.

Each concept contains:

- Stable `concept_id`, `taxonomy_version`, preferred labels by language.
- Definition, inclusion/exclusion notes and relevant examples.
- Multilingual synonyms and abbreviations, with ambiguous aliases identified.
- Explicit broader/narrower relations and separately labeled related concepts.
- Optional external ontology IDs with provenance and reuse terms.
- Deprecation/replacement mapping when concepts change.

Proposed facets: medical domain, research capability, technology/method,
application, infrastructure/service and collaboration need. Geography and
organization identity remain evidence-backed entity attributes, not guessed
topic labels. Entity types are person, unit, project, infrastructure, service
and company. These types are distinct from taxonomy concepts.

Classification uses surrounding passages, document context and concept
definitions. Keywords alone cannot assign a concept. Allow multiple concepts,
`unmapped` and `ambiguous`; retain candidate alternatives and supporting spans.
An alias shared by two concepts must not force them to merge. Proposed new
concepts go to review rather than modifying the taxonomy automatically.

## 6. Apertus enrichment and validation

### 6.1 Information sent to the classifier

Pass an explicit `ClassificationRequest`, not the whole crawler state or a
conversation transcript. Include `schema_version`, request/document/version
IDs, normalized body hash, title, source URL, language, organization hints marked
as hints, taxonomy ID/version, allowed document types, relevant concept
definitions, and source passages with evidence IDs/page/section locators.
The task instruction is application-owned; source text is delimited untrusted
data. Input includes contextual neighboring sections when a passage is ambiguous.

Use Apertus **v1.5 8B** as the default classifier. Long documents are processed
as bounded contextual section batches, then consolidated with the same evidence
IDs. Do not classify only a generated summary or silently truncate a document.
Store which spans were processed and disclose incomplete coverage. Budget with
the actual Apertus tokenizer/processor/template; endpoint capabilities are pending.

### 6.2 Information returned and validation routing

Require a `ClassificationResult` containing:

- Document type: institute profile, project, facility, funding opportunity,
  service, news or `unknown`. Allow additional reviewed types such as person
  profile instead of forcing an unsupported label. Types are versioned separately
  from research-topic concepts and can be multi-valued for mixed documents.
- Multiple research-topic assignments with concept IDs, mapping kind and evidence.
- Explicitly supported organization/location claims. Separate organization
  address, activity location and project geography; national/international
  content does not inherit a Bern location from its publisher.
- Extracted entity/claim candidates, supporting quotations, evidence IDs,
  original section/page references and missing-field reasons.
- Ambiguities, conflicting assignments and `unknown`/`unmapped` fields.
- Model/prompt/taxonomy versions and processing coverage. Plain-language
  descriptions, if generated, are separate derived fields with supporting claims.

Validate JSON/schema, label membership, IDs and literal quotation/span equality
deterministically. These checks do not establish semantic entailment; inspect
claim support and evaluate against independently labeled examples as well.

Route schema/quote failures after one bounded repair attempt, unresolved
ambiguities, conflicting topic assignments or insufficient context to **Apertus
v1.5 70B**. Send the same source passages/taxonomy plus validation diagnostics
and the 8B candidate explicitly labeled as unverified. The larger model cannot
resolve conflicting source facts by guesswork. Preserve both derivations and
the routing reason. Apply the same validators to its output; unresolved records
remain `needs_review` or `unknown` and do not become accepted claims.

If 70B is unavailable, preserve pending work and explicit limitations; do not
silently relabel the 8B output as verified. Use deterministic routing signals
and a manually labeled routing sample rather than model self-confidence alone.

### 6.3 Terminology bridge and claim protection

The stakeholder describes a gap between scientific page language and investor
language [T05 00:00–00:47](../recordings/bern-navigator-followup-2026-10-18.txt).
Retain scientific terms and their surrounding evidence. Store reviewed lay
aliases in the taxonomy; keep generated `plain_language_description`,
`business_relevance_hint` and suggested adjacent uses as derived, evidence-linked
fields. They are retrieval/explanation aids, never substitutes for source text.
Do not equate a suggested application with an evidenced project. Future fields
such as robotics should reuse these contracts with a new taxonomy/configuration,
without widening the current Bern healthcare pilot automatically.

### 6.4 Processing invariants

For each eligible document/section:

1. Construct a bounded input containing exact evidence, metadata and relevant
   taxonomy definitions. Delimit source content as untrusted data.
2. Ask Apertus 8B, with the bounded 70B route above, to produce concept assignments, entities and
   factual claims, each pointing to supporting evidence IDs.
3. Validate schema, allowed concept IDs, evidence existence and locator integrity.
   Missing facts remain null with a reason. Retry malformed output within a
   fixed budget; otherwise quarantine the derivation.
4. Check semantic support separately: valid offsets alone do not prove that a
   passage supports a role or capability. Use reviewed pilot examples and a
   documented review policy; retain unverified/conflicting claims explicitly.
5. Resolve duplicate entities using explicit profile links/identifiers and
   compatible affiliations. Similar names are insufficient. Record merge
   evidence and preserve ambiguous identities separately.
6. Store the derived result with model ID/revision, prompt version, taxonomy
   version, settings, input hashes, validation state and processing time.

Do not store a proposed adjacent application as an established capability, or
infer expert availability, willingness to collaborate, contact details or
economic impact. These boundaries also apply to Phase 2.

## 7. Shared contract v1 — owned here, consumed by Phase 2

Implement typed schemas and JSON Schema exports in `src/`. Every record carries
`schema_version`. IDs are opaque to consumers; references must resolve within
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
- **SnapshotManifest:** `snapshot_id`, schema/taxonomy versions, included
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
5. Pass an `EvidencePack` to synthesis: interpreted need, user priorities,
   accepted claim IDs, literal passages, locators, sources, conflicts, coverage
   and missing evidence. Use 8B initially; 70B is optional for difficult synthesis
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

## 9. Incremental processing and previous cases

Use conditional HTTP requests and raw hashes to avoid unnecessary extraction.
Document versions include extraction/normalization configuration; enrichment
versions additionally depend on taxonomy/model/prompt settings. Index builds
depend on chunker and embedding configuration. A changed taxonomy can trigger
reenrichment/reindexing without a new crawl.

Track raw fetch snapshots separately from normalized content versions so a
boilerplate-only change does not destroy auditability. Define a configurable
permanent-unavailability policy: an isolated 404 or temporary failure must not
silently remove evidence. Retire confirmed unavailable sources from current
search while retaining permitted history and warnings.

Import historical cases only from an approved public/non-confidential dataset.
Confidential plans cannot be made acceptable merely by moving inference locally
or removing names. No historical-case corpus is currently supplied. Support an
empty case collection with an explicit unavailable-data result. Demonstration
fixtures may be synthetic and must not be presented as real agency cases.

## 10. Milestones and acceptance gates

1. **Contracts and scope:** implement schemas, taxonomy loader and registry
   validator; verify seeds for all three required families; identify endpoint
   and permitted pilot inputs. Exit: fixtures validate and missing prerequisites
   are reported rather than invented.
2. **Collection and evidence:** bounded HTML/PDF acquisition, raw storage,
   normalization and exact spans. Exit: reviewed samples from all three families
   with recoverable provenance; scans/unsupported media have explicit outcomes.
3. **Taxonomy and entities:** Apertus derivations, validation and cautious entity
   resolution. Exit: reviewed ambiguous/synonym/missing-field examples, with no
   unsupported accepted claims in the reviewed sample.
   Compare 8B-only classification and the 8B-to-70B routing policy on a manually
   labeled sample; report routing rate, correction rate, cost and remaining errors.
4. **Published memory:** implement section 7 functions, indexes and atomic
   snapshots. Exit: Phase 2 contract tests can retrieve entities and resolve
   every cited span from a fixed snapshot; access filters and empty cases work.
5. **Refresh and evaluation:** verify unchanged reruns, changed sources,
   taxonomy migrations, revoked access and failed publication. Measure retrieval
   using [EVALUATION.md](../challenge/EVALUATION.md); document actual coverage and omissions.

Use offline fixtures for automated tests, including query parameters, scope,
redirects, robots denial, shared-host limits, malformed PDFs, Unicode, tables,
OCR flags, injected instructions, exact offsets, deduplication and index rebuilds.
Live source smoke tests are additional evidence, not prerequisites for offline
tests. Track fetched/extracted/enriched/indexed/rejected counts separately.

Handoff tests must reject unresolved evidence references, changed embedding
inputs with reused vectors, dimension mismatches, cross-snapshot queries and
partial index publications. Verify that an unlabeled but relevant source remains
retrievable, classifier summaries cannot replace original text, and a user focus
change reaches both retrieval and the evidence pack. Evaluate DE/FR/EN retrieval
and terminology bridging explicitly; Italian remains an extension.

When consuming the legacy collector, map its `version_id` to the shared
`document_version_id` at one typed adapter boundary. Preserve `chunk_id` and
offsets; do not accidentally treat an enrichment revision or index-build ID as
a source-document version. Publish this mapping with the JSON Schemas.

## 11. Corrections required in the collection implementation

- Move the old proposed root `bern_ingest/` package under `src/`.
- Add explicit ARTORG/DCB coverage and revise optional-source priorities.
- Support `allowed_exact_paths`, `adapter` and structured review metadata.
- Include parser/normalizer configuration and chunker/tokenizer versions in
  derived artifact identities; keep raw and content lineage distinct.
- Unify 404/410 retirement handling with section 9.
- Define `needs_review` records as ineligible for accepted factual results until
  validated; retain them for diagnostics and targeted review.
- Include sidecars and extraction locators in portable exports.
- Replace the old missing-inventory/manual-per-source gate with the supplied
  workbook, supplementary discovery and robots/access policy above. Update the draft registry
  and legacy spec accordingly when implementing collection.

## 12. Deployment and unresolved choices

Connected collection is distinct from runtime. A disconnected deployment must
bundle permitted snapshots, taxonomy, indexes, model/tokenizer assets and all
runtime dependencies. Test with networking disabled before claiming offline
operation. Independent cloud operation is also allowed; cantonal internal
networks remain excluded.

The selected pilot, discovery seeds and English-first language policy are in
[PILOT_SCOPE.md](../challenge/PILOT_SCOPE.md). Partner examples/expected entities can be
provided but are not received. Inference and deployment details are deferred
to the user's pre-development handoff. Remaining technical choices include
taxonomy contents/reviewer, model/package revisions, actual access policies and corpus
size; a historical-case dataset remains separately unavailable. Follow the
pilot's proposed pre-demo refresh policy and report snapshot age. Record decisions in
[DECISIONS_AND_OPEN_QUESTIONS.md](../project/DECISIONS_AND_OPEN_QUESTIONS.md).
