"""Forward-installable access and immutable guards for case pipeline tables."""
from sqlalchemy import text


def install_pipeline_security(connection):
    rules = {
        "interpretations": "EXISTS(SELECT 1 FROM cases.runs r WHERE r.run_id=interpretations.run_id)",
        "web_research": "EXISTS(SELECT 1 FROM cases.runs r WHERE r.run_id=web_research.run_id)",
        "web_sources": "EXISTS(SELECT 1 FROM cases.web_research w WHERE w.research_id=web_sources.research_id)",
        "claim_assessments": "EXISTS(SELECT 1 FROM cases.runs r WHERE r.run_id=claim_assessments.run_id)",
        "draft_reasons": "EXISTS(SELECT 1 FROM cases.result_revisions r WHERE r.result_id=draft_reasons.result_id)",
        "reason_claims": "EXISTS(SELECT 1 FROM cases.draft_reasons r WHERE r.reason_row_id=reason_claims.reason_row_id)",
        "reason_selections": "EXISTS(SELECT 1 FROM cases.draft_reasons r WHERE r.reason_row_id=reason_selections.reason_row_id)",
        "action_items": "ops.owns_case(case_id)",
    }
    for name, expression in rules.items():
        connection.execute(text(f"ALTER TABLE cases.{name} ENABLE ROW LEVEL SECURITY"))
        connection.execute(text(f"CREATE POLICY pipeline_access ON cases.{name} USING ({expression}) WITH CHECK ({expression})"))
        if name not in {"web_research", "reason_selections", "action_items"}:
            connection.execute(text(f"CREATE TRIGGER immutable BEFORE UPDATE OR DELETE ON cases.{name} FOR EACH ROW EXECUTE FUNCTION ops.prevent_change()"))
    connection.execute(text("""
        CREATE FUNCTION ops.verify_manifest_item() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF NOT EXISTS(SELECT 1 FROM cases.case_evidence_manifests m
            JOIN corpus.evidence_spans e ON e.evidence_id=NEW.evidence_id
            JOIN corpus.scopes s ON s.scope_id=e.scope_id
            WHERE m.manifest_id=NEW.manifest_id AND s.kind='case' AND s.case_id=m.case_id AND NOT s.revoked)
            OR EXISTS(SELECT 1 FROM cases.evidence_packs WHERE manifest_id=NEW.manifest_id) THEN
            RAISE EXCEPTION 'manifest must contain own case evidence and cannot change after pack freeze';
          END IF;
          RETURN NEW;
        END $$;
        CREATE TRIGGER verify_manifest_item BEFORE INSERT ON cases.case_evidence_items
          FOR EACH ROW EXECUTE FUNCTION ops.verify_manifest_item();
        CREATE FUNCTION ops.verify_pipeline_reason_claim() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF NOT EXISTS(SELECT 1 FROM cases.draft_reasons d JOIN cases.result_revisions r USING(result_id)
            JOIN cases.pack_claims p ON p.pack_id=r.pack_id AND p.claim_id=NEW.claim_id
            WHERE d.reason_row_id=NEW.reason_row_id) THEN
            RAISE EXCEPTION 'reason claim must belong to its frozen pack';
          END IF;
          RETURN NEW;
        END $$;
        CREATE TRIGGER verify_pipeline_reason_claim BEFORE INSERT ON cases.reason_claims
          FOR EACH ROW EXECUTE FUNCTION ops.verify_pipeline_reason_claim();
    """))
    # Upgrades must grant existing application roles access to new tables too.
    connection.execute(text("""DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='navigator_app') THEN
        GRANT SELECT,INSERT,UPDATE ON ALL TABLES IN SCHEMA cases TO navigator_app;
      END IF;
    END $$"""))
