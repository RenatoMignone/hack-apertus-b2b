"""Add case-local research, assessments and reason-level editorial review."""
from alembic import op
from sqlalchemy import text

from backend.data.schema import metadata, PIPELINE_TABLES
from backend.data.pipeline_security import install_pipeline_security

revision = "0004_case_pipeline"
down_revision = "0003_embedding_inputs"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    metadata.create_all(connection, tables=[table for table in metadata.sorted_tables
                                          if table.fullname in PIPELINE_TABLES])
    connection.execute(text("ALTER TABLE cases.reviews ADD COLUMN IF NOT EXISTS selection_hash text"))
    connection.execute(text("ALTER TABLE cases.exports ADD COLUMN IF NOT EXISTS format text NOT NULL DEFAULT 'legacy'"))
    install_pipeline_security(connection)


def downgrade():
    raise RuntimeError("restore a validated backup instead of destructive downgrade")
