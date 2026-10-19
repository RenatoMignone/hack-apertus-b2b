-- A short, case-owned capture of committed, searchable public evidence.
-- SECURITY DEFINER is limited to creating this manifest; no caller-supplied IDs
-- can add source rows, vectors, grants or advance a shared active pointer.
CREATE OR REPLACE FUNCTION ops.capture_live_corpus(target_case uuid, target_profile uuid,
    target_taxonomy uuid, embedding_hash text) RETURNS uuid
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
DECLARE
  space text; profile_config jsonb; taxonomy uuid; config uuid;
  build uuid := gen_random_uuid(); capture uuid := gen_random_uuid();
  manifest jsonb; search_hash text;
BEGIN
  -- Authenticates session_user, principal, namespace and case ownership.
  PERFORM ops.ensure_case_scope(target_case);
  SELECT namespace INTO space FROM cases.cases WHERE case_id=target_case;
  SELECT configuration INTO profile_config FROM taxonomy.profiles
    WHERE profile_id=target_profile AND namespace=space;
  IF profile_config IS NULL THEN
    RAISE EXCEPTION 'profile is unavailable in the application namespace' USING ERRCODE='42501';
  END IF;
  taxonomy := coalesce(target_taxonomy,(profile_config->>'taxonomy_version_id')::uuid);
  IF (profile_config ? 'taxonomy_version_id' AND (profile_config->>'taxonomy_version_id')::uuid<>taxonomy)
      OR NOT EXISTS(SELECT 1 FROM taxonomy.versions WHERE taxonomy_version_id=taxonomy AND status='reviewed') THEN
    RAISE EXCEPTION 'a compatible reviewed taxonomy is required';
  END IF;
  SELECT ec.config_id INTO config FROM retrieval.embedding_configs ec
    JOIN ops.model_configurations m USING(model_config_id)
    WHERE ec.config_hash=embedding_hash AND m.config_hash=embedding_hash AND m.verified
      AND (NOT m.test_only OR space LIKE 'test%' OR space LIKE 'fixture%');
  IF config IS NULL THEN RAISE EXCEPTION 'verified matching embedding configuration is unavailable'; END IF;
  -- This constant is the repository's lexical v1-A-B-D configuration hash.
  search_hash := '671644bd6516e92d80fec0c49ba42df95b3a76f9cfcc480b7d61f054f466424d';
  -- Typed, transaction-local membership avoids expanding/reparsing one huge JSON
  -- bag and gives the planner real cardinalities for membership and claim joins.
  -- CREATE (without IF NOT EXISTS) fails closed if a caller pre-created this name.
  CREATE TEMP TABLE pg_temp.navigator_live_capture_members (
    chunk_id uuid PRIMARY KEY, embedding_id uuid NOT NULL,
    document_version_id uuid NOT NULL, chunker_hash text NOT NULL,
    document_id uuid NOT NULL, created_at timestamptz NOT NULL
  ) ON COMMIT DROP;
  WITH authorized_scopes AS MATERIALIZED (
    SELECT scope_id FROM corpus.scopes
    WHERE kind='public' AND NOT revoked AND ops.can_access(scope_id)
  ), valid_documents AS MATERIALIZED (
    SELECT v.document_version_id,v.document_id,v.created_at,v.scope_id,
      v.body_text || '' AS body_text
    FROM corpus.document_versions v
    JOIN corpus.documents d ON d.document_id=v.document_id AND d.scope_id=v.scope_id
    JOIN corpus.sources src ON src.source_id=d.source_id AND src.scope_id=v.scope_id
    JOIN authorized_scopes sc ON sc.scope_id=v.scope_id
    JOIN corpus.artifacts body ON body.artifact_id=v.body_artifact_id
      AND body.status='available' AND body.sha256=v.body_hash
    JOIN corpus.artifacts raw ON raw.artifact_id=v.raw_artifact_id AND raw.status='available'
    WHERE v.status='accepted' AND src.status='active'
  ), ready AS MATERIALIZED (
    SELECT DISTINCT ON (c.chunk_id) c.chunk_id,e.embedding_id,c.document_version_id,
      c.chunker_hash,v.document_id,v.created_at
    FROM valid_documents v
    JOIN retrieval.chunks c ON c.document_version_id=v.document_version_id AND c.scope_id=v.scope_id
    JOIN retrieval.embeddings e ON e.chunk_id=c.chunk_id AND e.config_id=config
    JOIN retrieval.embedding_configs ec ON ec.config_id=e.config_id
    WHERE public.vector_dims(e.vector)=ec.dimension AND public.vector_norm(e.vector)>0
      AND substring(v.body_text FROM c.char_start+1 FOR c.char_end-c.char_start)=c.literal_text
      AND EXISTS(SELECT 1 FROM retrieval.search_documents p
        WHERE p.chunk_id=c.chunk_id AND p.search_config_hash=search_hash)
      AND EXISTS(SELECT 1 FROM retrieval.chunk_evidence ce JOIN corpus.evidence_spans es USING(evidence_id)
        WHERE ce.chunk_id=c.chunk_id AND es.document_version_id=c.document_version_id
          AND es.scope_id=c.scope_id)
    ORDER BY c.chunk_id,e.created_at DESC,e.embedding_id DESC
  ), ranked AS (
    -- A single window sort avoids re-running DISTINCT/newest sorting for every
    -- chunk when the planner underestimates the ready CTE's cardinality.
    SELECT r.*,dense_rank() OVER (PARTITION BY document_id
      ORDER BY created_at DESC,document_version_id DESC) AS version_rank FROM ready r
  )
  INSERT INTO pg_temp.navigator_live_capture_members
    SELECT chunk_id,embedding_id,document_version_id,chunker_hash,document_id,created_at
      FROM ranked WHERE version_rank=1;
  IF NOT FOUND THEN RAISE EXCEPTION 'no complete compatible public chunks are readable yet'; END IF;
  CREATE INDEX ON pg_temp.navigator_live_capture_members(document_version_id);
  ANALYZE pg_temp.navigator_live_capture_members;
  SELECT jsonb_build_object('mode','live','runtime_case_id',target_case,'captured_at',clock_timestamp(),
    'chunks',jsonb_agg(chunk_id ORDER BY chunk_id),
    'documents',(SELECT jsonb_agg(v ORDER BY v) FROM (
      SELECT DISTINCT document_version_id v FROM pg_temp.navigator_live_capture_members) d),
    'chunker_hashes',(SELECT jsonb_agg(v ORDER BY v) FROM (
      SELECT DISTINCT chunker_hash v FROM pg_temp.navigator_live_capture_members) h),
    'limitation','live_corpus_incomplete_coverage') INTO manifest
    FROM pg_temp.navigator_live_capture_members;
  INSERT INTO retrieval.index_builds(build_id,config_id,namespace,chunker_hash,search_config_hash,validation_manifest)
    VALUES(build,config,space,encode(sha256(convert_to((manifest->'chunker_hashes')::text,'UTF8')),'hex'),
      search_hash,jsonb_build_object('mode','live','runtime_case_id',target_case));
  INSERT INTO corpus.snapshots(snapshot_id,profile_id,taxonomy_version_id,build_id,namespace,
      schema_version,manifest,manifest_hash)
    VALUES(capture,target_profile,taxonomy,build,space,'1.0',manifest,
      encode(sha256(convert_to(manifest::text,'UTF8')),'hex'));
  INSERT INTO corpus.snapshot_documents(snapshot_id,document_version_id)
    SELECT DISTINCT capture,document_version_id FROM pg_temp.navigator_live_capture_members;
  INSERT INTO retrieval.snapshot_chunks(snapshot_id,chunk_id,embedding_id)
    SELECT capture,chunk_id,embedding_id FROM pg_temp.navigator_live_capture_members;
  INSERT INTO corpus.snapshot_claims(snapshot_id,claim_id)
    SELECT capture,c.claim_id FROM corpus.claims c
    JOIN corpus.scopes s ON s.scope_id=c.scope_id
    WHERE c.status='accepted' AND s.kind='public' AND ops.can_access(c.scope_id)
      AND EXISTS(SELECT 1 FROM corpus.claim_evidence ce WHERE ce.claim_id=c.claim_id
        AND ce.relation='supports' AND ce.review_decision='accepted')
      AND NOT EXISTS(SELECT 1 FROM corpus.claim_evidence ce JOIN corpus.evidence_spans es USING(evidence_id)
        WHERE ce.claim_id=c.claim_id AND ce.relation='supports' AND ce.review_decision='accepted'
          AND (NOT ops.can_access(es.scope_id) OR NOT EXISTS(SELECT 1 FROM pg_temp.navigator_live_capture_members m
            WHERE m.document_version_id=es.document_version_id)))
      AND EXISTS(SELECT 1 FROM corpus.entities e WHERE e.entity_id=c.subject_id AND ops.can_access(e.scope_id))
      AND (c.object_entity_id IS NULL OR EXISTS(SELECT 1 FROM corpus.entities e
        WHERE e.entity_id=c.object_entity_id AND ops.can_access(e.scope_id)));
  INSERT INTO corpus.snapshot_entities(snapshot_id,entity_id)
    SELECT capture,c.subject_id FROM corpus.claims c JOIN corpus.snapshot_claims sc USING(claim_id)
      WHERE sc.snapshot_id=capture
    UNION SELECT capture,c.object_entity_id FROM corpus.claims c JOIN corpus.snapshot_claims sc USING(claim_id)
      WHERE sc.snapshot_id=capture AND c.object_entity_id IS NOT NULL;
  UPDATE corpus.snapshots SET manifest=corpus.snapshots.manifest || jsonb_build_object(
      'claims',coalesce((SELECT jsonb_agg(claim_id ORDER BY claim_id) FROM corpus.snapshot_claims WHERE snapshot_id=capture),'[]'::jsonb),
      'entities',coalesce((SELECT jsonb_agg(entity_id ORDER BY entity_id) FROM corpus.snapshot_entities WHERE snapshot_id=capture),'[]'::jsonb))
    WHERE snapshot_id=capture;
  UPDATE corpus.snapshots SET manifest_hash=encode(sha256(convert_to(corpus.snapshots.manifest::text,'UTF8')),'hex')
    WHERE snapshot_id=capture;
  -- Seal only after all membership triggers have checked the draft. No publication.
  UPDATE retrieval.index_builds SET status='live' WHERE build_id=build;
  UPDATE corpus.snapshots SET status='live' WHERE snapshot_id=capture;
  DROP TABLE pg_temp.navigator_live_capture_members;
  RETURN capture;
END $$;
