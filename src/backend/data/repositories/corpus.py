from datetime import datetime
from uuid import uuid4

from sqlalchemy import insert, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from backend.contracts.data import (ArtifactRef, ModelConfiguration, Span, configuration_hash,
                                    content_hash, validate_vector)
from backend.data import schema as tables
from backend.data.database import require_scope, transaction


LANGUAGE_CONFIGS = {"en": "english", "de": "german", "fr": "french", "it": "italian"}


def save_artifact(connection, reference: ArtifactRef):
    artifact_id = uuid4()
    statement = pg_insert(tables.artifacts).values(
        artifact_id=artifact_id, storage_key=reference.key, sha256=reference.sha256,
        mime=reference.mime, byte_count=reference.byte_count).on_conflict_do_nothing(index_elements=["storage_key"])
    connection.execute(statement)
    return connection.execute(select(tables.artifacts.c.artifact_id).where(
        tables.artifacts.c.storage_key == reference.key)).scalar_one()


class CorpusRepository:
    def __init__(self, engine, artifacts):
        self.engine = engine
        self.artifacts = artifacts

    def record_entity(self, access, *, scope_id, entity_type, display_label):
        if entity_type not in {"person", "unit", "organization", "project", "facility", "service"} or not display_label.strip():
            raise ValueError("entity needs a supported type and nonempty identity label")
        with transaction(self.engine, access) as connection:
            require_scope(connection, scope_id, write=True)
            entity_id = uuid4()
            connection.execute(insert(tables.entities).values(entity_id=entity_id, scope_id=scope_id,
                entity_type=entity_type, display_label=display_label, status="needs_review"))
            return entity_id

    def record_claim(self, access, *, scope_id, subject_id, predicate, evidence_ids,
                     object_entity_id=None, typed_literal=None, accepted=False, derivation_id=None):
        if (object_entity_id is None) == (typed_literal is None) or not evidence_ids:
            raise ValueError("claim needs exactly one object and supporting evidence")
        if typed_literal is not None and (not isinstance(typed_literal, dict) or not {"type", "value"}.issubset(typed_literal)):
            raise ValueError("literal requires explicit type and value")
        with transaction(self.engine, access) as connection:
            require_scope(connection, scope_id, write=True)
            evidence = connection.execute(select(tables.spans).where(tables.spans.c.evidence_id.in_(evidence_ids),
                tables.spans.c.scope_id == scope_id)).mappings().all()
            if len(evidence) != len(set(evidence_ids)):
                raise PermissionError("support must resolve in the claim scope")
            claim_id = uuid4()
            connection.execute(insert(tables.claims).values(claim_id=claim_id, scope_id=scope_id, subject_id=subject_id,
                predicate=predicate, object_entity_id=object_entity_id, typed_literal=typed_literal,
                derivation_id=derivation_id, status="accepted" if accepted else "needs_review"))
            for evidence_id in set(evidence_ids):
                connection.execute(insert(tables.claim_evidence).values(claim_id=claim_id, evidence_id=evidence_id,
                    relation="supports", review_decision="accepted" if accepted else "needs_review"))
            return claim_id

    def stage_document(self, access, *, scope_id, source_id, url, title, language, raw: bytes,
                       body: str, spans: list[Span], parser_hash: str, raw_mime="text/html", http_status=None,
                       source_date: datetime | None = None):
        if source_date is not None and source_date.tzinfo is None:
            raise ValueError("source publication date must be timezone-aware")
        for span in spans:
            span.validate_body(body)
        with transaction(self.engine, access) as connection:
            require_scope(connection, scope_id, write=True)
            source_scope = connection.execute(select(tables.sources.c.scope_id).where(
                tables.sources.c.source_id == source_id)).scalar_one()
            if source_scope != scope_id:
                raise ValueError("source scope does not match document scope")
        raw_reference = self.artifacts.put(raw, raw_mime)
        body_reference = self.artifacts.put(body.encode(), "text/plain; charset=utf-8")
        with transaction(self.engine, access) as connection:
            require_scope(connection, scope_id, write=True)
            raw_id = save_artifact(connection, raw_reference)
            body_id = save_artifact(connection, body_reference)
            document_id = uuid4()
            connection.execute(pg_insert(tables.documents).values(document_id=document_id, source_id=source_id,
                canonical_url=url, scope_id=scope_id).on_conflict_do_nothing(index_elements=["scope_id", "canonical_url"]))
            document_id = connection.execute(select(tables.documents.c.document_id).where(
                tables.documents.c.scope_id == scope_id, tables.documents.c.canonical_url == url)).scalar_one()
            existing = connection.execute(select(tables.versions.c.document_version_id).where(
                tables.versions.c.document_id == document_id, tables.versions.c.body_hash == body_reference.sha256,
                tables.versions.c.parser_hash == parser_hash)).scalar_one_or_none()
            connection.execute(insert(tables.fetches).values(fetch_id=uuid4(), document_id=document_id,
                requested_url=url, final_url=url, http_status=http_status, raw_artifact_id=raw_id))
            if existing:
                return existing
            version_id = uuid4()
            connection.execute(insert(tables.versions).values(document_version_id=version_id, document_id=document_id,
                scope_id=scope_id, raw_artifact_id=raw_id, body_artifact_id=body_id, body_hash=body_reference.sha256,
                body_text=body, parser_hash=parser_hash, language=language, title=title, source_date=source_date))
            for span in spans:
                connection.execute(insert(tables.spans).values(evidence_id=uuid4(), document_version_id=version_id,
                    scope_id=scope_id, char_start=span.char_start, char_end=span.char_end, literal_text=span.text,
                    heading_path=span.heading_path, page=span.page, extraction_method="normalized-text"))
            return version_id

    def register_embedding(self, access, configuration: ModelConfiguration):
        configuration.require_resolved()
        if configuration.role != "embedding":
            raise ValueError("embedding role required")
        if configuration.test_only and not access.namespace.startswith(("test", "fixture")):
            raise ValueError("test model is restricted to test/fixture namespaces")
        with transaction(self.engine, access) as connection:
            model_id, config_id = uuid4(), uuid4()
            connection.execute(pg_insert(tables.models).values(model_config_id=model_id, role=configuration.role,
                config_hash=configuration.config_hash, configuration=configuration.model_dump(), verified=True,
                test_only=configuration.test_only).on_conflict_do_nothing(index_elements=["config_hash"]))
            model_id = connection.execute(select(tables.models.c.model_config_id).where(
                tables.models.c.config_hash == configuration.config_hash)).scalar_one()
            connection.execute(pg_insert(tables.embedding_configs).values(config_id=config_id, model_config_id=model_id,
                config_hash=configuration.config_hash, dimension=configuration.dimension,
                encoding={"query_template": configuration.query_template, "document_template": configuration.document_template,
                          "normalization": configuration.normalization}).on_conflict_do_nothing(index_elements=["config_hash"]))
            return connection.execute(select(tables.embedding_configs.c.config_id).where(
                tables.embedding_configs.c.config_hash == configuration.config_hash)).scalar_one()

    def stage_chunk(self, access, *, version_id, span: Span, chunker_hash, config_id, vector: list[float]):
        with transaction(self.engine, access) as connection:
            version = connection.execute(select(tables.versions).where(
                tables.versions.c.document_version_id == version_id)).mappings().one()
            require_scope(connection, version["scope_id"], write=True)
            span.validate_body(version["body_text"])
            config = connection.execute(select(tables.embedding_configs, tables.models.c.test_only).join(
                tables.models, tables.models.c.model_config_id == tables.embedding_configs.c.model_config_id).where(
                tables.embedding_configs.c.config_id == config_id)).mappings().one()
            if config["test_only"] and not access.namespace.startswith(("test", "fixture")):
                raise ValueError("test embeddings cannot enter a real corpus")
            validate_vector(vector, config["dimension"])
            embedding_text = config["encoding"]["document_template"].format(
                text=span.text, title=version["title"], headings=" / ".join(span.heading_path))
            if span.text not in embedding_text:
                raise ValueError("embedding template must preserve original chunk text")
            chunk_id, evidence_id, embedding_id = uuid4(), uuid4(), uuid4()
            existing = connection.execute(select(tables.chunks.c.chunk_id).where(
                tables.chunks.c.document_version_id == version_id, tables.chunks.c.char_start == span.char_start,
                tables.chunks.c.char_end == span.char_end, tables.chunks.c.chunker_hash == chunker_hash)).scalar_one_or_none()
            if existing:
                chunk_id = existing
            else:
                connection.execute(insert(tables.chunks).values(chunk_id=chunk_id, document_version_id=version_id,
                    scope_id=version["scope_id"], char_start=span.char_start, char_end=span.char_end,
                    literal_text=span.text, title=version["title"], heading_path=span.heading_path,
                    language=version["language"], chunker_hash=chunker_hash))
                connection.execute(pg_insert(tables.spans).values(evidence_id=evidence_id, document_version_id=version_id,
                    scope_id=version["scope_id"], char_start=span.char_start, char_end=span.char_end, literal_text=span.text,
                    heading_path=span.heading_path, page=span.page, extraction_method="normalized-text")
                    .on_conflict_do_nothing(index_elements=["document_version_id", "char_start", "char_end"]))
                evidence_id = connection.execute(select(tables.spans.c.evidence_id).where(
                    tables.spans.c.document_version_id == version_id, tables.spans.c.char_start == span.char_start,
                    tables.spans.c.char_end == span.char_end)).scalar_one()
                connection.execute(insert(tables.chunk_evidence).values(chunk_id=chunk_id, evidence_id=evidence_id))
            connection.execute(pg_insert(tables.embeddings).values(embedding_id=embedding_id, chunk_id=chunk_id,
                config_id=config_id, input_hash=content_hash(embedding_text.encode()), input_text=embedding_text, vector=vector)
                .on_conflict_do_nothing(index_elements=["chunk_id", "config_id", "input_hash"]))
            for language_config in {LANGUAGE_CONFIGS.get(version["language"], "simple"), "simple"}:
                connection.execute(text("""
                    INSERT INTO retrieval.search_documents(projection_id, chunk_id, search_config_hash, language_config, terms)
                    VALUES (:id,:chunk,:hash,CAST(:language AS text),
                      setweight(to_tsvector(CAST(CAST(:language AS text) AS regconfig),:title),'A') ||
                      setweight(to_tsvector(CAST(CAST(:language AS text) AS regconfig),:heading),'B') ||
                      setweight(to_tsvector(CAST(CAST(:language AS text) AS regconfig),:body),'D'))
                    ON CONFLICT(chunk_id, search_config_hash, language_config) DO NOTHING
                """), {"id": uuid4(), "chunk": chunk_id, "hash": configuration_hash({"lexical": "v1-A-B-D"}),
                        "language": language_config, "title": version["title"],
                        "heading": " / ".join(span.heading_path), "body": span.text})
            return chunk_id

    def get_evidence(self, access, snapshot_id, evidence_ids):
        with transaction(self.engine, access) as connection:
            statement = select(tables.spans).select_from(tables.spans.join(tables.snapshot_documents,
                tables.snapshot_documents.c.document_version_id == tables.spans.c.document_version_id).join(tables.snapshots)).where(
                tables.snapshot_documents.c.snapshot_id == snapshot_id, tables.spans.c.evidence_id.in_(evidence_ids),
                tables.snapshots.c.status.in_(["published", "live"]), tables.snapshots.c.namespace == access.namespace)
            rows = connection.execute(statement).mappings().all()
            for row in rows:
                require_scope(connection, row["scope_id"])
            if len(rows) != len(set(evidence_ids)):
                raise PermissionError("evidence is unavailable in the pinned snapshot")
            return [dict(row) for row in rows]
