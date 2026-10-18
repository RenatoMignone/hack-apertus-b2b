from uuid import uuid4, uuid5

from sqlalchemy import insert, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from backend.contracts.data import configuration_hash, content_hash
from backend.contracts.pipeline import canonical_url
from backend.data import schema as tables
from backend.data.database import require_scope, transaction
from backend.data.repositories.corpus import CorpusRepository
from backend.data.repositories.snapshots import SnapshotRepository
from backend.ingestion.normalize import PARSER_HASH, chunks, normalize
from backend.ingestion.mesh import MeSHTagger


class CorpusBuilder:
    def __init__(self, engine, artifacts, embedder, configuration, *, classifier=None, vocabulary=None):
        if configuration.config_hash != embedder.config_hash:
            raise ValueError("ingestion encoder/configuration mismatch")
        configuration.require_resolved()
        self.engine, self.embedder, self.configuration = engine, embedder, configuration
        self.classifier, self.vocabulary = classifier, vocabulary
        self.corpus = CorpusRepository(engine, artifacts)
        self.snapshots = SnapshotRepository(engine)
        self.chunker_hash = configuration_hash({"chunker": "unicode-budgeted-v1", "max_characters": 2400,
            "embedding_config": configuration.config_hash})

    def ingest(self, access, *, scope_id, source_id, observation, reviewed_claims=(),
               taxonomy_version_id=None, tag_proposals=(), tag_reviewer=None, specific_subjects=()):
        document = normalize(observation.raw, observation.mime, fallback_title=observation.final_url)
        if taxonomy_version_id and self.classifier and not tag_proposals:
            if self.vocabulary is None:
                raise ValueError("configured classification requires pinned MeSH vocabulary")
            classification = self.classifier.analyze(document, self.vocabulary)
            tag_proposals, specific_subjects = classification["tags"], classification["subjects"]
        url = canonical_url(observation.final_url)
        version_id = self.corpus.stage_document(access, scope_id=scope_id, source_id=source_id, url=url,
            title=document.title, language=document.language, raw=observation.raw, body=document.body, spans=document.spans,
            parser_hash=PARSER_HASH, raw_mime=observation.mime, http_status=observation.status, source_date=document.published_at)
        with transaction(self.engine, access) as connection:
            require_scope(connection, scope_id, write=True)
            document_id = connection.execute(select(tables.versions.c.document_id).where(tables.versions.c.document_version_id == version_id)).scalar_one()
            for alias in dict.fromkeys([observation.requested_url, *observation.redirects]):
                connection.execute(pg_insert(tables.aliases).values(alias_id=uuid4(), document_id=document_id, url=canonical_url(alias))
                    .on_conflict_do_nothing(index_elements=["document_id", "url"]))
            connection.execute(insert(tables.fetches).values(fetch_id=uuid4(), document_id=document_id,
                requested_url=observation.requested_url, final_url=observation.final_url, http_status=observation.status,
                raw_artifact_id=connection.execute(select(tables.versions.c.raw_artifact_id).where(
                    tables.versions.c.document_version_id == version_id)).scalar_one(), created_at=observation.fetched_at,
                redirects={"urls": list(observation.redirects)}, headers={"content-type": observation.mime, "kind": "actual-network-observation"}))
        config_id = self.corpus.register_embedding(access, self.configuration)
        passages = chunks(document, lambda value, headings: self.embedder.accepts_document(value, document.title, " / ".join(headings)))
        inputs = [self.embedder.document_input(span.text, document.title, " / ".join(span.heading_path)) for span in passages]
        vectors = [None] * len(passages)
        with transaction(self.engine, access) as connection:
            for index, span in enumerate(passages):
                cached = connection.execute(select(tables.embeddings.c.vector).join(tables.chunks).where(
                    tables.chunks.c.document_version_id == version_id, tables.chunks.c.char_start == span.char_start,
                    tables.chunks.c.char_end == span.char_end, tables.chunks.c.chunker_hash == self.chunker_hash,
                    tables.embeddings.c.config_id == config_id, tables.embeddings.c.input_hash == content_hash(inputs[index].encode()))).scalar_one_or_none()
                if cached is not None:
                    vectors[index] = list(map(float, cached))
        missing = [index for index, vector in enumerate(vectors) if vector is None]
        encoded = self.embedder.embed_documents([inputs[index] for index in missing])
        if len(encoded) != len(missing):
            raise ValueError("document embedding batch length mismatch")
        for index, vector in zip(missing, encoded, strict=True):
            vectors[index] = vector
        chunk_ids = [self.corpus.stage_chunk(access, version_id=version_id, span=span, chunker_hash=self.chunker_hash,
            config_id=config_id, vector=vector) for span, vector in zip(passages, vectors, strict=True)]
        entity_ids, claim_ids = [], []
        with transaction(self.engine, access) as connection:
            require_scope(connection, scope_id, write=True)
            for proposal in reviewed_claims:
                if not proposal.get("reviewer") or not proposal["label"] or proposal["label"] not in document.body:
                    raise ValueError("reviewed source-supported entity label required")
                span = proposal["span"]
                span.validate_body(document.body)
                subject_id = uuid5(scope_id, proposal["identity"])
                connection.execute(pg_insert(tables.entities).values(entity_id=subject_id, scope_id=scope_id,
                    entity_type=proposal["entity_type"], display_label=proposal["label"], status="accepted").on_conflict_do_nothing())
                identity = connection.execute(select(tables.entities).where(tables.entities.c.entity_id == subject_id)).mappings().one()
                if identity["entity_type"] != proposal["entity_type"] or identity["display_label"] != proposal["label"]:
                    raise ValueError("source-supported entity identity conflicts; explicit resolution required")
                evidence_id = connection.execute(select(tables.spans.c.evidence_id).where(tables.spans.c.document_version_id == version_id,
                    tables.spans.c.char_start == span.char_start, tables.spans.c.char_end == span.char_end)).scalar_one_or_none()
                if not evidence_id:
                    evidence_id = uuid4()
                    connection.execute(insert(tables.spans).values(evidence_id=evidence_id, document_version_id=version_id, scope_id=scope_id,
                        char_start=span.char_start, char_end=span.char_end, literal_text=span.text, heading_path=span.heading_path,
                        page=span.page, extraction_method="reviewed-import"))
                claim_id = uuid5(subject_id, configuration_hash({"version": str(version_id), "predicate": proposal["predicate"],
                    "literal": proposal.get("typed_literal"), "object": proposal.get("object_identity"), "evidence": str(evidence_id)}))
                object_id = uuid5(scope_id, proposal["object_identity"]) if proposal.get("object_identity") else None
                connection.execute(pg_insert(tables.claims).values(claim_id=claim_id, scope_id=scope_id, subject_id=subject_id,
                    predicate=proposal["predicate"], typed_literal=proposal.get("typed_literal"), object_entity_id=object_id,
                    status="accepted").on_conflict_do_nothing())
                connection.execute(pg_insert(tables.claim_evidence).values(claim_id=claim_id, evidence_id=evidence_id,
                    relation="supports", review_decision="accepted").on_conflict_do_nothing())
                entity_ids.extend([subject_id, *([object_id] if object_id else [])])
                claim_ids.append(claim_id)
        if tag_proposals and taxonomy_version_id is None:
            raise ValueError("tagging requires a pinned MeSH taxonomy version")
        tag_ids = MeSHTagger(self.engine).assign(access, version_id, taxonomy_version_id, tag_proposals,
            reviewer=tag_reviewer, subjects=specific_subjects) if taxonomy_version_id else []
        return {"version_id": version_id, "chunk_ids": chunk_ids, "entity_ids": sorted(set(entity_ids), key=str),
            "claim_ids": claim_ids, "config_id": config_id, "url": url, "published_at": document.published_at,
            "body_hash": content_hash(document.body.encode()), "language": document.language, "tag_assignment_ids": tag_ids,
            "tagging_status": "assigned" if tag_ids else "unknown" if taxonomy_version_id else "unavailable",
            "specific_subjects": [subject.model_dump(mode="json") for subject in specific_subjects]}

    def publish(self, access, records, *, profile_id, taxonomy_version_id, expected_active=None):
        if not records or any(not row["claim_ids"] for row in records):
            raise ValueError("real pilot publication requires reviewed entity/claim records for every source")
        config_ids = {row["config_id"] for row in records}
        if len(config_ids) != 1:
            raise ValueError("snapshot cannot mix embedding spaces")
        snapshot_id = self.snapshots.stage(access, profile_id=profile_id, taxonomy_version_id=taxonomy_version_id,
            config_id=next(iter(config_ids)), chunk_ids=list(dict.fromkeys(key for row in records for key in row["chunk_ids"])),
            entity_ids=list({key for row in records for key in row["entity_ids"]}),
            claim_ids=list({key for row in records for key in row["claim_ids"]}), chunker_hash=self.chunker_hash)
        self.snapshots.publish(access, snapshot_id, expected_active=expected_active)
        return self.snapshots.get(access, profile_id=profile_id, snapshot_id=snapshot_id)
