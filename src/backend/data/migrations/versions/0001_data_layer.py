from alembic import op
from sqlalchemy import text

from backend.data.schema import metadata
from backend.data.security import install_security


revision = "0001_data_layer"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    for schema in ("corpus", "taxonomy", "retrieval", "cases", "ops"):
        connection.execute(text(f"CREATE SCHEMA {schema}"))
    metadata.create_all(connection)
    install_security(connection)


def downgrade():
    raise RuntimeError("destructive downgrade is disabled; restore a validated backup")
