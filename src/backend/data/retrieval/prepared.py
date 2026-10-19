"""Transaction-local, caller-authorized retrieval relations with measured statistics."""
from sqlalchemy import text

from backend.data.retrieval.batched import statement

AUTHORIZED = """
    FROM pg_temp.navigator_retrieval_members sc
    JOIN retrieval.chunks c ON c.chunk_id=sc.chunk_id
    JOIN corpus.document_versions v ON v.document_version_id=c.document_version_id
    JOIN corpus.documents d ON d.document_id=v.document_id
    JOIN retrieval.embeddings e ON e.embedding_id=sc.embedding_id
      AND e.chunk_id=c.chunk_id AND e.config_id=:eligible_config
    WHERE c.scope_id IN (SELECT scope_id FROM corpus.scopes WHERE ops.can_access(scope_id))
      AND v.status='accepted'
      AND (:all_languages OR c.language IN :languages)
      AND (:all_documents OR d.document_id NOT IN :excluded)
      AND (:all_families OR EXISTS (
        SELECT 1 FROM corpus.source_family_memberships f
        WHERE f.source_id=d.source_id AND f.family_id IN :families))
"""


def prepare(connection, eligible, parameters, *, vectors):
    # Resolve the same snapshot/build/live-owning-run guard ONCE, before joining
    # the many chunks. All these reads still execute under caller RLS.
    config = connection.execute(text("""
        SELECT b.config_id FROM corpus.snapshots s
        JOIN retrieval.index_builds b ON b.build_id=s.build_id
        WHERE s.snapshot_id=:snapshot AND s.namespace=:namespace
          AND (s.status='published' OR (s.status='live' AND EXISTS (
            SELECT 1 FROM cases.runs r WHERE r.run_id=:run
              AND r.snapshot_id=s.snapshot_id AND r.case_id=:case)))
        """), parameters).scalar_one()
    parameters = {**parameters, "eligible_config": config}
    # Bounded per-transaction hash workspace; restored automatically on commit.
    connection.execute(text("SET LOCAL work_mem='32MB'"))
    # Never reuse/drop a caller-created relation with this reserved name.
    connection.execute(text("""CREATE TEMP TABLE navigator_retrieval_members ON COMMIT DROP AS
        SELECT snapshot_id,chunk_id,embedding_id FROM retrieval.snapshot_chunks
        WHERE snapshot_id=:snapshot"""), parameters)
    connection.execute(text("CREATE UNIQUE INDEX ON pg_temp.navigator_retrieval_members(chunk_id)"))
    connection.execute(text("ANALYZE pg_temp.navigator_retrieval_members"))
    # Keep only immutable embedding identities here. Copying 144k 768d vectors
    # into a TEMP heap detoasts/rewrites hundreds of MB before either branch.
    # The dense statement below reads those authorized immutable vectors once.
    columns = "c.chunk_id,c.scope_id,e.embedding_id"
    # The embedding-id/chunk-id consistency predicates are correlated. PostgreSQL
    # still multiplies their selectivities and can collapse this join to one row
    # even after membership ANALYZE. Prefer hash/merge joins for this one large
    # staging statement; retain every consistency predicate and restore the GUC.
    size = connection.execute(text("SELECT reltuples FROM pg_class WHERE oid="
        "'pg_temp.navigator_retrieval_members'::regclass")).scalar_one()
    previous = connection.execute(text("SHOW enable_nestloop")).scalar_one()
    if size >= 1024:
        connection.execute(text("SET LOCAL enable_nestloop=off"))
    connection.execute(statement("CREATE TEMP TABLE navigator_retrieval_eligible ON COMMIT DROP AS SELECT " +
                                 columns + AUTHORIZED), parameters)
    if size >= 1024:
        connection.execute(text("SELECT set_config('enable_nestloop',:previous,true)"), {"previous": previous})
    connection.execute(text("CREATE UNIQUE INDEX ON pg_temp.navigator_retrieval_eligible(chunk_id)"))
    connection.execute(text("ANALYZE pg_temp.navigator_retrieval_eligible"))
