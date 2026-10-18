"""Restricted case-scope provisioning and private runtime stage/command policies."""
from alembic import op
from sqlalchemy import text

revision = "0006_runtime_access"
down_revision = "0005_finalize_schema"
branch_labels = None
depends_on = None


def upgrade():
    op.get_bind().execute(text("""
        CREATE FUNCTION ops.ensure_case_scope(target uuid) RETURNS uuid
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
        DECLARE owner uuid; space text; scope uuid; count_scopes integer;
        BEGIN
          SELECT c.owner_id,p.namespace INTO owner,space
            FROM cases.cases c JOIN ops.principals p ON p.principal_id=c.owner_id
            WHERE c.case_id=target AND p.active AND p.database_role=session_user
              AND p.principal_id::text=current_setting('navigator.principal',true)
              AND p.namespace=current_setting('navigator.namespace',true)
              AND c.namespace=p.namespace FOR UPDATE OF c;
          IF owner IS NULL THEN RAISE EXCEPTION 'case is unavailable' USING ERRCODE='42501'; END IF;
          SELECT count(*) INTO count_scopes FROM corpus.scopes WHERE kind='case' AND case_id=target;
          IF count_scopes > 1 OR EXISTS(SELECT 1 FROM corpus.scopes
              WHERE kind='case' AND case_id=target AND revoked) THEN
            RAISE EXCEPTION 'case scope is unavailable' USING ERRCODE='42501';
          END IF;
          SELECT scope_id INTO scope FROM corpus.scopes WHERE kind='case' AND case_id=target;
          IF scope IS NULL THEN
            scope := gen_random_uuid();
            INSERT INTO corpus.scopes(scope_id,kind,case_id,access_policy_id)
              VALUES(scope,'case',target,'case-owner-v1');
          END IF;
          INSERT INTO ops.scope_grants(principal_id,scope_id,can_write) VALUES(owner,scope,true)
            ON CONFLICT(principal_id,scope_id) DO NOTHING;
          IF NOT EXISTS(SELECT 1 FROM ops.scope_grants
              WHERE principal_id=owner AND scope_id=scope AND can_write) THEN
            RAISE EXCEPTION 'case scope is read-only' USING ERRCODE='42501';
          END IF;
          RETURN scope;
        END $$;
        REVOKE ALL ON FUNCTION ops.ensure_case_scope(uuid) FROM PUBLIC;
        DO $$ BEGIN
          IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='navigator_app') THEN
            GRANT EXECUTE ON FUNCTION ops.ensure_case_scope(uuid) TO navigator_app;
          END IF;
        END $$;
        CREATE POLICY runtime_private ON ops.stage_attempts AS RESTRICTIVE
          USING (run_id IS NULL OR EXISTS(SELECT 1 FROM cases.runs r WHERE r.run_id=stage_attempts.run_id))
          WITH CHECK (run_id IS NULL OR EXISTS(SELECT 1 FROM cases.runs r WHERE r.run_id=stage_attempts.run_id));
        CREATE POLICY runtime_private ON ops.outbox AS RESTRICTIVE
          USING ((run_id IS NULL OR EXISTS(SELECT 1 FROM cases.runs r WHERE r.run_id=outbox.run_id))
            AND (event_type <> 'runtime.command' OR payload->>'principal_id'=current_setting('navigator.principal',true)))
          WITH CHECK ((run_id IS NULL OR EXISTS(SELECT 1 FROM cases.runs r WHERE r.run_id=outbox.run_id))
            AND (event_type <> 'runtime.command' OR payload->>'principal_id'=current_setting('navigator.principal',true)));
    """))


def downgrade():
    raise RuntimeError("restore a validated backup instead of removing access controls")
