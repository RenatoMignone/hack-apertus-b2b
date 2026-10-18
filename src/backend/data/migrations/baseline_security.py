"""Historical 0001 security installer. New schema changes belong in forward migrations."""
from sqlalchemy import text


def install_security(connection, *, metadata, exclude=()):
    connection.execute(text("""
        CREATE FUNCTION ops.can_access(target uuid, writing boolean DEFAULT false)
        RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $$
          SELECT EXISTS (
            SELECT 1 FROM ops.scope_grants g JOIN ops.principals p USING(principal_id)
              JOIN corpus.scopes s USING(scope_id)
            WHERE g.scope_id=target AND NOT s.revoked AND p.active
              AND p.database_role=session_user
              AND p.principal_id::text=current_setting('navigator.principal', true)
              AND p.namespace=current_setting('navigator.namespace', true)
              AND (NOT writing OR g.can_write))
        $$
    """))
    connection.execute(text("""
        CREATE FUNCTION ops.owns_case(target uuid) RETURNS boolean
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $$
          SELECT EXISTS (SELECT 1 FROM cases.cases c JOIN ops.principals p ON p.principal_id=c.owner_id
            WHERE c.case_id=target AND p.active AND p.database_role=session_user
              AND p.principal_id::text=current_setting('navigator.principal', true)
              AND p.namespace=current_setting('navigator.namespace', true))
        $$
    """))
    connection.execute(text("""
        CREATE FUNCTION ops.check_literal() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE body text; version_scope uuid;
        BEGIN
          SELECT body_text, scope_id INTO body, version_scope FROM corpus.document_versions
            WHERE document_version_id=NEW.document_version_id;
          IF NEW.scope_id <> version_scope OR
            substring(body FROM NEW.char_start+1 FOR NEW.char_end-NEW.char_start) IS DISTINCT FROM NEW.literal_text THEN
            RAISE EXCEPTION 'invalid literal body slice or scope';
          END IF;
          RETURN NEW;
        END $$
    """))
    for target in ("corpus.evidence_spans", "retrieval.chunks"):
        connection.execute(text(f"CREATE TRIGGER check_literal BEFORE INSERT OR UPDATE ON {target} FOR EACH ROW EXECUTE FUNCTION ops.check_literal()"))
    connection.execute(text("""
        CREATE FUNCTION ops.check_document_scope() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF NEW.scope_id IS DISTINCT FROM (SELECT scope_id FROM corpus.documents WHERE document_id=NEW.document_id) THEN
            RAISE EXCEPTION 'document version scope mismatch';
          END IF;
          RETURN NEW;
        END $$;
        CREATE TRIGGER check_document_scope BEFORE INSERT OR UPDATE ON corpus.document_versions
          FOR EACH ROW EXECUTE FUNCTION ops.check_document_scope();
        CREATE FUNCTION ops.check_source_scope() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF NEW.scope_id IS DISTINCT FROM (SELECT scope_id FROM corpus.sources WHERE source_id=NEW.source_id) THEN
            RAISE EXCEPTION 'source scope mismatch';
          END IF;
          RETURN NEW;
        END $$;
        CREATE TRIGGER check_source_scope BEFORE INSERT OR UPDATE ON corpus.documents
          FOR EACH ROW EXECUTE FUNCTION ops.check_source_scope();
        CREATE FUNCTION ops.check_embedding() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE expected integer;
        BEGIN
          SELECT dimension INTO expected FROM retrieval.embedding_configs WHERE config_id=NEW.config_id;
          IF vector_dims(NEW.vector) <> expected OR vector_norm(NEW.vector)=0 OR
             NEW.vector::text ~ '(NaN|Infinity)' THEN
            RAISE EXCEPTION 'invalid embedding dimension or values';
          END IF;
          RETURN NEW;
        END $$;
        CREATE TRIGGER check_embedding BEFORE INSERT OR UPDATE ON retrieval.embeddings
          FOR EACH ROW EXECUTE FUNCTION ops.check_embedding();
        CREATE FUNCTION ops.check_chunk_evidence() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF NOT EXISTS (SELECT 1 FROM retrieval.chunks c JOIN corpus.evidence_spans e
            ON c.document_version_id=e.document_version_id AND c.scope_id=e.scope_id
            WHERE c.chunk_id=NEW.chunk_id AND e.evidence_id=NEW.evidence_id) THEN
            RAISE EXCEPTION 'chunk evidence version mismatch';
          END IF;
          RETURN NEW;
        END $$;
        CREATE TRIGGER check_chunk_evidence BEFORE INSERT OR UPDATE ON retrieval.chunk_evidence
          FOR EACH ROW EXECUTE FUNCTION ops.check_chunk_evidence();
        CREATE FUNCTION ops.check_claim_evidence() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF NOT EXISTS (SELECT 1 FROM corpus.claims c JOIN corpus.evidence_spans e ON c.scope_id=e.scope_id
            WHERE c.claim_id=NEW.claim_id AND e.evidence_id=NEW.evidence_id) THEN
            RAISE EXCEPTION 'claim support scope mismatch';
          END IF;
          RETURN NEW;
        END $$;
        CREATE TRIGGER check_claim_evidence BEFORE INSERT OR UPDATE ON corpus.claim_evidence
          FOR EACH ROW EXECUTE FUNCTION ops.check_claim_evidence();
        CREATE FUNCTION ops.require_support() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF NEW.status='accepted' AND NOT EXISTS (SELECT 1 FROM corpus.claim_evidence
            WHERE claim_id=NEW.claim_id AND relation='supports' AND review_decision='accepted') THEN
            RAISE EXCEPTION 'accepted claim requires reviewed supporting evidence';
          END IF;
          RETURN NEW;
        END $$;
        CREATE CONSTRAINT TRIGGER require_support AFTER INSERT OR UPDATE ON corpus.claims
          DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION ops.require_support();
        CREATE FUNCTION ops.check_membership() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF NOT EXISTS (
            SELECT 1 FROM corpus.snapshots s JOIN retrieval.index_builds b ON b.build_id=s.build_id
            JOIN retrieval.embeddings e ON e.config_id=b.config_id AND e.embedding_id=NEW.embedding_id
            JOIN retrieval.chunks c ON c.chunk_id=e.chunk_id AND c.chunk_id=NEW.chunk_id
            JOIN corpus.snapshot_documents d ON d.snapshot_id=s.snapshot_id AND d.document_version_id=c.document_version_id
            WHERE s.snapshot_id=NEW.snapshot_id AND s.status='draft') THEN
            RAISE EXCEPTION 'incompatible snapshot chunk membership';
          END IF;
          RETURN NEW;
        END $$;
        CREATE TRIGGER check_membership BEFORE INSERT OR UPDATE ON retrieval.snapshot_chunks
          FOR EACH ROW EXECUTE FUNCTION ops.check_membership();
        CREATE FUNCTION ops.prevent_change() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'immutable record; create a new revision'; END $$;
        CREATE FUNCTION ops.freeze_membership() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE target uuid;
        BEGIN
          IF TG_OP='DELETE' THEN target=OLD.snapshot_id; ELSE target=NEW.snapshot_id; END IF;
          IF EXISTS(SELECT 1 FROM corpus.snapshots WHERE snapshot_id=target AND status='published') THEN
            RAISE EXCEPTION 'published membership is immutable';
          END IF;
          IF TG_OP='DELETE' THEN RETURN OLD; ELSE RETURN NEW; END IF;
        END $$
    """))
    immutable = ("corpus.document_versions", "corpus.evidence_spans", "corpus.claims", "corpus.claim_evidence",
                 "corpus.derivations", "retrieval.chunks", "retrieval.chunk_evidence", "retrieval.embeddings",
                 "retrieval.embedding_configs", "retrieval.search_documents", "ops.model_configurations",
                 "taxonomy.profiles", "taxonomy.versions", "taxonomy.concepts", "taxonomy.labels", "taxonomy.relations",
                 "taxonomy.assignments", "taxonomy.assignment_evidence", "cases.input_revisions", "cases.dialogue_turns",
                 "cases.query_plans", "cases.case_evidence_manifests", "cases.case_evidence_items",
                 "cases.evidence_packs", "cases.pack_items", "cases.pack_claims", "cases.result_revisions", "cases.reviews")
    for target in immutable:
        connection.execute(text(f"CREATE TRIGGER immutable BEFORE UPDATE OR DELETE ON {target} FOR EACH ROW EXECUTE FUNCTION ops.prevent_change()"))
    for target in ("corpus.snapshot_documents", "corpus.snapshot_entities", "corpus.snapshot_claims", "retrieval.snapshot_chunks"):
        connection.execute(text(f"CREATE TRIGGER freeze_membership BEFORE INSERT OR UPDATE OR DELETE ON {target} FOR EACH ROW EXECUTE FUNCTION ops.freeze_membership()"))
    for target in ("corpus.snapshots", "retrieval.index_builds"):
        connection.execute(text(f"CREATE TRIGGER freeze_published BEFORE UPDATE OR DELETE ON {target} FOR EACH ROW WHEN (OLD.status='published') EXECUTE FUNCTION ops.prevent_change()"))

    rules = {
        "ops.principals": "database_role=session_user",
        "ops.scope_grants": "false",
        "corpus.scopes": "ops.can_access(scope_id)",
        "cases.cases": "ops.owns_case(case_id)",
        "cases.runs": "ops.owns_case(case_id)",
        "retrieval.embeddings": "EXISTS(SELECT 1 FROM retrieval.chunks c WHERE c.chunk_id=embeddings.chunk_id)",
        "retrieval.search_documents": "EXISTS(SELECT 1 FROM retrieval.chunks c WHERE c.chunk_id=search_documents.chunk_id)",
        "corpus.claim_evidence": "EXISTS(SELECT 1 FROM corpus.claims c WHERE c.claim_id=claim_evidence.claim_id)",
        "retrieval.chunk_evidence": "EXISTS(SELECT 1 FROM retrieval.chunks c WHERE c.chunk_id=chunk_evidence.chunk_id)",
        "taxonomy.assignment_evidence": "EXISTS(SELECT 1 FROM taxonomy.assignments a WHERE a.assignment_id=assignment_evidence.assignment_id)",
    }
    case_links = {
        "input_revisions": "ops.owns_case(case_id)", "dialogue_turns": "ops.owns_case(case_id)",
        "case_evidence_manifests": "ops.owns_case(case_id)", "result_revisions": "ops.owns_case(case_id)",
        "questions": "EXISTS(SELECT 1 FROM cases.runs r WHERE r.run_id=questions.run_id)",
        "answers": "EXISTS(SELECT 1 FROM cases.questions q WHERE q.question_id=answers.question_id)",
        "query_plans": "EXISTS(SELECT 1 FROM cases.runs r WHERE r.run_id=query_plans.run_id)",
        "retrieval_rounds": "EXISTS(SELECT 1 FROM cases.query_plans q WHERE q.query_plan_id=retrieval_rounds.query_plan_id)",
        "retrieval_hits": "EXISTS(SELECT 1 FROM cases.retrieval_rounds r WHERE r.round_id=retrieval_hits.round_id)",
        "matches": "EXISTS(SELECT 1 FROM cases.runs r WHERE r.run_id=matches.run_id)",
        "match_support": "EXISTS(SELECT 1 FROM cases.matches m WHERE m.match_id=match_support.match_id)",
        "case_evidence_items": "EXISTS(SELECT 1 FROM cases.case_evidence_manifests m WHERE m.manifest_id=case_evidence_items.manifest_id)",
        "evidence_packs": "EXISTS(SELECT 1 FROM cases.runs r WHERE r.run_id=evidence_packs.run_id)",
        "pack_items": "EXISTS(SELECT 1 FROM cases.evidence_packs p WHERE p.pack_id=pack_items.pack_id)",
        "pack_claims": "EXISTS(SELECT 1 FROM cases.evidence_packs p WHERE p.pack_id=pack_claims.pack_id)",
        "selections": "EXISTS(SELECT 1 FROM cases.result_revisions r WHERE r.result_id=selections.result_id)",
        "reviews": "EXISTS(SELECT 1 FROM cases.result_revisions r WHERE r.result_id=reviews.result_id)",
        "exports": "EXISTS(SELECT 1 FROM cases.result_revisions r WHERE r.result_id=exports.result_id)",
    }
    rules.update({f"cases.{name}": expression for name, expression in case_links.items()})
    for target in metadata.tables.values():
        fullname = target.fullname
        if fullname in exclude:
            continue
        expression = rules.get(fullname)
        if expression is None and "scope_id" in target.c:
            expression = "ops.can_access(scope_id)"
        if expression is None and "namespace" in target.c:
            expression = "namespace=current_setting('navigator.namespace', true)"
        if expression is None:
            continue
        connection.execute(text(f"ALTER TABLE {fullname} ENABLE ROW LEVEL SECURITY"))
        connection.execute(text(f"CREATE POLICY read_access ON {fullname} FOR SELECT USING ({expression})"))
        writing = expression.replace("ops.can_access(scope_id)", "ops.can_access(scope_id, true)")
        if fullname == "cases.cases":
            writing = "owner_id::text=current_setting('navigator.principal',true) AND namespace=current_setting('navigator.namespace',true)"
        if fullname in {"ops.principals", "ops.scope_grants"}:
            writing = "false"
        connection.execute(text(f"CREATE POLICY insert_access ON {fullname} FOR INSERT WITH CHECK ({writing})"))
        connection.execute(text(f"CREATE POLICY update_access ON {fullname} FOR UPDATE USING ({writing}) WITH CHECK ({writing})"))
        connection.execute(text(f"CREATE POLICY delete_access ON {fullname} FOR DELETE USING ({writing})"))
