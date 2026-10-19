"""Optimize live capture without changing membership, source records or access."""
from pathlib import Path
from alembic import op
from sqlalchemy import text

revision = '0011_capture_performance'
down_revision = '0010_rich_outputs'
branch_labels = depends_on = None


def upgrade():
    c = op.get_bind()
    c.execute(text("SET LOCAL lock_timeout='3s'"))
    c.execute(text(Path(__file__).with_name('live_capture_fast.sql').read_text()))


def downgrade():
    raise RuntimeError('Restore an approved backup or deploy a reviewed forward fix')
