"""Optional manually entered case plans; additive to the 0008 core baseline."""
from alembic import op
from sqlalchemy import text
from backend.data.schema import business_contexts

revision = '0010_rich_outputs'
down_revision = '0009_case_memory'
branch_labels = depends_on = None


def upgrade():
    c = op.get_bind()
    c.execute(text("SET LOCAL lock_timeout='3s'"))
    business_contexts.create(c)
    c.execute(text('''
      ALTER TABLE cases.business_contexts ENABLE ROW LEVEL SECURITY;
      CREATE POLICY own_business_context ON cases.business_contexts
        USING (ops.owns_case(case_id)) WITH CHECK (ops.owns_case(case_id)
          AND entered_by::text=current_setting('navigator.principal',true));
      CREATE FUNCTION ops.verify_business_context() RETURNS trigger LANGUAGE plpgsql AS $$
      BEGIN
        IF TG_OP <> 'INSERT' THEN RAISE EXCEPTION 'business context is immutable'; END IF;
        IF NOT EXISTS(SELECT 1 FROM cases.input_revisions i WHERE i.input_id=NEW.input_id
          AND i.case_id=NEW.case_id) THEN RAISE EXCEPTION 'business context input mismatch'; END IF;
        RETURN NEW;
      END $$;
      CREATE TRIGGER business_context_lineage BEFORE INSERT OR UPDATE OR DELETE ON cases.business_contexts
        FOR EACH ROW EXECUTE FUNCTION ops.verify_business_context();
      DO $$ BEGIN
        IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='navigator_runtime') THEN
          GRANT SELECT,INSERT ON cases.business_contexts TO navigator_runtime;
        END IF;
        IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='navigator_app') THEN
          GRANT SELECT,INSERT ON cases.business_contexts TO navigator_app;
        END IF;
      END $$;
    '''))


def downgrade():
    raise RuntimeError('restore a reviewed backup; do not discard attributed input revisions')
