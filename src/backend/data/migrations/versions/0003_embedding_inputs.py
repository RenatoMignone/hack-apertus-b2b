from alembic import op
from sqlalchemy import text


revision = "0003_embedding_inputs"
down_revision = "0002_integrity"
branch_labels = None
depends_on = None


def upgrade():
    op.get_bind().execute(text("""
        ALTER TABLE corpus.fetches ALTER COLUMN http_status DROP NOT NULL;
        ALTER TABLE retrieval.embeddings ADD COLUMN IF NOT EXISTS input_text text;
        ALTER TABLE retrieval.embeddings DISABLE TRIGGER immutable;
        UPDATE retrieval.embeddings e SET input_text=c.embedding_text FROM retrieval.chunks c
          WHERE c.chunk_id=e.chunk_id AND e.input_text IS NULL;
        ALTER TABLE retrieval.embeddings ENABLE TRIGGER immutable;
        ALTER TABLE retrieval.embeddings ALTER COLUMN input_text SET NOT NULL;
        CREATE OR REPLACE FUNCTION ops.verify_embedding_input() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF NEW.input_hash <> encode(sha256(convert_to(NEW.input_text,'UTF8')),'hex') OR NOT EXISTS(
            SELECT 1 FROM retrieval.chunks WHERE chunk_id=NEW.chunk_id AND position(literal_text IN NEW.input_text)>0) THEN
            RAISE EXCEPTION 'embedding input hash mismatch or original text missing';
          END IF;
          RETURN NEW;
        END $$;
    """))


def downgrade():
    raise RuntimeError("restore a validated backup instead of destructive downgrade")
