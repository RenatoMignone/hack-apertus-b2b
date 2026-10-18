"""Case-owned live corpus captures and a restricted runtime database role.

No source rows, vectors or active publication pointers are changed.
"""
from pathlib import Path

from alembic import op
from sqlalchemy import text

revision = "0008_live_corpus"
down_revision = "0007_frontend_lifecycle"
branch_labels = None
depends_on = None


def upgrade():
    c = op.get_bind()
    # Fail atomically instead of waiting behind ingestion or an open user transaction.
    c.execute(text("SET LOCAL lock_timeout='3s'"))
    c.execute(text("""
        ALTER TABLE corpus.snapshots DROP CONSTRAINT snapshot_state;
        ALTER TABLE corpus.snapshots ADD CONSTRAINT snapshot_state
          CHECK(status IN ('draft','published','failed','live'));
        ALTER TABLE retrieval.index_builds DROP CONSTRAINT build_state;
        ALTER TABLE retrieval.index_builds ADD CONSTRAINT build_state
          CHECK(status IN ('draft','published','failed','live'));
        CREATE OR REPLACE FUNCTION ops.freeze_membership() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE target uuid;
        BEGIN
          IF TG_OP='DELETE' THEN target=OLD.snapshot_id; ELSE target=NEW.snapshot_id; END IF;
          IF EXISTS(SELECT 1 FROM corpus.snapshots WHERE snapshot_id=target AND status IN ('published','live')) THEN
            RAISE EXCEPTION 'captured membership is immutable';
          END IF;
          IF TG_OP='DELETE' THEN RETURN OLD; ELSE RETURN NEW; END IF;
        END $$;
        DROP TRIGGER freeze_published ON corpus.snapshots;
        CREATE TRIGGER freeze_published BEFORE UPDATE OR DELETE ON corpus.snapshots
          FOR EACH ROW WHEN (OLD.status IN ('published','live')) EXECUTE FUNCTION ops.prevent_change();
        DROP TRIGGER freeze_published ON retrieval.index_builds;
        CREATE TRIGGER freeze_published BEFORE UPDATE OR DELETE ON retrieval.index_builds
          FOR EACH ROW WHEN (OLD.status IN ('published','live')) EXECUTE FUNCTION ops.prevent_change();
        CREATE POLICY live_owner ON corpus.snapshots AS RESTRICTIVE FOR SELECT
          USING (status <> 'live' OR ops.owns_case((manifest->>'runtime_case_id')::uuid));
        CREATE POLICY live_owner ON retrieval.index_builds AS RESTRICTIVE FOR SELECT
          USING (status <> 'live' OR ops.owns_case((validation_manifest->>'runtime_case_id')::uuid));
        CREATE FUNCTION ops.verify_run_snapshot() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF NOT EXISTS(SELECT 1 FROM corpus.snapshots s JOIN cases.cases c ON c.case_id=NEW.case_id
              WHERE s.snapshot_id=NEW.snapshot_id AND s.namespace=c.namespace
                AND (s.status='published' OR (s.status='live' AND s.manifest->>'runtime_case_id'=c.case_id::text))) THEN
            RAISE EXCEPTION 'run requires a published corpus or its own live capture' USING ERRCODE='42501';
          END IF;
          RETURN NEW;
        END $$;
        CREATE TRIGGER verify_run_snapshot BEFORE INSERT ON cases.runs
          FOR EACH ROW EXECUTE FUNCTION ops.verify_run_snapshot();
        DO $$ BEGIN
          IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='navigator_runtime') THEN
            CREATE ROLE navigator_runtime NOLOGIN;
          END IF;
          EXECUTE format('GRANT CONNECT ON DATABASE %I TO navigator_runtime',current_database());
        END $$;
        GRANT USAGE ON SCHEMA corpus,taxonomy,retrieval,cases,ops TO navigator_runtime;
        GRANT SELECT ON ALL TABLES IN SCHEMA corpus,taxonomy,retrieval,cases,ops TO navigator_runtime;
        GRANT INSERT,UPDATE ON ALL TABLES IN SCHEMA cases TO navigator_runtime;
        GRANT INSERT,UPDATE ON ops.stage_attempts,ops.outbox TO navigator_runtime;
        GRANT INSERT ON corpus.artifacts,corpus.sources,corpus.documents,corpus.fetches,
          corpus.document_versions,corpus.evidence_spans,corpus.entities,corpus.claims,
          corpus.claim_evidence,corpus.derivations,corpus.entity_identifiers TO navigator_runtime;
        GRANT EXECUTE ON FUNCTION ops.ensure_case_scope(uuid) TO navigator_runtime;
    """))
    for table in ("corpus.snapshot_documents", "corpus.snapshot_entities", "corpus.snapshot_claims", "retrieval.snapshot_chunks"):
        name = table.split(".")[1]
        c.execute(text(f"""ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;
            CREATE POLICY snapshot_membership_access ON {table} USING (
              EXISTS(SELECT 1 FROM corpus.snapshots s WHERE s.snapshot_id={name}.snapshot_id))
            WITH CHECK (EXISTS(SELECT 1 FROM corpus.snapshots s WHERE s.snapshot_id={name}.snapshot_id));"""))
    # Runtime writers can create evidence only inside owned case scopes, even if
    # somebody accidentally gives them a writable public-scope grant later.
    for table in ("sources", "documents", "document_versions", "evidence_spans", "entities", "claims", "derivations"):
        c.execute(text(f"""CREATE POLICY runtime_case_only ON corpus.{table}
            AS RESTRICTIVE FOR INSERT TO navigator_runtime WITH CHECK (
              EXISTS(SELECT 1 FROM corpus.scopes s WHERE s.scope_id={table}.scope_id
                AND s.kind='case' AND ops.owns_case(s.case_id) AND ops.can_access(s.scope_id,true)))"""))
    for table, parent, key in (("fetches", "documents", "document_id"),
                               ("entity_identifiers", "entities", "entity_id"),
                               ("claim_evidence", "claims", "claim_id")):
        c.execute(text(f"""CREATE POLICY runtime_case_only ON corpus.{table}
            AS RESTRICTIVE FOR INSERT TO navigator_runtime WITH CHECK (
              EXISTS(SELECT 1 FROM corpus.{parent} p JOIN corpus.scopes s USING(scope_id)
                WHERE p.{key}={table}.{key} AND s.kind='case' AND ops.owns_case(s.case_id)
                  AND ops.can_access(s.scope_id,true)))"""))
    c.execute(text((Path(__file__).with_name("live_capture.sql")).read_text(encoding="utf-8")))
    c.execute(text("""
        REVOKE ALL ON FUNCTION ops.capture_live_corpus(uuid,uuid,uuid,text) FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION ops.capture_live_corpus(uuid,uuid,uuid,text) TO navigator_runtime;
        DO $$ BEGIN
          IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='navigator_app') THEN
            GRANT EXECUTE ON FUNCTION ops.capture_live_corpus(uuid,uuid,uuid,text) TO navigator_app;
          END IF;
        END $$;
    """))


def downgrade():
    raise RuntimeError("restore a validated backup instead of removing live capture authorization")
