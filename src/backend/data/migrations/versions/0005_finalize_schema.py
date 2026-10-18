"""Retire duplicate workflows and finalize the ingestion/retrieval schema.

Populated historical tables and nonredundant retired chunk fields are archived,
never silently discarded. The archive is not an application query surface.
"""
from alembic import op
from sqlalchemy import text


revision = "0005_finalize_schema"
down_revision = "0004_case_pipeline"
branch_labels = None
depends_on = None

# Child tables first; this list is frozen migration history, not runtime metadata.
RETIRED = (
    "cases.selections", "cases.match_support", "cases.matches",
    "cases.retrieval_hits", "cases.retrieval_rounds", "cases.query_plans",
    "ops.frontier",
)


def upgrade():
    connection = op.get_bind()
    has_history = any(connection.execute(text(f"SELECT EXISTS(SELECT 1 FROM {name})")).scalar_one()
                      for name in RETIRED)
    has_context = connection.execute(text("""
        SELECT EXISTS(SELECT 1 FROM retrieval.chunks
          WHERE context_prefix <> '' OR embedding_text IS DISTINCT FROM literal_text)
    """)).scalar_one()
    if has_history or has_context:
        connection.execute(text("CREATE SCHEMA legacy"))
        connection.execute(text("REVOKE ALL ON SCHEMA legacy FROM PUBLIC"))
    if has_history:
        for name in RETIRED:
            connection.execute(text(f"ALTER TABLE {name} SET SCHEMA legacy"))
    else:
        for name in RETIRED:
            connection.execute(text(f"DROP TABLE {name}"))
    if has_context:
        connection.execute(text("""
            CREATE TABLE legacy.chunk_encoding AS
              SELECT chunk_id,context_prefix,embedding_text FROM retrieval.chunks
              WHERE context_prefix <> '' OR embedding_text IS DISTINCT FROM literal_text
        """))
    # Revoke inherited/direct legacy table privileges; the owner retains audit access.
    if has_history or has_context:
        roles = connection.execute(text("""
            SELECT DISTINCT r.rolname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
            CROSS JOIN LATERAL aclexplode(coalesce(c.relacl,acldefault('r',c.relowner))) a
            JOIN pg_roles r ON r.oid=a.grantee
            WHERE n.nspname='legacy' AND a.grantee <> c.relowner
        """)).scalars().all()
        quote = connection.dialect.identifier_preparer.quote
        for role in ["PUBLIC", *roles]:
            target = "PUBLIC" if role == "PUBLIC" else quote(role)
            connection.execute(text(f"REVOKE ALL ON ALL TABLES IN SCHEMA legacy FROM {target}"))
    connection.execute(text("""
        ALTER TABLE cases.exports ALTER COLUMN format SET DEFAULT 'pdf';
        ALTER TABLE retrieval.chunks DROP COLUMN context_prefix, DROP COLUMN embedding_text;
        ALTER TABLE corpus.entities ADD CONSTRAINT entity_type_allowed
          CHECK(entity_type IN ('person','unit','organization','project','facility','service'));
        ALTER TABLE corpus.entities ADD CONSTRAINT entity_label_required CHECK(length(btrim(display_label)) > 0);
        ALTER TABLE corpus.claims ADD CONSTRAINT claim_predicate_required CHECK(length(btrim(predicate)) > 0);
        ALTER TABLE retrieval.index_builds ADD CONSTRAINT build_state CHECK(status IN ('draft','published','failed'));
        ALTER TABLE cases.reviews ADD CONSTRAINT review_decision_allowed CHECK(decision IN ('accepted','rejected'));
        ALTER TABLE corpus.document_versions ADD CONSTRAINT document_version_state
          CHECK(status IN ('accepted','needs_review','rejected'));
        ALTER TABLE corpus.document_aliases ADD CONSTRAINT document_alias_unique UNIQUE(document_id,url);
        ALTER TABLE cases.case_evidence_items ADD CONSTRAINT manifest_evidence_unique UNIQUE(manifest_id,evidence_id);
        CREATE INDEX ix_claim_evidence_evidence ON corpus.claim_evidence(evidence_id);
        CREATE INDEX ix_chunk_evidence_evidence ON retrieval.chunk_evidence(evidence_id);
        CREATE INDEX ix_pack_items_evidence ON cases.pack_items(evidence_id);
        CREATE INDEX ix_document_alias_url ON corpus.document_aliases(url);
        CREATE INDEX ix_cases_cases_current_input_id ON cases.cases(current_input_id);
        CREATE INDEX ix_cases_cases_current_result_id ON cases.cases(current_result_id);
        CREATE INDEX ix_ops_ingest_jobs_profile_id ON ops.ingest_jobs(profile_id);
        CREATE INDEX ix_ops_ingest_jobs_base_snapshot_id ON ops.ingest_jobs(base_snapshot_id);
    """))


def downgrade():
    raise RuntimeError("restore a validated backup instead of recreating retired workflows")
