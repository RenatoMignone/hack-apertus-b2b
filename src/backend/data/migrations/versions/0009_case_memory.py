"""Optional own-case memory. Core 0008 runtime remains compatible while disabled."""
from alembic import op
from sqlalchemy import text
from backend.data.schema import case_memory

revision = '0009_case_memory'
down_revision = '0008_live_corpus'
branch_labels = depends_on = None


def upgrade():
    c = op.get_bind()
    c.execute(text("SET LOCAL lock_timeout='3s'"))
    case_memory.create(c)
    c.execute(text('''
        ALTER TABLE cases.memory_profiles ENABLE ROW LEVEL SECURITY;
        CREATE POLICY own_memory ON cases.memory_profiles USING (
          ops.owns_case(case_id) AND owner_id::text=current_setting('navigator.principal',true)
          AND namespace=current_setting('navigator.namespace',true)) WITH CHECK (
          ops.owns_case(case_id) AND owner_id::text=current_setting('navigator.principal',true)
          AND namespace=current_setting('navigator.namespace',true));
        CREATE FUNCTION ops.verify_case_memory() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF NOT EXISTS(SELECT 1 FROM cases.cases c JOIN cases.input_revisions i ON i.case_id=c.case_id
            JOIN cases.result_revisions r ON r.case_id=c.case_id JOIN cases.evidence_packs p ON p.pack_id=r.pack_id
            WHERE c.case_id=NEW.case_id AND c.owner_id=NEW.owner_id AND c.namespace=NEW.namespace
              AND i.input_id=NEW.input_id AND p.input_id=NEW.input_id AND r.result_id=NEW.result_id) THEN
            RAISE EXCEPTION 'memory lineage mismatch';
          END IF;
          IF TG_OP='UPDATE' AND (to_jsonb(NEW)-'enabled') IS DISTINCT FROM (to_jsonb(OLD)-'enabled') THEN
            RAISE EXCEPTION 'memory profile is immutable; create a revision';
          END IF;
          RETURN NEW;
        END $$;
        CREATE TRIGGER memory_lineage BEFORE INSERT OR UPDATE ON cases.memory_profiles
          FOR EACH ROW EXECUTE FUNCTION ops.verify_case_memory();
        DO $$ BEGIN
          IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='navigator_runtime') THEN
            GRANT SELECT,INSERT,UPDATE ON cases.memory_profiles TO navigator_runtime;
          END IF;
          IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='navigator_app') THEN
            GRANT SELECT,INSERT,UPDATE ON cases.memory_profiles TO navigator_app;
          END IF;
        END $$;
    '''))


def downgrade():
    raise RuntimeError('restore a reviewed backup; do not discard case history')
