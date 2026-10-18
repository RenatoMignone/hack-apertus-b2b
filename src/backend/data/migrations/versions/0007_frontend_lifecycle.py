"""Persist the polished UI's independent hold/outcome flags and action notes."""
from alembic import op
from sqlalchemy import text

revision = "0007_frontend_lifecycle"
down_revision = "0006_runtime_access"
branch_labels = None
depends_on = None


def upgrade():
    op.get_bind().execute(text("""
        ALTER TABLE cases.cases ADD COLUMN on_hold boolean NOT NULL DEFAULT false;
        ALTER TABLE cases.cases ADD COLUMN outcome text;
        ALTER TABLE cases.cases ADD CONSTRAINT case_outcome_allowed CHECK(outcome IN ('visit','no_interest'));
        UPDATE cases.cases SET on_hold=true,status='researching' WHERE status='on_hold';
        UPDATE cases.cases SET outcome=substring(status FROM 8),status='closed'
          WHERE status IN ('closed_visit','closed_no_interest');
        ALTER TABLE cases.action_items ADD COLUMN answer text;
    """))


def downgrade():
    raise RuntimeError("restore a validated backup instead of discarding case metadata")
