# Final application schema

**18 October 2026 · Contract v1 finalized at 0005; current head `0007_frontend_lifecycle`.**
This is the schema for the agreed case → research → evidence pack → draft →
reason review → PDF pipeline. The executable table definitions are
[`schema.py`](../../src/backend/data/schema.py); the generated
[field reference](SCHEMA_REFERENCE.md) lists every actual column, FK, default,
check and index. Future agents must use those definitions rather than infer
columns from older planning text. Schema changes require a forward migration,
updated reference and focused integration checks.

One PostgreSQL `navigator` database has five application schemas. LangGraph and
Langfuse own separate databases and migrations. Do not create a database per
institution, entity type, case or taxonomy topic.

## Tables retained and why

| Area | Retained tables | Purpose |
| --- | --- | --- |
| Corpus acquisition | `corpus.sources`, `source_families`, `source_family_memberships`, `documents`, `document_aliases`, `fetches`, `document_versions`, `artifacts` | Registered origins/families, canonical URLs, observed fetches, immutable original/normalized content and dates |
| Source-backed knowledge | `corpus.evidence_spans`, `entities`, `entity_identifiers`, `claims`, `claim_evidence`, `derivations` | Exact quotations, entity identity, literal/entity relationships, support and extraction provenance |
| Published corpus | `corpus.snapshots`, `snapshot_documents`, `snapshot_entities`, `snapshot_claims`, `active_snapshots` | Freeze eligible versions and identities for reproducible searches/cases |
| Taxonomy | `taxonomy.profiles`, `versions`, `concepts`, `labels`, `relations`, `assignments`, `assignment_evidence` | Pinned domain settings; multilingual concepts/aliases; broader/related links; supported many-to-many tags on documents, chunks or entities |
| Retrieval | `retrieval.chunks`, `chunk_evidence`, `embedding_configs`, `embeddings`, `index_builds`, `search_documents`, `snapshot_chunks` | Original passages, citation mapping, compatible embedding spaces, full-text projections and exact published membership |
| Case identity/context | `cases.cases`, `input_revisions`, `dialogue_turns`, `runs`, `questions`, `answers`, `interpretations` | Owner/revision, permitted prompts/chat, pinned runs and structured classification/clarification |
| Case-time sources | `cases.web_research`, `web_sources`, `case_evidence_manifests`, `case_evidence_items` | Bounded discovery outcomes, flagged new pages, corpus duplicates and sealed local evidence |
| Evidence/report | `cases.claim_assessments`, `evidence_packs`, `pack_items`, `pack_claims`, `result_revisions`, `draft_reasons`, `reason_claims` | Semantic assessment records, immutable supported pack, draft revisions and explicit reason-to-claim support |
| Editorial/output | `cases.reason_selections`, `reviews`, `exports`, `action_items` | Keep/reject/none per card, exact approval hashes, output artifacts and follow-up questions |
| Access/build/execution | `ops.principals`, `scope_grants`, `model_configurations`, `ingest_jobs`, `stage_attempts`, `publication_checks`, `outbox`; `corpus.scopes` | Existing isolation/revocation, model/build identity, restart-safe work and publication checks |

These **63 tables** include small association tables; they are not 63 separate
services. Scope, version and support links remain relational because retrieval,
case isolation and traceability depend on them. Not every import populates every
table: identifier/derivation/concept-assignment rows exist only when known.
There is no requirement to manufacture missing data to complete a row.

## Entity and relationship contract

Use `corpus.entities.entity_type` = `person`, `unit`, `organization`, `project`,
`facility` or `service`. An institute/research group is a `unit`; a public company,
university, centre or civic organization is an `organization`. A relevant person
uses `person`. No separate institutes/companies/contacts tables are needed.

Identity labels are not globally unique. Use `entity_identifiers` only for
source-supported identifiers with a known authority; `verified=true` asserts
issuer-level uniqueness. A private company description in a case is operator
input, not an automatic public organization row.

Relations and attributes use `corpus.claims`:

- `subject_id`, `predicate`, and **exactly one** of `object_entity_id` or
  `typed_literal`; support goes in `claim_evidence`.
- Starter predicate names: `name`, `role`, `affiliated_with`, `part_of`,
  `expertise`, `capability`, `works_on`, `provides`, `located_in`, `contact`.
  These are an ingestion convention; the DB enforces nonempty predicates,
  not a closed scientific vocabulary. Document an extension before consumers use it.
- Entity relations such as affiliation use `object_entity_id`. Literal attributes
  use `{"type":"text","value":"..."}`; `url` and `email` are suitable literal
  type names for explicit source-provided links/addresses. Type/value are required;
  other literal types require an agreed consumer, not invented guessed values.
- Source-supported facts are separate from run-specific fit and writing.
  `claim_assessments` assesses an exact statement/support set for one run;
  it does not convert a new web source into a curated shared source.

Nullable source dates mean unknown publication dates. `created_at` on a fetch is
its observation time, not the publication date. `source_date` belongs to the
immutable document version. Names, roles, contacts, location and affiliations
must resolve to supported claims; do not add mutable person-profile columns.

## Data and JSON ownership

Relational IDs/FKs own identity, access, membership and factual support.
Validated JSON owns bounded structured outputs, without a second table for each
field of those outputs:

| Column | Contract / owner |
| --- | --- |
| `cases.interpretations.payload` | `CaseInterpretation`: company name/summary, fields, activity, Bern intent, needs, concepts/terms, constraints, leads and clarification |
| `cases.claim_assessments.payload` | `ClaimAssessment`: exact statement/evidence IDs, assessment, validator and explanation |
| `cases.evidence_packs.payload` | `ReportEvidencePack` v2; matches/arguments, supported claims, coverage, gaps and actions; relational membership is checked against it |
| `cases.result_revisions.payload` | `DraftRevision` v2 plus the repository's exact-draft assessment assertion |
| `cases.draft_reasons.payload` | `DraftReason` content; indexed `reason_key` and `support_hash` bind editorial review |
| `cases.web_sources.payload` | `FetchedSource` metadata excluding content; body is stored once as a document version |
| `ops.stage_attempts.outputs` | Durable stage envelope: serialize actual `QueryPlan` / `SearchResult` and output IDs as appropriate; application task owns validation |
| Profile/model/build configuration and diagnostics | Pinned configuration or execution metadata; never a substitute for source evidence or access policy |

Do not duplicate company-classification fields into another company table or
create a second match/score store beside the pack. Query plans and retrieval
round observations use stage outputs (include round in the stage/idempotency
identity); graph checkpoints hold resumable state, Langfuse holds masked diagnostics.

## Retrieval and provenance invariants

- Body text is immutable and hashed against its artifact. Evidence/chunk offsets
  are zero-based Unicode characters, exclusive end: `body[start:end] == literal_text`.
- A chunk holds original text; `retrieval.embeddings.input_text` holds the actual
  model-formatted input. There is no chunk `embedding_text` or `context_prefix`.
- An embedding config fixes model/tokenizer/revision/templates/dimension. Vector
  dimensions are checked per config; model/deployment selection need not alter
  the schema. Queries and builds cannot mix spaces.
- `search_documents.terms` has a GIN index; lexical and cosine branches search
  independently over the same authorized published membership. Exact cosine is
  the pilot baseline; no unmeasured ANN index is mandated.
- Source-family membership is many-to-many: ARTORG can also be UniBE.
  Preserve canonical document identity and aliases; URLs alone do not prove expertise.
- New web evidence is case-scoped. Pack membership is the pinned snapshot plus
  its own sealed case manifest. No automatic promotion into the shared corpus.
- Reason review is the sole editorial selection model. Rejection does not mean
  a claim is false. All reviewed/one kept and exact hashes gate PDF export.
- Existing RLS, immutability, scope, slice, embedding and lineage triggers remain.
  Repositories additionally validate pack hashes and semantic-assessment records;
  raw SQL writes do not replace those checks.

## Additions after contract v1

- `0006_runtime_access`: owner-checked case-scope provisioning and restrictive
  run/command RLS; application workers retain ordinary credentials.
- `0007_frontend_lifecycle`: independent case `on_hold` / closed `outcome` and
  action-item `answer`; migrates former combined statuses.

New installations and upgrades target **head**, currently 0007, rather than
stopping at 0005. See [live setup](LIVE_SETUP.md) for the coordinated rollout.
Neither integration nor this documentation audit migrated Eric's host.

## Removed structures and upgrade behavior

Migration 0005 retires `cases.query_plans`, `retrieval_rounds`, `retrieval_hits`,
`matches`, `match_support`, `selections`, and `ops.frontier`. These had no active
repository consumer or duplicated the agreed pack/reason workflow. A crawler queue
is not part of the current ingestion contract; add one later only for an implemented need.
It also removes the two redundant chunk encoding columns.

Fresh databases contain only the final application tables. Upgrades preserve
populated retired tables in owner-only `legacy`, and preserve any nonredundant
old chunk values in `legacy.chunk_encoding`. No application repository or future
feature should query that archive. Empty retired tables are dropped when there
is no historical data. Existing conflicting duplicate aliases/manifest items or
invalid types make constraint installation fail transactionally; resolve them
explicitly, never silently delete facts. Back up before a shared-host migration.
Historical migrations use frozen baseline metadata and their original security
installer under `data/migrations/`, so future schema edits cannot
silently change older migration behavior. Destructive downgrades remain disabled.

Start the data teammate at [ingestion/retrieval handoff](INGESTION_RETRIEVAL_HANDOFF.md).
