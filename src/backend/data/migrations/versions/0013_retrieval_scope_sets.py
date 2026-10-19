"""Evaluate identical readable-scope authorization once per statement."""
from alembic import op
from sqlalchemy import text

revision = "0013_retrieval_scope_sets"
down_revision = "0012_membership_lookup"
branch_labels = depends_on = None


def upgrade():
    c = op.get_bind()
    c.execute(text("SET LOCAL lock_timeout='3s'"))
    c.execute(text("""
        CREATE FUNCTION ops.readable_scope_ids() RETURNS SETOF uuid
        LANGUAGE sql STABLE SECURITY DEFINER ROWS 100 SET search_path=pg_catalog AS $$
          SELECT g.scope_id FROM ops.scope_grants g
            JOIN ops.principals p USING(principal_id) JOIN corpus.scopes s USING(scope_id)
          WHERE NOT s.revoked AND p.active AND p.database_role=session_user
            AND p.principal_id::text=current_setting('navigator.principal',true)
            AND p.namespace=current_setting('navigator.namespace',true)
        $$;
        REVOKE ALL ON FUNCTION ops.readable_scope_ids() FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION ops.readable_scope_ids() TO navigator_runtime,navigator_app;
    """))
    # SELECT only. Writing policies, case ownership, namespace and live-owner
    # restrictions remain in place. This is exactly can_access(scope_id,false).
    for target in ("corpus.scopes", "corpus.sources", "corpus.documents",
                   "corpus.document_versions", "corpus.evidence_spans", "corpus.entities",
                   "corpus.claims", "corpus.derivations", "taxonomy.assignments", "retrieval.chunks"):
        c.execute(text(f"""ALTER POLICY read_access ON {target}
            USING (scope_id IN (SELECT ops.readable_scope_ids()))"""))
    for target in ("retrieval.embeddings", "retrieval.search_documents"):
        c.execute(text(f"""ALTER POLICY read_access ON {target}
            USING (chunk_id IN (SELECT c.chunk_id FROM retrieval.chunks c))"""))


def downgrade():
    raise RuntimeError("Deploy a reviewed forward fix")
