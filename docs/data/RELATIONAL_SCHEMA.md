# PostgreSQL schema specification

**18 October 2026 · Physical design proposal under selected PostgreSQL stack.**
Read [data layer](DATA_LAYER.md) first. Logical record meanings remain owned by
[Phase 1 section 7](../plans/INGESTION_PLAN.md#7-shared-contract-v1--owned-here-consumed-by-phase-2).
The tables below are implemented by the versioned Alembic migrations under
`src/backend/data/migrations/`; see [deployment](DEPLOYMENT.md) for validation.

## Common conventions

- Use application-generated UUID primary keys, `timestamptz` timestamps in UTC,
  UTF-8 text, SHA-256 artifact/input hashes, and explicit version/status columns.
- Use relational columns/FKs for identity, visibility, joins and filter keys.
  JSONB holds validated optional extensions, settings and diagnostics; do not
  bury all source/claim relationships or authorization inside opaque JSON.
- Store missing source facts as null with a reason; never synthesize roles,
  email addresses, geography, outcomes or publication dates.
- Restrict enumerated states with check constraints or migration-owned lookup
  tables. Every foreign key has an intentional deletion/retention policy.
- `corpus.scopes(scope_id, kind, case_id, access_policy_id)` distinguishes shared
  public from case-private evidence. Case ownership/access is enforced in the
  application and PostgreSQL roles/RLS as applicable. A scope reference is not
  itself an authorization check. Case scope requires a case ID; public does not.

## Corpus and provenance

| Table | Important columns and constraints |
| --- | --- |
| `corpus.sources` | `source_id`, canonical origin, registry/profile reference, scope/access decisions, status; discovery URLs are not evidence of expertise |
| `corpus.source_families`, `source_family_memberships` | Family IDs; source ↔ family many-to-many; ARTORG may also be UniBE without duplicate downloads |
| `corpus.documents` | `document_id`, source ID, canonical fetch identity, scope ID; unique `(scope_id, canonical_url)`; retain URL aliases separately |
| `corpus.artifacts` | `artifact_id`, storage key, SHA-256, MIME, byte count, availability/status; content-addressed bytes may be shared internally, access is checked through scoped references |
| `corpus.fetches` | Requested/final URL, redirects, HTTP status/validators, retrieval time, raw artifact ID or failure, job ID; unchanged/failed fetch is still an observation |
| `corpus.document_versions` | `document_version_id`, document ID, raw/body artifacts, body hash, parser/configuration version, language, source date; unique normalization identity; immutable after acceptance |
| `corpus.evidence_spans` | `evidence_id`, document-version ID, Unicode `char_start/char_end`, literal text, heading/page locator, extraction method; `0 <= start < end`, unique version/locator identity |
| `corpus.entities` | `entity_id`, type, scoped identity, supported display label, review state; names are not globally unique identities |
| `corpus.entity_identifiers` | Entity ID, identifier kind/value, authority and evidence; unique verified identifiers only where the issuer guarantees uniqueness |
| `corpus.claims` | `claim_id`, subject entity ID, predicate, exactly one of object entity ID or typed literal, scope, source/observed dates, validation state, derivation ID; use an XOR constraint for object representation |
| `corpus.claim_evidence` | Claim ID, evidence ID, support/contradiction relation, review decision; accepted factual claims require supporting evidence in an eligible scope |
| `corpus.derivations` | Input IDs/hashes, model/prompt/taxonomy configuration IDs, output hash/artifact, time, validation and errors; generated explanations remain separate from source text |
| `corpus.snapshots` | Snapshot ID, profile/schema/taxonomy versions, index-build ID, coverage manifest/hash, status and publication time |
| `corpus.snapshot_documents`, `snapshot_claims`, `snapshot_entities` | Explicit membership by immutable version/ID; runtime joins cannot substitute arbitrary newest rows |
| `corpus.active_snapshots` | Profile ID → published snapshot ID; one active pointer per profile, changed transactionally after validation |

Evidence invariants are verified by the application against the exact stored
body: `body[start:end] == literal_text`. Python-style Unicode offsets start at
zero with exclusive end; do not confuse them with PostgreSQL substring offsets
or UTF-8 bytes. A locator resolving correctly does not establish semantic support.

Store roles, affiliations and capability relationships as evidence-backed claims,
not mutable free-text columns on a person. When a reviewed interpretation changes,
write a new claim/derivation and snapshot; preserve conflict/supersession lineage.
Never overwrite the support of a claim already pinned by an accepted pack.
Entity rows anchor identity; snapshot display facts resolve from pinned claims,
not an unversioned newest label/affiliation. Composite references/validation must
prevent claim, evidence, chunk and embedding joins across incompatible versions
or scopes. A public claim cannot cite case-private evidence as its support.

## Taxonomy and profiles

| Table | Important columns and constraints |
| --- | --- |
| `taxonomy.profiles` | Profile ID/version, schema version, config artifact/hash, source/ranking/validation settings |
| `taxonomy.versions` | Taxonomy ID/version, immutable artifact/hash, review status and publication date |
| `taxonomy.concepts` | Stable concept ID + taxonomy version, definition, inclusion/exclusion notes, facet and deprecation/replacement |
| `taxonomy.labels` | Concept/version, language, preferred/alternative label, ambiguity notes; label text is not globally unique |
| `taxonomy.relations` | Versioned concept IDs, relation kind (`broader`, `narrower`, `related`); related is not synonym/equivalence |
| `taxonomy.assignments` | Assignment ID, concept/version, one typed target (document version, entity or chunk), direct/related mapping, derivation and validation status |
| `taxonomy.assignment_evidence` | Assignment ID → actual supporting evidence spans |

Use explicit nullable target FKs plus a check that exactly one target is set,
or equivalent typed join tables; avoid an unchecked `(type, arbitrary_id)` pair.
Assignments are many-to-many. Unknown/unmapped text stays searchable. Persist
the imported profile hash; a runtime never reads changing YAML as its live truth.

## Retrieval representation

| Table | Important columns and constraints |
| --- | --- |
| `retrieval.chunks` | Chunk ID, document version, contiguous offsets/literal text, title/headings, language, scope, chunker hash; no generated summary substituted for text |
| `retrieval.chunk_evidence` | Chunk ID ↔ evidence ID, preserving exact document-version compatibility |
| `retrieval.embedding_configs` | FK to resolved `ops.model_configurations`, immutable encoding config hash, dimension, query/document templates and normalization; no second mutable model registry |
| `retrieval.embeddings` | Embedding ID, chunk ID, config ID, embedding-input hash, dense vector; unique `(chunk_id, config_id, input_hash)` |
| `retrieval.index_builds` | Build ID, embedding config, chunker/search settings, status and validation manifest |
| `retrieval.snapshot_chunks` | Snapshot/build → chunk and embedding IDs; unique membership, enforce matching config/version/scope |
| `retrieval.search_documents` | One lexical projection per chunk/search-config version: weighted `tsvector`, text-search configuration and original-text references |

The candidate full dimension **768** remains unverified. Storage uses `vector`
with a trigger enforcing each immutable embedding configuration's dimension;
no production dimension is hard-coded before model handoff. Different dimensions
or embedding spaces require separate compatible builds. The exact-search baseline
does not require dimension-specific ANN indexes. Do not mix configs in one search.

GIN indexes support lexical projections; ordinary indexes support scope,
version and snapshot joins. Start with exact cosine ranking on the bounded
pilot; add HNSW only after comparison with exact results under real filters.
Detailed ranking and multilingual behavior belong to [retrieval](RETRIEVAL_SPEC.md).

## Case and operations schemas

`cases` owns cases, input/dialogue revisions, runs, questions, query plans,
retrieval observations, matches, packs, result revisions, selections, reviews,
case-evidence manifests and exports. See [case state](CASE_STATE_AND_LINEAGE.md)
for keys and lifecycle. `ops` has these migration targets:

| Table | Important columns and constraints |
| --- | --- |
| `ops.model_configurations` | Immutable resolved model-role/config record from the build spec, config hash, artifact/adapter/tokenizer identity and verification state |
| `ops.ingest_jobs` | Job/profile/scope/base-snapshot IDs, configuration hash, state, budgets, counters, timestamps and failure summary |
| `ops.frontier` | Job/source ID, canonical candidate URL, discovery parent/row reference, scope/access decision, state and next eligible attempt; deduplicate per job/source/fetch identity |
| `ops.stage_attempts` | Job/run ID, stage, input/config hash, attempt count, output refs, status, error and worker lease; unique committed stage-result key |
| `ops.publication_checks` | Build/snapshot ID, validator/version, result, manifest/hash and timestamp; required checks must pass before publication |
| `ops.outbox` | Event/idempotency key, type, payload refs, state, attempts, lease and next retry; committed with the initiating business write |

Use unique idempotency keys for retried writes; not every retry is a new fact.

Keep LangGraph/Langfuse framework tables in their separate databases with their
own migrations. Application rows record opaque checkpoint/trace correlations,
not foreign keys into framework internals. Source permission revocation overrides
immutable history: prevent reads and retire dependent packs/exports as required.

## U8 case pipeline extension

[Case pipeline storage](CASE_PIPELINE_STORAGE.md) owns the new tables, manifest
eligibility, supported-claim assessments and reason-level selection/review hashes.
Legacy match selections remain historical. New accepted reviews/exports require
the v2 reason workflow; rejection is editorial and does not retract a claim.
