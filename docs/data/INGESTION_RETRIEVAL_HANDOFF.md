# Ingestion and hybrid retrieval: implementation handoff

**18 October 2026 · Corpus contract v1; application head `0007_frontend_lifecycle`.**
Scope: populate the public knowledge corpus, build a compatible search snapshot,
and improve hybrid retrieval. Leave frontend, case/report orchestration and
schema design to their owners. Read this file, [retrieval](RETRIEVAL_SPEC.md),
[`CorpusRepository`](../../src/backend/data/repositories/corpus.py),
[`SnapshotRepository`](../../src/backend/data/repositories/snapshots.py) and
[`HybridSearch`](../../src/backend/data/retrieval/hybrid.py). Look up exact fields
in the generated [schema reference](SCHEMA_REFERENCE.md); do not use historical
migration metadata as an application query model.

## Write boundary and prerequisites

Write acquisition/normalization adapters under `src/backend/ingestion/`, embedding
integration under `src/backend/models/embeddings/`, retrieval changes under
`src/backend/data/retrieval/`, and focused tests/docs. Reuse `contracts/data.py` and
`contracts/pipeline.py`. Coordinate shared DTO/migration changes; do not add
ad hoc columns or alternate databases while filling the corpus.

The maintainer provisions a DB principal, grants a writable public scope,
imports a versioned domain profile and reviewed taxonomy, and migrates to
the current head, `0007_frontend_lifecycle`. The worker receives `AccessContext`, `scope_id`,
`profile_id`, `taxonomy_version_id`, artifact store and a resolved embedding config.
`access_policy_id` is a descriptive policy reference, not an authorization rule;
actual access is enforced through scope grants/RLS/revocation. Never bypass it
with a superuser connection in application workers.

## Import order and minimum actual records

1. **Register sources:** `corpus.sources` supplies `source_id`, `scope_id`,
   `canonical_origin`, `registry_ref`; status defaults active. Register source-family
   names `UniBE`, `ARTORG`, `DCB`, then join via `source_family_memberships`.
   Multiple families may share a source. Use the inventory/config as discovery,
   not evidence of a particular capability. `RegistryImporter.sources` imports these records; `mesh-import` imports
   reviewed profile/taxonomy pins. See the [ingestion CLI and manifest](../../src/backend/ingestion/README.md).
2. **Fetch and normalize:** call `CorpusRepository.stage_document(...)` with
   scope/source IDs, canonical URL, title, language, raw bytes/MIME, faithful body,
   exact `Span` records and parser hash. This writes artifact references, document,
   fetch observation, immutable version and spans. Normalize URLs with
   `canonical_url(...)` before calling; store observed aliases explicitly.
   The repository now accepts optional timezone-aware `source_date`; omit unknown
   publication dates. `http_status` may be null when no HTTP observation exists.
   Do not store a current timestamp as a guessed publication date.
3. **Prepare supported knowledge:** `record_entity(...)` for person/unit/
   organization/project/facility/service; `record_claim(...)` for a relationship
   or typed literal with source evidence IDs. Use the conventions in
   [schema decisions](RELATIONAL_SCHEMA.md#entity-and-relationship-contract).
   Mark `accepted=True` only after the importer/curator checks support. Missing
   roles/contact/projects/services stay absent, not invented. Extraction can be
   manual for the pilot; automated enrichment is a separate adapter.
4. **Optional enrichment:** source-supported identity keys → `entity_identifiers`;
   extraction/model provenance → `derivations`; reviewed concept tags →
   `taxonomy.assignments` + `assignment_evidence`. No empty placeholders required.
   Assignments have exactly one target: document version, entity or chunk.
   Broader/related concepts are not exact synonyms. Every concept belongs to the
   pinned taxonomy version.
5. **Embed chunks:** register a verified `ModelConfiguration` with
   `register_embedding(...)`; call `stage_chunk(...)` with version, exact `Span`,
   chunker hash, config ID and the computed vector. The method writes chunk,
   exact citation mapping, actual formatted `embeddings.input_text`/hash/vector,
   and weighted language + `simple` full-text projections. The embedding worker
   must encode exactly the configured document template using the version's
   title and chunk headings/text. Use its own tokenizer and explicit token limits;
   do not silently truncate. Changing model/template creates a new config/build.
6. **Stage a snapshot:** `SnapshotRepository.stage(...)` receives the exact chunk,
   entity and accepted claim IDs plus profile/taxonomy/config/chunker IDs.
   Claims need pinned subjects and accepted supporting evidence in the snapshot.
   Pass complete subject/object entities for relationship graphs; never silently
   substitute newest document versions. An accepted claim's complete support
   should be included if it will be used in a pack.
7. **Publish:** `publish(..., expected_active=...)` checks the configured source
   families, text/vector integrity and lexical projections, then atomically
   advances the profile's active pointer. Failed publication preserves the old
   active snapshot. Runs already pinned to it stay unchanged.

A document/chunk-only snapshot can support search experiments, but final
entity-backed reports require supported entities/claims. Synthetic fixtures do
not establish real corpus coverage or retrieval quality.

## Search contract and joins

`HybridSearch.search(access, QueryPlan(...)) -> SearchResult` is the existing port.
The caller pins `snapshot_id`, `profile_id`, `taxonomy_version_id`, `build_id` and
`embedding_config_hash`; keep the full request and at most five query variants.
Reliable language/family/excluded-document constraints are supported today.
Inferred taxonomy labels never become mandatory filters that suppress vector hits.

The existing query path is:

```text
corpus.snapshots → retrieval.index_builds → retrieval.embedding_configs
retrieval.snapshot_chunks → retrieval.chunks → corpus.document_versions → corpus.documents
                         → retrieval.embeddings (same config + chunk)
retrieval.chunks → retrieval.search_documents (same search_config_hash)
retrieval.chunks → retrieval.chunk_evidence → corpus.evidence_spans
corpus.documents → corpus.sources → corpus.source_family_memberships
```

Lexical and cosine branches run independently, combine via RRF, deduplicate
passages and optionally rerank. Return actual passage text/offsets, evidence IDs,
source URL, separate ranks/scores and snapshot/build pins. A score is relevance,
not factual confidence. `CatalogRepository.entities_for_hits(...)` resolves
pinned accepted claims/support into candidate people/units; downstream evidence
preparation assesses fit and freezes the pack.

Do not write removed plan/hit/match/selection tables. Durable retrieval stage
outputs use `ops.stage_attempts.outputs` (serialize the `QueryPlan`, `SearchResult`,
round and output refs with a round-specific stage identity). Checkpoints and
traces serve their separate purposes. Case-time web tools use `ResearchRepository`
and case scopes; this ingestion task does not publish their discoveries automatically.

## Acceptance and delivery

- Reimport unchanged pages without creating duplicate document versions;
  canonical URLs/aliases and exact body/offsets remain verifiable.
- Publish a real pilot snapshot covering UniBE, ARTORG and DCB; state omissions.
- Query + document vectors use the same config/encoding/dimension; malformed,
  zero and incompatible vectors fail explicitly.
- Lexical-only and semantic-only examples both survive fusion; filters and access
  are applied to both branches; retrieve supporting entity/claim IDs.
- Retain authorization, revocation, snapshots and pack compatibility tests.
  Measure synonym/lay-term Recall@10 against reviewed expert/unit labels.
- Deliver source manifest, publication/snapshot IDs, config hashes, import failures,
  coverage counts and example queries. Never claim a fixture score is model quality.

Exact embedder runtime/model revision, reranker and real dataset quality remain
in [open questions](../project/OPEN_QUESTIONS.md); those are implementation/config
inputs rather than reasons to invent another schema.
