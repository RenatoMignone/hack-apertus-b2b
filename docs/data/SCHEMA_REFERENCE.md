# Exact application schema reference

Generated from `src/backend/data/schema.py`; migration head **`0012_membership_lookup`**.
Do not edit by hand. Regenerate with `PYTHONPATH=src python -m backend.data.schema_docs`.

**65 application tables.** Read [schema decisions](RELATIONAL_SCHEMA.md) and
[ingestion/retrieval handoff](INGESTION_RETRIEVAL_HANDOFF.md) for meanings and write order.
Only these tables are supported for new queries. `alembic_version` is migration-owned;
optional `legacy` history is maintainer-only. Framework tables live outside this database.

UUIDs are supplied by the application. Timestamps are UTC. JSON payload contracts and
database triggers are explained in the owner docs; a nullable field may be omitted.

## `corpus`

### `corpus.active_snapshots`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `profile_id` | `UUID` | yes | `—` | taxonomy.profiles.profile_id |
| `snapshot_id` | `UUID` | yes | `—` | corpus.snapshots.snapshot_id |

Primary key: `profile_id`.

- Index: `snapshot_id`.

### `corpus.artifacts`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `artifact_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `storage_key` | `TEXT` | yes | `—` | — |
| `sha256` | `TEXT` | yes | `—` | — |
| `mime` | `TEXT` | yes | `—` | — |
| `byte_count` | `INTEGER` | yes | `—` | — |
| `status` | `TEXT` | yes | `'available'` | — |

Primary key: `artifact_id`.

- Check: `byte_count >= 0`.
- Check: `sha256 ~ '^[a-f0-9]{64}$'`.
- Unique: `storage_key`.

### `corpus.claim_evidence`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `claim_id` | `UUID` | yes | `—` | corpus.claims.claim_id |
| `evidence_id` | `UUID` | yes | `—` | corpus.evidence_spans.evidence_id |
| `relation` | `TEXT` | yes | `—` | — |
| `review_decision` | `TEXT` | yes | `—` | — |

Primary key: `claim_id, evidence_id`.

- Check: `relation IN ('supports','contradicts')`.
- Index: `evidence_id`.

### `corpus.claims`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `claim_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `scope_id` | `UUID` | yes | `—` | corpus.scopes.scope_id |
| `subject_id` | `UUID` | yes | `—` | corpus.entities.entity_id |
| `predicate` | `TEXT` | yes | `—` | — |
| `object_entity_id` | `UUID` | no | `—` | corpus.entities.entity_id |
| `typed_literal` | `JSONB` | no | `—` | — |
| `derivation_id` | `UUID` | no | `—` | corpus.derivations.derivation_id |
| `supersedes_id` | `UUID` | no | `—` | corpus.claims.claim_id |
| `status` | `TEXT` | yes | `'needs_review'` | — |

Primary key: `claim_id`.

- Check: `(object_entity_id IS NULL) <> (typed_literal IS NULL)`.
- Check: `length(btrim(predicate)) > 0`.
- Check: `status IN ('draft','accepted','needs_review','rejected')`.
- Check: `typed_literal IS NULL OR (jsonb_typeof(typed_literal)='object' AND typed_literal ? 'type' AND typed_literal ? 'value')`.
- Index: `derivation_id`.
- Index: `object_entity_id`.
- Index: `scope_id`.
- Index: `subject_id`.
- Index: `supersedes_id`.

### `corpus.derivations`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `derivation_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `scope_id` | `UUID` | yes | `—` | corpus.scopes.scope_id |
| `inputs` | `JSONB` | yes | `'{}'::jsonb` | — |
| `model_config_id` | `UUID` | no | `—` | ops.model_configurations.model_config_id |
| `configuration_hash` | `TEXT` | yes | `—` | — |
| `output_hash` | `TEXT` | yes | `—` | — |
| `status` | `TEXT` | yes | `'draft'` | — |
| `diagnostics` | `JSONB` | yes | `'{}'::jsonb` | — |

Primary key: `derivation_id`.

- Index: `model_config_id`.
- Index: `scope_id`.

### `corpus.document_aliases`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `alias_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `document_id` | `UUID` | yes | `—` | corpus.documents.document_id |
| `url` | `TEXT` | yes | `—` | — |

Primary key: `alias_id`.

- Unique: `document_id, url`.
- Index: `document_id`.
- Index: `url`.

### `corpus.document_versions`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `document_version_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `document_id` | `UUID` | yes | `—` | corpus.documents.document_id |
| `scope_id` | `UUID` | yes | `—` | corpus.scopes.scope_id |
| `raw_artifact_id` | `UUID` | yes | `—` | corpus.artifacts.artifact_id |
| `body_artifact_id` | `UUID` | yes | `—` | corpus.artifacts.artifact_id |
| `body_hash` | `TEXT` | yes | `—` | — |
| `body_text` | `TEXT` | yes | `—` | — |
| `parser_hash` | `TEXT` | yes | `—` | — |
| `language` | `TEXT` | yes | `—` | — |
| `title` | `TEXT` | yes | `—` | — |
| `source_date` | `TIMESTAMP WITH TIME ZONE` | no | `—` | — |
| `status` | `TEXT` | yes | `'accepted'` | — |

Primary key: `document_version_id`.

- Check: `status IN ('accepted','needs_review','rejected')`.
- Unique: `document_id, body_hash, parser_hash`.
- Index: `body_artifact_id`.
- Index: `document_id`.
- Index: `raw_artifact_id`.
- Index: `scope_id`.

### `corpus.documents`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `document_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `source_id` | `UUID` | yes | `—` | corpus.sources.source_id |
| `scope_id` | `UUID` | yes | `—` | corpus.scopes.scope_id |
| `canonical_url` | `TEXT` | yes | `—` | — |

Primary key: `document_id`.

- Unique: `scope_id, canonical_url`.
- Index: `scope_id`.
- Index: `source_id`.

### `corpus.entities`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `entity_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `scope_id` | `UUID` | yes | `—` | corpus.scopes.scope_id |
| `entity_type` | `TEXT` | yes | `—` | — |
| `display_label` | `TEXT` | yes | `—` | — |
| `status` | `TEXT` | yes | `'needs_review'` | — |

Primary key: `entity_id`.

- Check: `length(btrim(display_label)) > 0`.
- Check: `entity_type IN ('person','unit','organization','project','facility','service')`.
- Index: `scope_id`.

### `corpus.entity_identifiers`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `identifier_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `entity_id` | `UUID` | yes | `—` | corpus.entities.entity_id |
| `kind` | `TEXT` | yes | `—` | — |
| `identifier_value` | `TEXT` | yes | `—` | — |
| `authority` | `TEXT` | yes | `—` | — |
| `evidence_id` | `UUID` | yes | `—` | corpus.evidence_spans.evidence_id |
| `verified` | `BOOLEAN` | yes | `false` | — |

Primary key: `identifier_id`.

- Index: `entity_id`.
- Index: `evidence_id`.
- Unique index: `authority, kind, identifier_value` where `entity_identifiers.verified`.

### `corpus.evidence_spans`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `evidence_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `document_version_id` | `UUID` | yes | `—` | corpus.document_versions.document_version_id |
| `scope_id` | `UUID` | yes | `—` | corpus.scopes.scope_id |
| `char_start` | `INTEGER` | yes | `—` | — |
| `char_end` | `INTEGER` | yes | `—` | — |
| `literal_text` | `TEXT` | yes | `—` | — |
| `heading_path` | `JSONB` | yes | `'[]'::jsonb` | — |
| `page` | `INTEGER` | no | `—` | — |
| `extraction_method` | `TEXT` | yes | `—` | — |

Primary key: `evidence_id`.

- Check: `char_start >= 0 AND char_end > char_start`.
- Unique: `document_version_id, char_start, char_end`.
- Index: `document_version_id`.
- Index: `scope_id`.

### `corpus.fetches`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `fetch_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `document_id` | `UUID` | yes | `—` | corpus.documents.document_id |
| `job_id` | `UUID` | no | `—` | ops.ingest_jobs.job_id |
| `requested_url` | `TEXT` | yes | `—` | — |
| `final_url` | `TEXT` | yes | `—` | — |
| `http_status` | `INTEGER` | no | `—` | — |
| `raw_artifact_id` | `UUID` | no | `—` | corpus.artifacts.artifact_id |
| `headers` | `JSONB` | yes | `'{}'::jsonb` | — |
| `redirects` | `JSONB` | yes | `'{}'::jsonb` | — |
| `failure` | `TEXT` | no | `—` | — |

Primary key: `fetch_id`.

- Index: `document_id`.
- Index: `job_id`.
- Index: `raw_artifact_id`.

### `corpus.scopes`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `scope_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `kind` | `TEXT` | yes | `—` | — |
| `case_id` | `UUID` | no | `—` | cases.cases.case_id |
| `access_policy_id` | `TEXT` | yes | `—` | — |
| `revoked` | `BOOLEAN` | yes | `false` | — |

Primary key: `scope_id`.

- Check: `(kind='public' AND case_id IS NULL) OR (kind='case' AND case_id IS NOT NULL)`.
- Index: `case_id`.

### `corpus.snapshot_claims`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `snapshot_id` | `UUID` | yes | `—` | corpus.snapshots.snapshot_id |
| `claim_id` | `UUID` | yes | `—` | corpus.claims.claim_id |

Primary key: `snapshot_id, claim_id`.


### `corpus.snapshot_documents`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `snapshot_id` | `UUID` | yes | `—` | corpus.snapshots.snapshot_id |
| `document_version_id` | `UUID` | yes | `—` | corpus.document_versions.document_version_id |

Primary key: `snapshot_id, document_version_id`.


### `corpus.snapshot_entities`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `snapshot_id` | `UUID` | yes | `—` | corpus.snapshots.snapshot_id |
| `entity_id` | `UUID` | yes | `—` | corpus.entities.entity_id |

Primary key: `snapshot_id, entity_id`.


### `corpus.snapshots`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `snapshot_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `profile_id` | `UUID` | yes | `—` | taxonomy.profiles.profile_id |
| `taxonomy_version_id` | `UUID` | yes | `—` | taxonomy.versions.taxonomy_version_id |
| `build_id` | `UUID` | yes | `—` | retrieval.index_builds.build_id |
| `namespace` | `TEXT` | yes | `—` | — |
| `schema_version` | `TEXT` | yes | `—` | — |
| `manifest_hash` | `TEXT` | yes | `—` | — |
| `manifest` | `JSONB` | yes | `'{}'::jsonb` | — |
| `status` | `TEXT` | yes | `'draft'` | — |
| `published_at` | `TIMESTAMP WITH TIME ZONE` | no | `—` | — |

Primary key: `snapshot_id`.

- Check: `status IN ('draft','published','failed','live')`.
- Index: `build_id`.
- Index: `profile_id`.
- Index: `taxonomy_version_id`.

### `corpus.source_families`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `family_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `name` | `TEXT` | yes | `—` | — |

Primary key: `family_id`.

- Unique: `name`.

### `corpus.source_family_memberships`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `source_id` | `UUID` | yes | `—` | corpus.sources.source_id |
| `family_id` | `UUID` | yes | `—` | corpus.source_families.family_id |

Primary key: `source_id, family_id`.


### `corpus.sources`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `source_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `scope_id` | `UUID` | yes | `—` | corpus.scopes.scope_id |
| `canonical_origin` | `TEXT` | yes | `—` | — |
| `registry_ref` | `TEXT` | yes | `—` | — |
| `status` | `TEXT` | yes | `'active'` | — |

Primary key: `source_id`.

- Index: `scope_id`.

## `taxonomy`

### `taxonomy.assignment_evidence`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `assignment_id` | `UUID` | yes | `—` | taxonomy.assignments.assignment_id |
| `evidence_id` | `UUID` | yes | `—` | corpus.evidence_spans.evidence_id |

Primary key: `assignment_id, evidence_id`.


### `taxonomy.assignments`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `assignment_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `scope_id` | `UUID` | yes | `—` | corpus.scopes.scope_id |
| `concept_id` | `UUID` | yes | `—` | taxonomy.concepts.concept_id |
| `document_version_id` | `UUID` | no | `—` | corpus.document_versions.document_version_id |
| `entity_id` | `UUID` | no | `—` | corpus.entities.entity_id |
| `chunk_id` | `UUID` | no | `—` | retrieval.chunks.chunk_id |
| `derivation_id` | `UUID` | no | `—` | corpus.derivations.derivation_id |
| `mapping_kind` | `TEXT` | yes | `—` | — |
| `status` | `TEXT` | yes | `'draft'` | — |

Primary key: `assignment_id`.

- Check: `mapping_kind IN ('direct','related')`.
- Check: `num_nonnulls(document_version_id, entity_id, chunk_id)=1`.
- Check: `status IN ('draft','accepted','needs_review','rejected')`.
- Index: `chunk_id`.
- Index: `concept_id`.
- Index: `derivation_id`.
- Index: `document_version_id`.
- Index: `entity_id`.
- Index: `scope_id`.

### `taxonomy.concepts`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `concept_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `taxonomy_version_id` | `UUID` | yes | `—` | taxonomy.versions.taxonomy_version_id |
| `code` | `TEXT` | yes | `—` | — |
| `definition` | `TEXT` | yes | `—` | — |
| `facet` | `TEXT` | yes | `—` | — |
| `notes` | `JSONB` | yes | `'{}'::jsonb` | — |

Primary key: `concept_id`.

- Unique: `taxonomy_version_id, code`.
- Index: `taxonomy_version_id`.

### `taxonomy.labels`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `label_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `concept_id` | `UUID` | yes | `—` | taxonomy.concepts.concept_id |
| `language` | `TEXT` | yes | `—` | — |
| `label` | `TEXT` | yes | `—` | — |
| `preferred` | `BOOLEAN` | yes | `—` | — |
| `ambiguity` | `JSONB` | yes | `'{}'::jsonb` | — |

Primary key: `label_id`.

- Index: `concept_id`.

### `taxonomy.profiles`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `profile_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `name` | `TEXT` | yes | `—` | — |
| `namespace` | `TEXT` | yes | `—` | — |
| `version` | `TEXT` | yes | `—` | — |
| `schema_version` | `TEXT` | yes | `—` | — |
| `config_hash` | `TEXT` | yes | `—` | — |
| `configuration` | `JSONB` | yes | `'{}'::jsonb` | — |

Primary key: `profile_id`.

- Unique: `namespace, name, version`.

### `taxonomy.relations`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `subject_id` | `UUID` | yes | `—` | taxonomy.concepts.concept_id |
| `object_id` | `UUID` | yes | `—` | taxonomy.concepts.concept_id |
| `kind` | `TEXT` | yes | `—` | — |

Primary key: `subject_id, object_id`.

- Check: `kind IN ('broader','narrower','related')`.

### `taxonomy.versions`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `taxonomy_version_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `name` | `TEXT` | yes | `—` | — |
| `version` | `TEXT` | yes | `—` | — |
| `artifact_hash` | `TEXT` | yes | `—` | — |
| `status` | `TEXT` | yes | `'reviewed'` | — |

Primary key: `taxonomy_version_id`.

- Unique: `name, version`.

## `retrieval`

### `retrieval.chunk_evidence`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `chunk_id` | `UUID` | yes | `—` | retrieval.chunks.chunk_id |
| `evidence_id` | `UUID` | yes | `—` | corpus.evidence_spans.evidence_id |

Primary key: `chunk_id, evidence_id`.

- Index: `evidence_id`.

### `retrieval.chunks`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `chunk_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `document_version_id` | `UUID` | yes | `—` | corpus.document_versions.document_version_id |
| `scope_id` | `UUID` | yes | `—` | corpus.scopes.scope_id |
| `char_start` | `INTEGER` | yes | `—` | — |
| `char_end` | `INTEGER` | yes | `—` | — |
| `literal_text` | `TEXT` | yes | `—` | — |
| `title` | `TEXT` | yes | `—` | — |
| `heading_path` | `JSONB` | yes | `'[]'::jsonb` | — |
| `language` | `TEXT` | yes | `—` | — |
| `chunker_hash` | `TEXT` | yes | `—` | — |

Primary key: `chunk_id`.

- Check: `char_start >= 0 AND char_end > char_start`.
- Unique: `document_version_id, char_start, char_end, chunker_hash`.
- Index: `document_version_id`.
- Index: `scope_id`.

### `retrieval.embedding_configs`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `config_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `model_config_id` | `UUID` | yes | `—` | ops.model_configurations.model_config_id |
| `config_hash` | `TEXT` | yes | `—` | — |
| `dimension` | `INTEGER` | yes | `—` | — |
| `encoding` | `JSONB` | yes | `'{}'::jsonb` | — |

Primary key: `config_id`.

- Check: `dimension > 0`.
- Unique: `config_hash`.
- Index: `model_config_id`.

### `retrieval.embeddings`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `embedding_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `chunk_id` | `UUID` | yes | `—` | retrieval.chunks.chunk_id |
| `config_id` | `UUID` | yes | `—` | retrieval.embedding_configs.config_id |
| `input_hash` | `TEXT` | yes | `—` | — |
| `input_text` | `TEXT` | yes | `—` | — |
| `vector` | `VECTOR` | yes | `—` | — |

Primary key: `embedding_id`.

- Unique: `chunk_id, config_id, input_hash`.
- Index: `chunk_id`.
- Index: `config_id`.

### `retrieval.index_builds`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `build_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `config_id` | `UUID` | yes | `—` | retrieval.embedding_configs.config_id |
| `namespace` | `TEXT` | yes | `—` | — |
| `chunker_hash` | `TEXT` | yes | `—` | — |
| `search_config_hash` | `TEXT` | yes | `—` | — |
| `status` | `TEXT` | yes | `'draft'` | — |
| `validation_manifest` | `JSONB` | yes | `'{}'::jsonb` | — |

Primary key: `build_id`.

- Check: `status IN ('draft','published','failed','live')`.
- Index: `config_id`.

### `retrieval.search_documents`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `projection_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `chunk_id` | `UUID` | yes | `—` | retrieval.chunks.chunk_id |
| `search_config_hash` | `TEXT` | yes | `—` | — |
| `language_config` | `TEXT` | yes | `—` | — |
| `terms` | `TSVECTOR` | yes | `—` | — |

Primary key: `projection_id`.

- Unique: `chunk_id, search_config_hash, language_config`.
- Index: `chunk_id`.
- Index: `terms`.

### `retrieval.snapshot_chunks`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `snapshot_id` | `UUID` | yes | `—` | corpus.snapshots.snapshot_id |
| `chunk_id` | `UUID` | yes | `—` | retrieval.chunks.chunk_id |
| `embedding_id` | `UUID` | yes | `—` | retrieval.embeddings.embedding_id |

Primary key: `snapshot_id, chunk_id`.

- Index: `embedding_id`.

## `cases`

### `cases.action_items`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `action_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `case_id` | `UUID` | yes | `—` | cases.cases.case_id |
| `question` | `TEXT` | yes | `—` | — |
| `ask_role` | `TEXT` | yes | `—` | — |
| `status` | `TEXT` | yes | `'open'` | — |
| `answer` | `TEXT` | no | `—` | — |

Primary key: `action_id`.

- Check: `status IN ('open','asked','done')`.
- Index: `case_id`.

### `cases.answers`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `answer_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `question_id` | `UUID` | yes | `—` | cases.questions.question_id |
| `turn_id` | `UUID` | yes | `—` | cases.dialogue_turns.turn_id |

Primary key: `answer_id`.

- Unique: `question_id`.
- Index: `question_id`.
- Index: `turn_id`.

### `cases.business_contexts`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `context_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `case_id` | `UUID` | yes | `—` | cases.cases.case_id |
| `input_id` | `UUID` | yes | `—` | cases.input_revisions.input_id |
| `entered_by` | `UUID` | yes | `—` | ops.principals.principal_id |
| `payload` | `JSONB` | yes | `'{}'::jsonb` | — |

Primary key: `context_id`.

- Unique: `input_id`.
- Index: `case_id`.
- Index: `entered_by`.
- Index: `input_id`.

### `cases.case_evidence_items`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `item_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `manifest_id` | `UUID` | yes | `—` | cases.case_evidence_manifests.manifest_id |
| `evidence_id` | `UUID` | yes | `—` | corpus.evidence_spans.evidence_id |

Primary key: `item_id`.

- Unique: `manifest_id, evidence_id`.
- Index: `evidence_id`.
- Index: `manifest_id`.

### `cases.case_evidence_manifests`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `manifest_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `case_id` | `UUID` | yes | `—` | cases.cases.case_id |
| `parent_id` | `UUID` | no | `—` | cases.case_evidence_manifests.manifest_id |
| `manifest_hash` | `TEXT` | yes | `—` | — |

Primary key: `manifest_id`.

- Index: `case_id`.
- Index: `parent_id`.

### `cases.cases`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `case_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `owner_id` | `UUID` | yes | `—` | ops.principals.principal_id |
| `namespace` | `TEXT` | yes | `—` | — |
| `status` | `TEXT` | yes | `'draft'` | — |
| `revision` | `INTEGER` | yes | `0` | — |
| `on_hold` | `BOOLEAN` | yes | `false` | — |
| `outcome` | `TEXT` | no | `—` | — |
| `current_input_id` | `UUID` | no | `—` | cases.input_revisions.input_id |
| `current_result_id` | `UUID` | no | `—` | cases.result_revisions.result_id |

Primary key: `case_id`.

- Check: `outcome IN ('visit','no_interest')`.
- Index: `current_input_id`.
- Index: `current_result_id`.
- Index: `owner_id`.

### `cases.claim_assessments`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `assessment_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `run_id` | `UUID` | yes | `—` | cases.runs.run_id |
| `claim_id` | `UUID` | yes | `—` | corpus.claims.claim_id |
| `status` | `TEXT` | yes | `—` | — |
| `payload` | `JSONB` | yes | `'{}'::jsonb` | — |

Primary key: `assessment_id`.

- Check: `status IN ('supported','unsupported','contradicted')`.
- Unique: `run_id, claim_id`.
- Index: `claim_id`.
- Index: `run_id`.

### `cases.dialogue_turns`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `turn_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `case_id` | `UUID` | yes | `—` | cases.cases.case_id |
| `role` | `TEXT` | yes | `—` | — |
| `message` | `TEXT` | yes | `—` | — |
| `input_id` | `UUID` | no | `—` | cases.input_revisions.input_id |

Primary key: `turn_id`.

- Check: `role IN ('user','assistant','system')`.
- Index: `case_id`.
- Index: `input_id`.

### `cases.draft_reasons`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `reason_row_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `result_id` | `UUID` | yes | `—` | cases.result_revisions.result_id |
| `reason_key` | `TEXT` | yes | `—` | — |
| `support_hash` | `TEXT` | yes | `—` | — |
| `payload` | `JSONB` | yes | `'{}'::jsonb` | — |

Primary key: `reason_row_id`.

- Unique: `result_id, reason_key`.
- Index: `result_id`.

### `cases.evidence_packs`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `pack_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `run_id` | `UUID` | yes | `—` | cases.runs.run_id |
| `input_id` | `UUID` | yes | `—` | cases.input_revisions.input_id |
| `manifest_id` | `UUID` | no | `—` | cases.case_evidence_manifests.manifest_id |
| `pack_hash` | `TEXT` | yes | `—` | — |
| `payload` | `JSONB` | yes | `'{}'::jsonb` | — |
| `status` | `TEXT` | yes | `'frozen'` | — |

Primary key: `pack_id`.

- Index: `input_id`.
- Index: `manifest_id`.
- Index: `run_id`.

### `cases.exports`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `export_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `result_id` | `UUID` | yes | `—` | cases.result_revisions.result_id |
| `review_id` | `UUID` | yes | `—` | cases.reviews.review_id |
| `artifact_id` | `UUID` | yes | `—` | corpus.artifacts.artifact_id |
| `template_version` | `TEXT` | yes | `—` | — |
| `renderer_version` | `TEXT` | yes | `—` | — |
| `selection_hash` | `TEXT` | yes | `—` | — |
| `status` | `TEXT` | yes | `'ready'` | — |
| `format` | `TEXT` | yes | `'pdf'` | — |

Primary key: `export_id`.

- Index: `artifact_id`.
- Index: `result_id`.
- Index: `review_id`.

### `cases.input_revisions`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `input_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `case_id` | `UUID` | yes | `—` | cases.cases.case_id |
| `parent_id` | `UUID` | no | `—` | cases.input_revisions.input_id |
| `message` | `TEXT` | yes | `—` | — |

Primary key: `input_id`.

- Index: `case_id`.
- Index: `parent_id`.

### `cases.interpretations`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `interpretation_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `run_id` | `UUID` | yes | `—` | cases.runs.run_id |
| `payload` | `JSONB` | yes | `'{}'::jsonb` | — |

Primary key: `interpretation_id`.

- Unique: `run_id`.
- Index: `run_id`.

### `cases.memory_profiles`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `memory_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `case_id` | `UUID` | yes | `—` | cases.cases.case_id |
| `input_id` | `UUID` | yes | `—` | cases.input_revisions.input_id |
| `result_id` | `UUID` | yes | `—` | cases.result_revisions.result_id |
| `owner_id` | `UUID` | yes | `—` | ops.principals.principal_id |
| `namespace` | `TEXT` | yes | `—` | — |
| `projection_hash` | `TEXT` | yes | `—` | — |
| `embedding_config_hash` | `TEXT` | yes | `—` | — |
| `dimension` | `INTEGER` | yes | `—` | — |
| `embedding` | `VECTOR` | yes | `—` | — |
| `payload` | `JSONB` | yes | `'{}'::jsonb` | — |
| `enabled` | `BOOLEAN` | yes | `true` | — |

Primary key: `memory_id`.

- Check: `dimension > 0 AND vector_dims(embedding)=dimension`.
- Unique: `case_id, input_id, projection_hash, embedding_config_hash`.
- Index: `case_id`.
- Index: `input_id`.
- Index: `owner_id`.
- Index: `result_id`.
- Index: `owner_id, namespace, embedding_config_hash`.
- Index: `embedding` where `cases.memory_profiles.dimension = :dimension_1`.

### `cases.pack_claims`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `pack_id` | `UUID` | yes | `—` | cases.evidence_packs.pack_id |
| `claim_id` | `UUID` | yes | `—` | corpus.claims.claim_id |

Primary key: `pack_id, claim_id`.


### `cases.pack_items`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `pack_id` | `UUID` | yes | `—` | cases.evidence_packs.pack_id |
| `evidence_id` | `UUID` | yes | `—` | corpus.evidence_spans.evidence_id |

Primary key: `pack_id, evidence_id`.

- Index: `evidence_id`.

### `cases.questions`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `question_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `run_id` | `UUID` | yes | `—` | cases.runs.run_id |
| `input_id` | `UUID` | yes | `—` | cases.input_revisions.input_id |
| `field` | `TEXT` | yes | `—` | — |
| `reason` | `TEXT` | yes | `—` | — |
| `required` | `BOOLEAN` | yes | `—` | — |
| `status` | `TEXT` | yes | `'open'` | — |

Primary key: `question_id`.

- Index: `input_id`.
- Index: `run_id`.

### `cases.reason_claims`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `reason_row_id` | `UUID` | yes | `—` | cases.draft_reasons.reason_row_id |
| `claim_id` | `UUID` | yes | `—` | corpus.claims.claim_id |

Primary key: `reason_row_id, claim_id`.


### `cases.reason_selections`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `reason_row_id` | `UUID` | yes | `—` | cases.draft_reasons.reason_row_id |
| `selection` | `TEXT` | yes | `—` | — |
| `reviewer_id` | `UUID` | yes | `—` | ops.principals.principal_id |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |

Primary key: `reason_row_id`.

- Check: `selection IN ('none','kept','rejected')`.
- Index: `reviewer_id`.

### `cases.result_revisions`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `result_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `case_id` | `UUID` | yes | `—` | cases.cases.case_id |
| `pack_id` | `UUID` | yes | `—` | cases.evidence_packs.pack_id |
| `parent_id` | `UUID` | no | `—` | cases.result_revisions.result_id |
| `instruction` | `TEXT` | yes | `—` | — |
| `result_hash` | `TEXT` | yes | `—` | — |
| `payload` | `JSONB` | yes | `'{}'::jsonb` | — |
| `status` | `TEXT` | yes | `'draft'` | — |

Primary key: `result_id`.

- Index: `case_id`.
- Index: `pack_id`.
- Index: `parent_id`.

### `cases.reviews`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `review_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `result_id` | `UUID` | yes | `—` | cases.result_revisions.result_id |
| `reviewer_id` | `UUID` | yes | `—` | ops.principals.principal_id |
| `result_hash` | `TEXT` | yes | `—` | — |
| `decision` | `TEXT` | yes | `—` | — |
| `selection_hash` | `TEXT` | no | `—` | — |

Primary key: `review_id`.

- Check: `decision IN ('accepted','rejected')`.
- Index: `result_id`.
- Index: `reviewer_id`.

### `cases.runs`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `run_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `case_id` | `UUID` | yes | `—` | cases.cases.case_id |
| `input_id` | `UUID` | yes | `—` | cases.input_revisions.input_id |
| `snapshot_id` | `UUID` | yes | `—` | corpus.snapshots.snapshot_id |
| `thread_id` | `UUID` | yes | `—` | — |
| `status` | `TEXT` | yes | `'draft'` | — |
| `configuration` | `JSONB` | yes | `'{}'::jsonb` | — |
| `trace_id` | `TEXT` | no | `—` | — |
| `last_successful_stage` | `TEXT` | no | `—` | — |
| `failure_reason` | `TEXT` | no | `—` | — |

Primary key: `run_id`.

- Unique: `thread_id`.
- Index: `case_id`.
- Index: `input_id`.
- Index: `snapshot_id`.

### `cases.web_research`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `research_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `run_id` | `UUID` | yes | `—` | cases.runs.run_id |
| `query` | `TEXT` | yes | `—` | — |
| `mode` | `TEXT` | yes | `—` | — |
| `status` | `TEXT` | yes | `'pending'` | — |
| `diagnostics` | `JSONB` | yes | `'{}'::jsonb` | — |

Primary key: `research_id`.

- Check: `mode IN ('connected','offline')`.
- Check: `status IN ('pending','completed','unavailable','failed')`.
- Index: `run_id`.

### `cases.web_sources`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `discovery_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `research_id` | `UUID` | yes | `—` | cases.web_research.research_id |
| `canonical_url` | `TEXT` | yes | `—` | — |
| `document_version_id` | `UUID` | no | `—` | corpus.document_versions.document_version_id |
| `duplicate_version_id` | `UUID` | no | `—` | corpus.document_versions.document_version_id |
| `payload` | `JSONB` | yes | `'{}'::jsonb` | — |

Primary key: `discovery_id`.

- Check: `num_nonnulls(document_version_id,duplicate_version_id)=1`.
- Unique: `research_id, canonical_url`.
- Index: `document_version_id`.
- Index: `duplicate_version_id`.
- Index: `research_id`.

## `ops`

### `ops.ingest_jobs`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `job_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `namespace` | `TEXT` | yes | `—` | — |
| `scope_id` | `UUID` | yes | `—` | corpus.scopes.scope_id |
| `profile_id` | `UUID` | no | `—` | taxonomy.profiles.profile_id |
| `base_snapshot_id` | `UUID` | no | `—` | corpus.snapshots.snapshot_id |
| `configuration_hash` | `TEXT` | yes | `—` | — |
| `status` | `TEXT` | yes | `'draft'` | — |
| `budgets` | `JSONB` | yes | `'{}'::jsonb` | — |
| `counters` | `JSONB` | yes | `'{}'::jsonb` | — |

Primary key: `job_id`.

- Index: `base_snapshot_id`.
- Index: `profile_id`.
- Index: `scope_id`.

### `ops.model_configurations`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `model_config_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `role` | `TEXT` | yes | `—` | — |
| `config_hash` | `TEXT` | yes | `—` | — |
| `configuration` | `JSONB` | yes | `'{}'::jsonb` | — |
| `verified` | `BOOLEAN` | yes | `—` | — |
| `test_only` | `BOOLEAN` | yes | `—` | — |

Primary key: `model_config_id`.

- Unique: `config_hash`.

### `ops.outbox`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `event_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `namespace` | `TEXT` | yes | `—` | — |
| `run_id` | `UUID` | no | `—` | cases.runs.run_id |
| `idempotency_key` | `TEXT` | yes | `—` | — |
| `event_type` | `TEXT` | yes | `—` | — |
| `payload` | `JSONB` | yes | `'{}'::jsonb` | — |
| `status` | `TEXT` | yes | `'pending'` | — |
| `worker_id` | `TEXT` | no | `—` | — |
| `lease_until` | `TIMESTAMP WITH TIME ZONE` | no | `—` | — |
| `attempts` | `INTEGER` | yes | `0` | — |
| `next_retry` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |

Primary key: `event_id`.

- Check: `status IN ('pending','running','delivered','failed')`.
- Unique: `idempotency_key`.
- Index: `run_id`.

### `ops.principals`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `principal_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `database_role` | `TEXT` | yes | `—` | — |
| `namespace` | `TEXT` | yes | `—` | — |
| `active` | `BOOLEAN` | yes | `true` | — |

Primary key: `principal_id`.

- Unique: `database_role, namespace`.

### `ops.publication_checks`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `check_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `snapshot_id` | `UUID` | yes | `—` | corpus.snapshots.snapshot_id |
| `validator` | `TEXT` | yes | `—` | — |
| `version` | `TEXT` | yes | `—` | — |
| `passed` | `BOOLEAN` | yes | `—` | — |
| `manifest_hash` | `TEXT` | yes | `—` | — |

Primary key: `check_id`.

- Unique: `snapshot_id, validator`.
- Index: `snapshot_id`.

### `ops.scope_grants`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `principal_id` | `UUID` | yes | `—` | ops.principals.principal_id |
| `scope_id` | `UUID` | yes | `—` | corpus.scopes.scope_id |
| `can_write` | `BOOLEAN` | yes | `false` | — |

Primary key: `principal_id, scope_id`.


### `ops.stage_attempts`

| Column | Type | Required | Default | References |
| --- | --- | --- | --- | --- |
| `attempt_id` | `UUID` | yes | `—` | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | yes | `now()` | — |
| `run_id` | `UUID` | no | `—` | cases.runs.run_id |
| `job_id` | `UUID` | no | `—` | ops.ingest_jobs.job_id |
| `namespace` | `TEXT` | yes | `—` | — |
| `stage` | `TEXT` | yes | `—` | — |
| `input_hash` | `TEXT` | yes | `—` | — |
| `config_hash` | `TEXT` | yes | `—` | — |
| `idempotency_key` | `TEXT` | yes | `—` | — |
| `status` | `TEXT` | yes | `'pending'` | — |
| `worker_id` | `TEXT` | no | `—` | — |
| `lease_until` | `TIMESTAMP WITH TIME ZONE` | no | `—` | — |
| `attempt_count` | `INTEGER` | yes | `0` | — |
| `outputs` | `JSONB` | yes | `'{}'::jsonb` | — |

Primary key: `attempt_id`.

- Check: `num_nonnulls(run_id,job_id)=1`.
- Check: `status IN ('pending','running','committed','failed')`.
- Unique: `idempotency_key`.
- Index: `job_id`.
- Index: `run_id`.
