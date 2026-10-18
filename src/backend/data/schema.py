"""Final application tables. Historical migrations use their frozen baseline metadata.

See docs/data/SCHEMA_REFERENCE.md for the generated field inventory and
INGESTION_RETRIEVAL_HANDOFF.md for the supported write/search path.
"""
from sqlalchemy import (Boolean, CheckConstraint, Column, DateTime, ForeignKey, ForeignKeyConstraint,
                        Index, Integer, MetaData, Table, Text, UniqueConstraint, text)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID
from pgvector.sqlalchemy import Vector


SCHEMA_REVISION = "0005_finalize_schema"

metadata = MetaData(naming_convention={"ix": "ix_%(table_name)s_%(column_0_name)s",
                                      "uq": "uq_%(table_name)s_%(column_0_name)s",
                                      "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
                                      "pk": "pk_%(table_name)s"})


def uid(name, target=None, nullable=False, primary_key=False):
    arguments = [ForeignKey(target, ondelete="RESTRICT")] if target else []
    return Column(name, UUID(as_uuid=True), *arguments, nullable=nullable, primary_key=primary_key)


def value(name, kind=Text, nullable=False, default=None):
    return Column(name, kind, nullable=nullable, server_default=default)


def payload(name="payload"):
    return value(name, JSONB, default=text("'{}'::jsonb"))


def state(default="draft"):
    return value("status", default=text(f"'{default}'"))


def scoped():
    return uid("scope_id", "corpus.scopes.scope_id", nullable=False)


def table(schema, name, identity, *columns):
    return Table(name, metadata, uid(identity, primary_key=True),
                 value("created_at", DateTime(timezone=True), default=text("now()")), *columns, schema=schema)


principals = table("ops", "principals", "principal_id", value("database_role"), value("namespace"),
                   value("active", Boolean, default=text("true")), UniqueConstraint("database_role", "namespace"))
cases = table("cases", "cases", "case_id", uid("owner_id", "ops.principals.principal_id"),
              value("namespace"), state(), value("revision", Integer, default=text("0")),
              uid("current_input_id", nullable=True), uid("current_result_id", nullable=True),
              ForeignKeyConstraint(["current_input_id"], ["cases.input_revisions.input_id"], name="current_input_fk",
                                   deferrable=True, initially="DEFERRED", use_alter=True),
              ForeignKeyConstraint(["current_result_id"], ["cases.result_revisions.result_id"], name="current_result_fk",
                                   deferrable=True, initially="DEFERRED", use_alter=True))
scopes = table("corpus", "scopes", "scope_id", value("kind"),
               uid("case_id", "cases.cases.case_id", nullable=True), value("access_policy_id"),
               value("revoked", Boolean, default=text("false")),
               CheckConstraint("(kind='public' AND case_id IS NULL) OR (kind='case' AND case_id IS NOT NULL)"))
scope_grants = Table("scope_grants", metadata, uid("principal_id", "ops.principals.principal_id", primary_key=True),
                     uid("scope_id", "corpus.scopes.scope_id", primary_key=True),
                     value("can_write", Boolean, default=text("false")), schema="ops")
artifacts = table("corpus", "artifacts", "artifact_id", value("storage_key"), value("sha256"),
                  value("mime"), value("byte_count", Integer), state("available"),
                  UniqueConstraint("storage_key"), CheckConstraint("byte_count >= 0"),
                  CheckConstraint("sha256 ~ '^[a-f0-9]{64}$'"))
sources = table("corpus", "sources", "source_id", scoped(), value("canonical_origin"), value("registry_ref"), state("active"))
families = table("corpus", "source_families", "family_id", value("name"), UniqueConstraint("name"))
family_memberships = Table("source_family_memberships", metadata,
                           uid("source_id", "corpus.sources.source_id", primary_key=True),
                           uid("family_id", "corpus.source_families.family_id", primary_key=True), schema="corpus")
documents = table("corpus", "documents", "document_id", uid("source_id", "corpus.sources.source_id"),
                  scoped(), value("canonical_url"), UniqueConstraint("scope_id", "canonical_url"))
aliases = table("corpus", "document_aliases", "alias_id", uid("document_id", "corpus.documents.document_id"), value("url"))
jobs = table("ops", "ingest_jobs", "job_id", value("namespace"), scoped(), uid("profile_id", "taxonomy.profiles.profile_id", nullable=True),
             uid("base_snapshot_id", "corpus.snapshots.snapshot_id", nullable=True), value("configuration_hash"), state(), payload("budgets"), payload("counters"))
fetches = table("corpus", "fetches", "fetch_id", uid("document_id", "corpus.documents.document_id"),
                uid("job_id", "ops.ingest_jobs.job_id", nullable=True), value("requested_url"), value("final_url"),
                value("http_status", Integer, nullable=True), uid("raw_artifact_id", "corpus.artifacts.artifact_id", nullable=True),
                payload("headers"), payload("redirects"), value("failure", nullable=True))
versions = table("corpus", "document_versions", "document_version_id", uid("document_id", "corpus.documents.document_id"),
                 scoped(), uid("raw_artifact_id", "corpus.artifacts.artifact_id"),
                 uid("body_artifact_id", "corpus.artifacts.artifact_id"), value("body_hash"), value("body_text"),
                 value("parser_hash"), value("language"), value("title"), value("source_date", DateTime(timezone=True), nullable=True),
                 state("accepted"), UniqueConstraint("document_id", "body_hash", "parser_hash"))
spans = table("corpus", "evidence_spans", "evidence_id", uid("document_version_id", "corpus.document_versions.document_version_id"),
              scoped(), value("char_start", Integer), value("char_end", Integer), value("literal_text"),
              value("heading_path", JSONB, default=text("'[]'::jsonb")), value("page", Integer, nullable=True),
              value("extraction_method"), CheckConstraint("char_start >= 0 AND char_end > char_start"),
              UniqueConstraint("document_version_id", "char_start", "char_end"))
entities = table("corpus", "entities", "entity_id", scoped(), value("entity_type"), value("display_label"), state("needs_review"))
identifiers = table("corpus", "entity_identifiers", "identifier_id", uid("entity_id", "corpus.entities.entity_id"),
                    value("kind"), value("identifier_value"), value("authority"),
                    uid("evidence_id", "corpus.evidence_spans.evidence_id"), value("verified", Boolean, default=text("false")))
models = table("ops", "model_configurations", "model_config_id", value("role"), value("config_hash"), payload("configuration"),
               value("verified", Boolean), value("test_only", Boolean), UniqueConstraint("config_hash"))
derivations = table("corpus", "derivations", "derivation_id", scoped(), payload("inputs"),
                    uid("model_config_id", "ops.model_configurations.model_config_id", nullable=True),
                    value("configuration_hash"), value("output_hash"), state(), payload("diagnostics"))
claims = table("corpus", "claims", "claim_id", scoped(), uid("subject_id", "corpus.entities.entity_id"), value("predicate"),
               uid("object_entity_id", "corpus.entities.entity_id", nullable=True), value("typed_literal", JSONB(none_as_null=True), nullable=True),
               uid("derivation_id", "corpus.derivations.derivation_id", nullable=True),
               uid("supersedes_id", "corpus.claims.claim_id", nullable=True), state("needs_review"),
               CheckConstraint("(object_entity_id IS NULL) <> (typed_literal IS NULL)"))
claim_evidence = Table("claim_evidence", metadata, uid("claim_id", "corpus.claims.claim_id", primary_key=True),
                       uid("evidence_id", "corpus.evidence_spans.evidence_id", primary_key=True),
                       value("relation"), value("review_decision"),
                       CheckConstraint("relation IN ('supports','contradicts')"), schema="corpus")
profiles = table("taxonomy", "profiles", "profile_id", value("name"), value("namespace"), value("version"),
                 value("schema_version"), value("config_hash"), payload("configuration"),
                 UniqueConstraint("namespace", "name", "version"))
taxonomies = table("taxonomy", "versions", "taxonomy_version_id", value("name"), value("version"),
                   value("artifact_hash"), state("reviewed"), UniqueConstraint("name", "version"))
concepts = table("taxonomy", "concepts", "concept_id", uid("taxonomy_version_id", "taxonomy.versions.taxonomy_version_id"),
                 value("code"), value("definition"), value("facet"), payload("notes"), UniqueConstraint("taxonomy_version_id", "code"))
labels = table("taxonomy", "labels", "label_id", uid("concept_id", "taxonomy.concepts.concept_id"),
               value("language"), value("label"), value("preferred", Boolean), payload("ambiguity"))
relations = Table("relations", metadata, uid("subject_id", "taxonomy.concepts.concept_id", primary_key=True),
                   uid("object_id", "taxonomy.concepts.concept_id", primary_key=True), value("kind"),
                   CheckConstraint("kind IN ('broader','narrower','related')"), schema="taxonomy")
chunks = table("retrieval", "chunks", "chunk_id", uid("document_version_id", "corpus.document_versions.document_version_id"),
               scoped(), value("char_start", Integer), value("char_end", Integer), value("literal_text"), value("title"),
               value("heading_path", JSONB, default=text("'[]'::jsonb")), value("language"), value("chunker_hash"),
               CheckConstraint("char_start >= 0 AND char_end > char_start"),
               UniqueConstraint("document_version_id", "char_start", "char_end", "chunker_hash"))
chunk_evidence = Table("chunk_evidence", metadata, uid("chunk_id", "retrieval.chunks.chunk_id", primary_key=True),
                       uid("evidence_id", "corpus.evidence_spans.evidence_id", primary_key=True), schema="retrieval")
assignments = table("taxonomy", "assignments", "assignment_id", scoped(), uid("concept_id", "taxonomy.concepts.concept_id"),
                    uid("document_version_id", "corpus.document_versions.document_version_id", nullable=True),
                    uid("entity_id", "corpus.entities.entity_id", nullable=True), uid("chunk_id", "retrieval.chunks.chunk_id", nullable=True),
                    uid("derivation_id", "corpus.derivations.derivation_id", nullable=True), value("mapping_kind"), state(),
                    CheckConstraint("num_nonnulls(document_version_id, entity_id, chunk_id)=1"),
                    CheckConstraint("mapping_kind IN ('direct','related')"))
assignment_evidence = Table("assignment_evidence", metadata, uid("assignment_id", "taxonomy.assignments.assignment_id", primary_key=True),
                            uid("evidence_id", "corpus.evidence_spans.evidence_id", primary_key=True), schema="taxonomy")
embedding_configs = table("retrieval", "embedding_configs", "config_id", uid("model_config_id", "ops.model_configurations.model_config_id"),
                          value("config_hash"), value("dimension", Integer), payload("encoding"), UniqueConstraint("config_hash"),
                          CheckConstraint("dimension > 0"))
embeddings = table("retrieval", "embeddings", "embedding_id", uid("chunk_id", "retrieval.chunks.chunk_id"),
                   uid("config_id", "retrieval.embedding_configs.config_id"), value("input_hash"), value("input_text"), value("vector", Vector()),
                   UniqueConstraint("chunk_id", "config_id", "input_hash"))
builds = table("retrieval", "index_builds", "build_id", uid("config_id", "retrieval.embedding_configs.config_id"),
               value("namespace"), value("chunker_hash"), value("search_config_hash"), state(), payload("validation_manifest"))
search_documents = table("retrieval", "search_documents", "projection_id", uid("chunk_id", "retrieval.chunks.chunk_id"),
                         value("search_config_hash"), value("language_config"), value("terms", TSVECTOR),
                         UniqueConstraint("chunk_id", "search_config_hash", "language_config"))
Index("ix_search_documents_terms", search_documents.c.terms, postgresql_using="gin")
snapshots = table("corpus", "snapshots", "snapshot_id", uid("profile_id", "taxonomy.profiles.profile_id"),
                  uid("taxonomy_version_id", "taxonomy.versions.taxonomy_version_id"), uid("build_id", "retrieval.index_builds.build_id"),
                  value("namespace"), value("schema_version"), value("manifest_hash"), payload("manifest"), state(),
                  value("published_at", DateTime(timezone=True), nullable=True))
snapshot_documents = Table("snapshot_documents", metadata, uid("snapshot_id", "corpus.snapshots.snapshot_id", primary_key=True),
                           uid("document_version_id", "corpus.document_versions.document_version_id", primary_key=True), schema="corpus")
snapshot_claims = Table("snapshot_claims", metadata, uid("snapshot_id", "corpus.snapshots.snapshot_id", primary_key=True),
                        uid("claim_id", "corpus.claims.claim_id", primary_key=True), schema="corpus")
snapshot_entities = Table("snapshot_entities", metadata, uid("snapshot_id", "corpus.snapshots.snapshot_id", primary_key=True),
                          uid("entity_id", "corpus.entities.entity_id", primary_key=True), schema="corpus")
snapshot_chunks = Table("snapshot_chunks", metadata, uid("snapshot_id", "corpus.snapshots.snapshot_id", primary_key=True),
                        uid("chunk_id", "retrieval.chunks.chunk_id", primary_key=True),
                        uid("embedding_id", "retrieval.embeddings.embedding_id"), schema="retrieval")
active_snapshots = Table("active_snapshots", metadata, uid("profile_id", "taxonomy.profiles.profile_id", primary_key=True),
                         uid("snapshot_id", "corpus.snapshots.snapshot_id"), schema="corpus")
inputs = table("cases", "input_revisions", "input_id", uid("case_id", "cases.cases.case_id"),
               uid("parent_id", "cases.input_revisions.input_id", nullable=True), value("message"))
runs = table("cases", "runs", "run_id", uid("case_id", "cases.cases.case_id"), uid("input_id", "cases.input_revisions.input_id"),
             uid("snapshot_id", "corpus.snapshots.snapshot_id"), uid("thread_id"), state(), payload("configuration"),
             value("trace_id", nullable=True), value("last_successful_stage", nullable=True), value("failure_reason", nullable=True),
             UniqueConstraint("thread_id"))
turns = table("cases", "dialogue_turns", "turn_id", uid("case_id", "cases.cases.case_id"), value("role"), value("message"),
              uid("input_id", "cases.input_revisions.input_id", nullable=True),
              CheckConstraint("role IN ('user','assistant','system')"))
questions = table("cases", "questions", "question_id", uid("run_id", "cases.runs.run_id"),
                  uid("input_id", "cases.input_revisions.input_id"), value("field"), value("reason"),
                  value("required", Boolean), state("open"))
answers = table("cases", "answers", "answer_id", uid("question_id", "cases.questions.question_id"),
                uid("turn_id", "cases.dialogue_turns.turn_id"), UniqueConstraint("question_id"))
manifests = table("cases", "case_evidence_manifests", "manifest_id", uid("case_id", "cases.cases.case_id"),
                  uid("parent_id", "cases.case_evidence_manifests.manifest_id", nullable=True), value("manifest_hash"))
manifest_items = table("cases", "case_evidence_items", "item_id", uid("manifest_id", "cases.case_evidence_manifests.manifest_id"),
                       uid("evidence_id", "corpus.evidence_spans.evidence_id"))
packs = table("cases", "evidence_packs", "pack_id", uid("run_id", "cases.runs.run_id"),
              uid("input_id", "cases.input_revisions.input_id"), uid("manifest_id", "cases.case_evidence_manifests.manifest_id", nullable=True),
              value("pack_hash"), payload(), state("frozen"))
pack_items = Table("pack_items", metadata, uid("pack_id", "cases.evidence_packs.pack_id", primary_key=True),
                   uid("evidence_id", "corpus.evidence_spans.evidence_id", primary_key=True), schema="cases")
pack_claims = Table("pack_claims", metadata, uid("pack_id", "cases.evidence_packs.pack_id", primary_key=True),
                    uid("claim_id", "corpus.claims.claim_id", primary_key=True), schema="cases")
results = table("cases", "result_revisions", "result_id", uid("case_id", "cases.cases.case_id"),
                uid("pack_id", "cases.evidence_packs.pack_id"), uid("parent_id", "cases.result_revisions.result_id", nullable=True),
                value("instruction"), value("result_hash"), payload(), state("draft"))
reviews = table("cases", "reviews", "review_id", uid("result_id", "cases.result_revisions.result_id"),
                uid("reviewer_id", "ops.principals.principal_id"), value("result_hash"), value("decision"))
exports = table("cases", "exports", "export_id", uid("result_id", "cases.result_revisions.result_id"),
                uid("review_id", "cases.reviews.review_id"), uid("artifact_id", "corpus.artifacts.artifact_id"),
                value("template_version"), value("renderer_version"), value("selection_hash"), state("ready"))
attempts = table("ops", "stage_attempts", "attempt_id", uid("run_id", "cases.runs.run_id", nullable=True),
                 uid("job_id", "ops.ingest_jobs.job_id", nullable=True), value("namespace"), value("stage"),
                 value("input_hash"), value("config_hash"), value("idempotency_key"), state("pending"),
                 value("worker_id", nullable=True), value("lease_until", DateTime(timezone=True), nullable=True),
                 value("attempt_count", Integer, default=text("0")), payload("outputs"),
                 CheckConstraint("num_nonnulls(run_id,job_id)=1"), UniqueConstraint("idempotency_key"))
checks = table("ops", "publication_checks", "check_id", uid("snapshot_id", "corpus.snapshots.snapshot_id"),
               value("validator"), value("version"), value("passed", Boolean), value("manifest_hash"),
               UniqueConstraint("snapshot_id", "validator"))
outbox = table("ops", "outbox", "event_id", value("namespace"), uid("run_id", "cases.runs.run_id", nullable=True),
               value("idempotency_key"), value("event_type"), payload(), state("pending"),
               value("worker_id", nullable=True), value("lease_until", DateTime(timezone=True), nullable=True),
               value("attempts", Integer, default=text("0")), value("next_retry", DateTime(timezone=True), default=text("now()")),
               UniqueConstraint("idempotency_key"))

# Case processing and reason-level editorial review.
interpretations = table("cases", "interpretations", "interpretation_id",
    uid("run_id", "cases.runs.run_id"), payload(), UniqueConstraint("run_id"))
web_research = table("cases", "web_research", "research_id", uid("run_id", "cases.runs.run_id"),
    value("query"), value("mode"), state("pending"), payload("diagnostics"),
    CheckConstraint("mode IN ('connected','offline')"),
    CheckConstraint("status IN ('pending','completed','unavailable','failed')"))
web_sources = table("cases", "web_sources", "discovery_id", uid("research_id", "cases.web_research.research_id"),
    value("canonical_url"), uid("document_version_id", "corpus.document_versions.document_version_id", nullable=True),
    uid("duplicate_version_id", "corpus.document_versions.document_version_id", nullable=True), payload(),
    CheckConstraint("num_nonnulls(document_version_id,duplicate_version_id)=1"),
    UniqueConstraint("research_id", "canonical_url"))
assessments = table("cases", "claim_assessments", "assessment_id", uid("run_id", "cases.runs.run_id"),
    uid("claim_id", "corpus.claims.claim_id"), value("status"), payload(),
    UniqueConstraint("run_id", "claim_id"), CheckConstraint("status IN ('supported','unsupported','contradicted')"))
reasons = table("cases", "draft_reasons", "reason_row_id", uid("result_id", "cases.result_revisions.result_id"),
    value("reason_key"), value("support_hash"), payload(), UniqueConstraint("result_id", "reason_key"))
reason_claims = Table("reason_claims", metadata,
    uid("reason_row_id", "cases.draft_reasons.reason_row_id", primary_key=True),
    uid("claim_id", "corpus.claims.claim_id", primary_key=True), schema="cases")
reason_selections = Table("reason_selections", metadata,
    uid("reason_row_id", "cases.draft_reasons.reason_row_id", primary_key=True),
    value("selection"), uid("reviewer_id", "ops.principals.principal_id"),
    value("updated_at", DateTime(timezone=True), default=text("now()")),
    CheckConstraint("selection IN ('none','kept','rejected')"), schema="cases")
action_items = table("cases", "action_items", "action_id", uid("case_id", "cases.cases.case_id"),
    value("question"), value("ask_role"), state("open"), CheckConstraint("status IN ('open','asked','done')"))
reviews.append_column(value("selection_hash", nullable=True))
exports.append_column(value("format", default=text("'pdf'")))

# Constraints installed by historical migrations, mirrored here for schema consumers.
claims.append_constraint(CheckConstraint("typed_literal IS NULL OR (jsonb_typeof(typed_literal)='object' AND typed_literal ? 'type' AND typed_literal ? 'value')", name="typed_literal_shape"))
for target, expression, name in (
    (assignments, "status IN ('draft','accepted','needs_review','rejected')", "assignment_state"),
    (claims, "status IN ('draft','accepted','needs_review','rejected')", "claim_state"),
    (snapshots, "status IN ('draft','published','failed')", "snapshot_state"),
    (attempts, "status IN ('pending','running','committed','failed')", "attempt_state"),
    (outbox, "status IN ('pending','running','delivered','failed')", "outbox_state"),
):
    target.append_constraint(CheckConstraint(expression, name=name))
Index("verified_entity_identifier", identifiers.c.authority, identifiers.c.kind,
      identifiers.c.identifier_value, unique=True, postgresql_where=identifiers.c.verified)

# Scope-specific finalization constraints are applied by migration 0005.
for target, expression, name in (
    (entities, "entity_type IN ('person','unit','organization','project','facility','service')", "entity_type_allowed"),
    (entities, "length(btrim(display_label)) > 0", "entity_label_required"),
    (claims, "length(btrim(predicate)) > 0", "claim_predicate_required"),
    (builds, "status IN ('draft','published','failed')", "build_state"),
    (reviews, "decision IN ('accepted','rejected')", "review_decision_allowed"),
    (versions, "status IN ('accepted','needs_review','rejected')", "document_version_state"),
):
    target.append_constraint(CheckConstraint(expression, name=name))
aliases.append_constraint(UniqueConstraint("document_id", "url", name="document_alias_unique"))
manifest_items.append_constraint(UniqueConstraint("manifest_id", "evidence_id", name="manifest_evidence_unique"))
Index("ix_claim_evidence_evidence", claim_evidence.c.evidence_id)
Index("ix_chunk_evidence_evidence", chunk_evidence.c.evidence_id)
Index("ix_pack_items_evidence", pack_items.c.evidence_id)
Index("ix_document_alias_url", aliases.c.url)

for current_table in list(metadata.tables.values()):
    for current_column in current_table.columns:
        if current_column.foreign_keys and not current_column.primary_key:
            Index(f"ix_{current_table.schema}_{current_table.name}_{current_column.name}", current_column)
