from alembic import op
from sqlalchemy import text


revision = "0002_integrity"
down_revision = "0001_data_layer"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    connection.execute(text("""
        ALTER TABLE cases.cases ADD CONSTRAINT current_input_fk FOREIGN KEY(current_input_id)
          REFERENCES cases.input_revisions(input_id) DEFERRABLE INITIALLY DEFERRED;
        ALTER TABLE cases.cases ADD CONSTRAINT current_result_fk FOREIGN KEY(current_result_id)
          REFERENCES cases.result_revisions(result_id) DEFERRABLE INITIALLY DEFERRED;
        ALTER TABLE ops.ingest_jobs ADD CONSTRAINT job_profile_fk FOREIGN KEY(profile_id) REFERENCES taxonomy.profiles(profile_id);
        ALTER TABLE ops.ingest_jobs ADD CONSTRAINT job_snapshot_fk FOREIGN KEY(base_snapshot_id) REFERENCES corpus.snapshots(snapshot_id);
        ALTER TABLE corpus.claims ADD CONSTRAINT typed_literal_shape CHECK(typed_literal IS NULL OR
          (jsonb_typeof(typed_literal)='object' AND typed_literal ? 'type' AND typed_literal ? 'value'));
        ALTER TABLE taxonomy.assignments ADD CONSTRAINT assignment_state CHECK(status IN ('draft','accepted','needs_review','rejected'));
        ALTER TABLE corpus.claims ADD CONSTRAINT claim_state CHECK(status IN ('draft','accepted','needs_review','rejected'));
        ALTER TABLE corpus.snapshots ADD CONSTRAINT snapshot_state CHECK(status IN ('draft','published','failed'));
        ALTER TABLE ops.stage_attempts ADD CONSTRAINT attempt_state CHECK(status IN ('pending','running','committed','failed'));
        ALTER TABLE ops.outbox ADD CONSTRAINT outbox_state CHECK(status IN ('pending','running','delivered','failed'));
        CREATE UNIQUE INDEX verified_entity_identifier ON corpus.entity_identifiers(authority,kind,identifier_value) WHERE verified;
        CREATE FUNCTION ops.verify_body_hash() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF NEW.body_hash <> encode(sha256(convert_to(NEW.body_text,'UTF8')),'hex') OR NOT EXISTS(
            SELECT 1 FROM corpus.artifacts WHERE artifact_id=NEW.body_artifact_id AND sha256=NEW.body_hash AND status='available') THEN
            RAISE EXCEPTION 'normalized body hash or artifact mismatch';
          END IF;
          RETURN NEW;
        END $$;
        CREATE TRIGGER verify_body_hash BEFORE INSERT ON corpus.document_versions FOR EACH ROW EXECUTE FUNCTION ops.verify_body_hash();
        CREATE FUNCTION ops.verify_claim_scope() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF NOT EXISTS(SELECT 1 FROM corpus.entities e WHERE e.entity_id=NEW.subject_id AND e.scope_id=NEW.scope_id)
            OR (NEW.object_entity_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM corpus.entities e JOIN corpus.scopes s USING(scope_id)
              WHERE e.entity_id=NEW.object_entity_id AND (e.scope_id=NEW.scope_id OR s.kind='public'))) THEN
            RAISE EXCEPTION 'claim entity scope mismatch';
          END IF;
          RETURN NEW;
        END $$;
        CREATE TRIGGER verify_claim_scope BEFORE INSERT ON corpus.claims FOR EACH ROW EXECUTE FUNCTION ops.verify_claim_scope();
        CREATE FUNCTION ops.verify_taxonomy_relation() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF NOT EXISTS(SELECT 1 FROM taxonomy.concepts a JOIN taxonomy.concepts b USING(taxonomy_version_id)
            WHERE a.concept_id=NEW.subject_id AND b.concept_id=NEW.object_id) THEN
            RAISE EXCEPTION 'taxonomy relation version mismatch';
          END IF;
          RETURN NEW;
        END $$;
        CREATE TRIGGER verify_taxonomy_relation BEFORE INSERT ON taxonomy.relations FOR EACH ROW EXECUTE FUNCTION ops.verify_taxonomy_relation();
        CREATE FUNCTION ops.verify_assignment() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE target_scope uuid;
        BEGIN
          IF NEW.chunk_id IS NOT NULL THEN SELECT scope_id INTO target_scope FROM retrieval.chunks WHERE chunk_id=NEW.chunk_id;
          ELSIF NEW.entity_id IS NOT NULL THEN SELECT scope_id INTO target_scope FROM corpus.entities WHERE entity_id=NEW.entity_id;
          ELSE SELECT scope_id INTO target_scope FROM corpus.document_versions WHERE document_version_id=NEW.document_version_id;
          END IF;
          IF target_scope IS DISTINCT FROM NEW.scope_id THEN RAISE EXCEPTION 'assignment target scope mismatch'; END IF;
          RETURN NEW;
        END $$;
        CREATE TRIGGER verify_assignment BEFORE INSERT ON taxonomy.assignments FOR EACH ROW EXECUTE FUNCTION ops.verify_assignment();
        CREATE FUNCTION ops.verify_assignment_evidence() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF NOT EXISTS(SELECT 1 FROM taxonomy.assignments a JOIN corpus.evidence_spans e ON a.scope_id=e.scope_id
            LEFT JOIN retrieval.chunks c ON c.chunk_id=a.chunk_id
            WHERE a.assignment_id=NEW.assignment_id AND e.evidence_id=NEW.evidence_id
              AND (a.document_version_id IS NULL OR a.document_version_id=e.document_version_id)
              AND (a.chunk_id IS NULL OR c.document_version_id=e.document_version_id)) THEN
            RAISE EXCEPTION 'assignment evidence is incompatible';
          END IF;
          RETURN NEW;
        END $$;
        CREATE TRIGGER verify_assignment_evidence BEFORE INSERT ON taxonomy.assignment_evidence
          FOR EACH ROW EXECUTE FUNCTION ops.verify_assignment_evidence();
        CREATE FUNCTION ops.verify_embedding_input() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF NOT EXISTS(SELECT 1 FROM retrieval.chunks WHERE chunk_id=NEW.chunk_id
            AND NEW.input_hash=encode(sha256(convert_to(embedding_text,'UTF8')),'hex')) THEN
            RAISE EXCEPTION 'embedding input hash mismatch';
          END IF;
          RETURN NEW;
        END $$;
        CREATE TRIGGER verify_embedding_input BEFORE INSERT ON retrieval.embeddings FOR EACH ROW EXECUTE FUNCTION ops.verify_embedding_input();
        CREATE FUNCTION ops.verify_run_input() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF NOT EXISTS(SELECT 1 FROM cases.input_revisions WHERE input_id=NEW.input_id AND case_id=NEW.case_id) THEN
            RAISE EXCEPTION 'run input belongs to another case';
          END IF;
          RETURN NEW;
        END $$;
        CREATE TRIGGER verify_run_input BEFORE INSERT OR UPDATE ON cases.runs FOR EACH ROW EXECUTE FUNCTION ops.verify_run_input();
        CREATE FUNCTION ops.pin_run() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF (NEW.case_id,NEW.input_id,NEW.snapshot_id,NEW.thread_id,NEW.configuration)
            IS DISTINCT FROM (OLD.case_id,OLD.input_id,OLD.snapshot_id,OLD.thread_id,OLD.configuration) THEN
            RAISE EXCEPTION 'run pins are immutable';
          END IF;
          RETURN NEW;
        END $$;
        CREATE TRIGGER pin_run BEFORE UPDATE ON cases.runs FOR EACH ROW EXECUTE FUNCTION ops.pin_run();
        CREATE FUNCTION ops.verify_result_lineage() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF NOT EXISTS(SELECT 1 FROM cases.evidence_packs p JOIN cases.runs r USING(run_id)
            WHERE p.pack_id=NEW.pack_id AND r.case_id=NEW.case_id) THEN
            RAISE EXCEPTION 'result pack belongs to another case';
          END IF;
          RETURN NEW;
        END $$;
        CREATE TRIGGER verify_result_lineage BEFORE INSERT ON cases.result_revisions FOR EACH ROW EXECUTE FUNCTION ops.verify_result_lineage();
        CREATE FUNCTION ops.verify_export() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF NOT EXISTS(SELECT 1 FROM cases.reviews r JOIN cases.result_revisions v USING(result_id)
            WHERE r.review_id=NEW.review_id AND r.result_id=NEW.result_id AND r.result_hash=v.result_hash AND r.decision='accepted') THEN
            RAISE EXCEPTION 'export requires the exact accepted review';
          END IF;
          RETURN NEW;
        END $$;
        CREATE TRIGGER verify_export BEFORE INSERT ON cases.exports FOR EACH ROW EXECUTE FUNCTION ops.verify_export();
    """))
    policies = {
        "corpus.fetches": "EXISTS(SELECT 1 FROM corpus.documents d WHERE d.document_id=fetches.document_id)",
        "corpus.document_aliases": "EXISTS(SELECT 1 FROM corpus.documents d WHERE d.document_id=document_aliases.document_id)",
        "corpus.entity_identifiers": "EXISTS(SELECT 1 FROM corpus.entities e WHERE e.entity_id=entity_identifiers.entity_id)",
        "corpus.source_family_memberships": "EXISTS(SELECT 1 FROM corpus.sources s WHERE s.source_id=source_family_memberships.source_id)",
    }
    for target, expression in policies.items():
        connection.execute(text(f"ALTER TABLE {target} ENABLE ROW LEVEL SECURITY"))
        connection.execute(text(f"CREATE POLICY derived_access ON {target} USING({expression}) WITH CHECK({expression})"))


def downgrade():
    raise RuntimeError("restore a validated backup instead of destructive downgrade")
