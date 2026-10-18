from uuid import uuid4

from sqlalchemy import insert, select, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from backend.contracts.data import configuration_hash
from backend.data import schema as tables
from backend.data.database import require_scope, transaction


class SnapshotRepository:
    def __init__(self, engine):
        self.engine = engine

    def stage(self, access, *, profile_id, taxonomy_version_id, config_id, chunk_ids, chunker_hash,
              entity_ids=(), claim_ids=()):
        if not chunk_ids or len(set(chunk_ids)) != len(chunk_ids):
            raise ValueError("snapshot needs unique chunk membership")
        with transaction(self.engine, access) as connection:
            profile = connection.execute(select(tables.profiles).where(tables.profiles.c.profile_id == profile_id)).mappings().one()
            if profile["namespace"] != access.namespace:
                raise PermissionError("profile namespace mismatch")
            taxonomy = connection.execute(select(tables.taxonomies).where(
                tables.taxonomies.c.taxonomy_version_id == taxonomy_version_id)).mappings().one()
            if taxonomy["status"] != "reviewed":
                raise ValueError("snapshot requires a reviewed pinned taxonomy")
            build_id, snapshot_id = uuid4(), uuid4()
            search_hash = configuration_hash({"lexical": "v1-A-B-D"})
            members = connection.execute(select(tables.chunks, tables.embeddings.c.embedding_id).join(
                tables.embeddings, tables.embeddings.c.chunk_id == tables.chunks.c.chunk_id).where(
                tables.chunks.c.chunk_id.in_(chunk_ids), tables.embeddings.c.config_id == config_id)).mappings().all()
            if len(members) != len(chunk_ids):
                raise ValueError("every member requires exactly one compatible embedding")
            for member in members:
                require_scope(connection, member["scope_id"], write=True)
                if connection.execute(select(tables.scopes.c.kind).where(
                        tables.scopes.c.scope_id == member["scope_id"])).scalar_one() != "public":
                    raise ValueError("case-scoped evidence cannot be published to the shared corpus")
                if member["chunker_hash"] != chunker_hash:
                    raise ValueError("chunker configuration mismatch")
            manifest = {"chunks": sorted(str(member["chunk_id"]) for member in members),
                        "documents": sorted({str(member["document_version_id"]) for member in members}),
                        "entities": sorted(str(entity_id) for entity_id in set(entity_ids)),
                        "claims": sorted(str(claim_id) for claim_id in set(claim_ids))}
            connection.execute(insert(tables.builds).values(build_id=build_id, config_id=config_id, namespace=access.namespace,
                chunker_hash=chunker_hash, search_config_hash=search_hash))
            connection.execute(insert(tables.snapshots).values(snapshot_id=snapshot_id, profile_id=profile_id,
                taxonomy_version_id=taxonomy_version_id, build_id=build_id, namespace=access.namespace, schema_version="1.0",
                manifest=manifest, manifest_hash=configuration_hash(manifest)))
            for version_id in {member["document_version_id"] for member in members}:
                connection.execute(insert(tables.snapshot_documents).values(snapshot_id=snapshot_id, document_version_id=version_id))
            for member in members:
                connection.execute(insert(tables.snapshot_chunks).values(snapshot_id=snapshot_id,
                    chunk_id=member["chunk_id"], embedding_id=member["embedding_id"]))
            for entity_id in set(entity_ids):
                entity = connection.execute(select(tables.entities).where(tables.entities.c.entity_id == entity_id)).mappings().one()
                require_scope(connection, entity["scope_id"], write=True)
                connection.execute(insert(tables.snapshot_entities).values(snapshot_id=snapshot_id, entity_id=entity_id))
            for claim_id in set(claim_ids):
                claim = connection.execute(select(tables.claims).where(tables.claims.c.claim_id == claim_id)).mappings().one()
                require_scope(connection, claim["scope_id"], write=True)
                support = connection.execute(select(tables.spans.c.document_version_id).join(tables.claim_evidence).where(
                    tables.claim_evidence.c.claim_id == claim_id, tables.claim_evidence.c.relation == "supports",
                    tables.claim_evidence.c.review_decision == "accepted")).scalars().all()
                if (claim["status"] != "accepted" or claim["subject_id"] not in entity_ids or not support
                        or not set(support) <= {member["document_version_id"] for member in members}
                        or (claim["object_entity_id"] is not None and claim["object_entity_id"] not in entity_ids)):
                    raise ValueError("pinned claims require complete accepted support and pinned subject/object entities")
                connection.execute(insert(tables.snapshot_claims).values(snapshot_id=snapshot_id, claim_id=claim_id))
            return snapshot_id

    def publish(self, access, snapshot_id, *, expected_active=None):
        with transaction(self.engine, access) as connection:
            snapshot = connection.execute(select(tables.snapshots).where(
                tables.snapshots.c.snapshot_id == snapshot_id).with_for_update()).mappings().one()
            if snapshot["namespace"] != access.namespace or snapshot["status"] != "draft":
                raise ValueError("only draft snapshots in this namespace can be published")
            connection.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:profile,0))"),
                               {"profile": str(snapshot["profile_id"])})
            active = connection.execute(select(tables.active_snapshots.c.snapshot_id).where(
                tables.active_snapshots.c.profile_id == snapshot["profile_id"])).scalar_one_or_none()
            if active != expected_active:
                raise ValueError("active snapshot changed; rebase publication explicitly")
            model = connection.execute(select(tables.models.c.verified, tables.models.c.test_only).select_from(
                tables.builds.join(tables.embedding_configs).join(tables.models)).where(
                tables.builds.c.build_id == snapshot["build_id"])).mappings().one()
            if not model["verified"] or (model["test_only"] and not access.namespace.startswith(("test", "fixture"))):
                raise ValueError("unresolved or test model cannot be published to this profile")
            members = connection.execute(select(tables.chunks, tables.versions.c.status.label("version_status"),
                tables.documents.c.source_id).select_from(tables.snapshot_chunks.join(tables.chunks).join(
                    tables.versions).join(tables.documents)).where(
                tables.snapshot_chunks.c.snapshot_id == snapshot_id)).mappings().all()
            if not members:
                raise ValueError("empty snapshot")
            for member in members:
                require_scope(connection, member["scope_id"], write=True)
                if member["version_status"] != "accepted":
                    raise ValueError("snapshot contains unaccepted content")
            profile = connection.execute(select(tables.profiles).where(
                tables.profiles.c.profile_id == snapshot["profile_id"])).mappings().one()
            found_families = set(connection.execute(select(tables.families.c.name).join(tables.family_memberships).where(
                tables.family_memberships.c.source_id.in_([member["source_id"] for member in members]))).scalars())
            required_families = set(profile["configuration"].get("required_source_families", ["UniBE", "ARTORG", "DCB"]))
            if not required_families.issubset(found_families):
                raise ValueError("required source-family coverage is incomplete")
            missing_projection = connection.execute(text("""
                SELECT count(*) FROM retrieval.snapshot_chunks sc JOIN corpus.snapshots s USING(snapshot_id)
                JOIN retrieval.index_builds b ON b.build_id=s.build_id
                WHERE sc.snapshot_id=:snapshot AND NOT EXISTS (
                  SELECT 1 FROM retrieval.search_documents d
                  WHERE d.chunk_id=sc.chunk_id AND d.search_config_hash=b.search_config_hash)
            """), {"snapshot": snapshot_id}).scalar_one()
            if missing_projection:
                raise ValueError("lexical projection is incomplete")
            for validator in ("integrity", "coverage"):
                connection.execute(insert(tables.checks).values(check_id=uuid4(), snapshot_id=snapshot_id,
                    validator=validator, version="1", passed=True, manifest_hash=snapshot["manifest_hash"]))
            connection.execute(update(tables.builds).where(tables.builds.c.build_id == snapshot["build_id"]).values(status="published"))
            connection.execute(update(tables.snapshots).where(tables.snapshots.c.snapshot_id == snapshot_id).values(
                status="published", published_at=text("now()")))
            connection.execute(pg_insert(tables.active_snapshots).values(profile_id=snapshot["profile_id"], snapshot_id=snapshot_id)
                .on_conflict_do_update(index_elements=["profile_id"], set_={"snapshot_id": snapshot_id}))
            connection.execute(insert(tables.outbox).values(event_id=uuid4(), namespace=access.namespace,
                idempotency_key=f"snapshot:{snapshot_id}", event_type="snapshot.published", payload={"snapshot_id": str(snapshot_id)}))

    def get(self, access, *, profile_id, snapshot_id=None):
        with transaction(self.engine, access) as connection:
            if snapshot_id is None:
                snapshot_id = connection.execute(select(tables.active_snapshots.c.snapshot_id).where(
                    tables.active_snapshots.c.profile_id == profile_id)).scalar_one()
            snapshot = connection.execute(select(tables.snapshots).where(tables.snapshots.c.snapshot_id == snapshot_id,
                tables.snapshots.c.profile_id == profile_id, tables.snapshots.c.status == "published")).mappings().one()
            if snapshot["namespace"] != access.namespace:
                raise PermissionError("snapshot namespace mismatch")
            return dict(snapshot)
