"""Evaluate visible snapshot membership once per statement, preserving RLS."""
from alembic import op
from sqlalchemy import text

revision = '0012_membership_lookup'
down_revision = '0011_capture_performance'
branch_labels = depends_on = None


def upgrade():
    c = op.get_bind()
    c.execute(text("SET LOCAL lock_timeout='3s'"))
    for target in ('corpus.snapshot_documents', 'corpus.snapshot_entities',
                   'corpus.snapshot_claims', 'retrieval.snapshot_chunks'):
        # Uncorrelated IN permits a hashed subplan. The subquery still runs with
        # caller RLS, including namespace and live-capture ownership. No grants
        # or visibility rules change; avoid re-reading a large JSON manifest per chunk.
        c.execute(text(f'''ALTER POLICY snapshot_membership_access ON {target}
            USING (snapshot_id IN (SELECT s.snapshot_id FROM corpus.snapshots s))
            WITH CHECK (snapshot_id IN (SELECT s.snapshot_id FROM corpus.snapshots s))'''))


def downgrade():
    raise RuntimeError('Deploy a reviewed forward fix')
