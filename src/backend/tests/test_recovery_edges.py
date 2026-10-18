from concurrent.futures import ThreadPoolExecutor
from uuid import UUID

import pytest
from sqlalchemy import select, text

from backend.data import schema as tables
from backend.data.admin import revoke_scope
from backend.data.repositories.jobs import JobRepository
from backend.data.repositories.snapshots import SnapshotRepository
from backend.data.retrieval.hybrid import HybridSearch
from backend.data.fixtures import FixtureEmbedder
from backend.tests.test_database import context, make_run, plan_for


pytestmark = pytest.mark.integration


def test_expired_worker_cannot_overwrite_reclaimed_stage(database, corpus):
    fixture, _ = corpus
    access = context(fixture)
    _, _, _, run_id, _ = make_run(database, fixture)
    jobs = JobRepository(database)
    attempt = jobs.enqueue_stage(access, run_id, "retrieval", "input", "config")
    jobs.claim(access, "old")
    with database.begin() as connection:
        connection.execute(text("UPDATE ops.stage_attempts SET lease_until=now()-interval '1 second' WHERE attempt_id=:id"), {"id": attempt})
    assert jobs.claim(access, "replacement")["attempt_id"] == attempt
    with pytest.raises(ValueError, match="lease"):
        jobs.complete(access, attempt, "old", {"wrong": True})
    jobs.complete(access, attempt, "replacement", {"correct": True})
    with pytest.raises(ValueError, match="output changed"):
        jobs.complete(access, attempt, "old", {"wrong": True})


def test_competing_publishers_cannot_silently_replace_each_other(database, corpus):
    fixture, _ = corpus
    access = context(fixture)
    repository = SnapshotRepository(database)
    with database.connect() as connection:
        build = connection.execute(select(tables.builds).join(tables.snapshots).where(
            tables.snapshots.c.snapshot_id == UUID(fixture["snapshot_id"]))).mappings().one()
    snapshots = [repository.stage(access, profile_id=UUID(fixture["profile_id"]), taxonomy_version_id=UUID(fixture["taxonomy_version_id"]),
        config_id=build["config_id"], chunk_ids=[UUID(value) for value in fixture["chunk_ids"]], chunker_hash=build["chunker_hash"]) for _ in range(2)]
    def publish(snapshot):
        try:
            repository.publish(access, snapshot, expected_active=UUID(fixture["snapshot_id"]))
            return "published"
        except ValueError:
            return "conflict"
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(publish, snapshots)) == ["conflict", "published"]


def test_revocation_blocks_legacy_result_and_prevents_new_approval(database, corpus):
    fixture, artifacts = corpus
    access = context(fixture)
    repository, case_id, _, run_id, _ = make_run(database, fixture)
    hit = HybridSearch(database, FixtureEmbedder()).search(access, plan_for(database, fixture)).hits[0]
    pack = repository.freeze_pack(access, run_id, {"synthetic": True}, hit.evidence_ids)
    result = repository.record_result(access, case_id, pack, {"text": "Synthetic output"}, expected_revision=0)
    result_hash = repository.read_result(access, result)["result_hash"]
    with pytest.raises(ValueError, match="legacy"):
        repository.review(access, result, expected_hash=result_hash, decision="accepted")
    revoke_scope(database, UUID(fixture["scope_id"]))
    with pytest.raises(PermissionError):
        repository.read_result(access, result)


def test_supported_claims_and_new_embedding_templates_keep_original_chunks(database, corpus):
    from backend.contracts.data import Span
    from backend.data.fixtures import FIXTURE_MODEL
    from backend.data.repositories.corpus import CorpusRepository
    from backend.data.repositories.catalog import CatalogRepository

    fixture, artifacts = corpus
    access = context(fixture)
    repository = CorpusRepository(database, artifacts)
    hit = HybridSearch(database, FixtureEmbedder()).search(access, plan_for(database, fixture)).hits[0]
    scope_id = UUID(fixture["scope_id"])
    entity_id = repository.record_entity(access, scope_id=scope_id, entity_type="unit", display_label="Synthetic test unit")
    claim_id = repository.record_claim(access, scope_id=scope_id, subject_id=entity_id, predicate="capability",
        evidence_ids=hit.evidence_ids, typed_literal={"type": "text", "value": "synthetic example only"}, accepted=True)
    with database.connect() as connection:
        build = connection.execute(select(tables.builds).join(tables.snapshots).where(
            tables.snapshots.c.snapshot_id == UUID(fixture["snapshot_id"]))).mappings().one()
        original = connection.execute(select(tables.chunks).where(tables.chunks.c.chunk_id == hit.chunk_id)).mappings().one()
    snapshots = SnapshotRepository(database)
    staged = snapshots.stage(access, profile_id=UUID(fixture["profile_id"]), taxonomy_version_id=UUID(fixture["taxonomy_version_id"]),
        config_id=build["config_id"], chunk_ids=[UUID(value) for value in fixture["chunk_ids"]],
        chunker_hash=build["chunker_hash"], entity_ids=[entity_id], claim_ids=[claim_id])
    snapshots.publish(access, staged, expected_active=UUID(fixture["snapshot_id"]))
    resolved = CatalogRepository(database).get_entity(access, entity_id, staged)
    assert resolved["claims"][0]["claim_id"] == claim_id
    changed_config = repository.register_embedding(access, FIXTURE_MODEL.model_copy(update={
        "revision": "2", "document_template": "document: {text}"}))
    chunk_id = repository.stage_chunk(access, version_id=hit.document_version_id,
        span=Span(char_start=hit.char_start, char_end=hit.char_end, text=hit.text),
        chunker_hash=build["chunker_hash"], config_id=changed_config, vector=[1, .1, .1])
    assert chunk_id == hit.chunk_id
    with database.connect() as connection:
        input_text = connection.execute(select(tables.embeddings.c.input_text).where(
            tables.embeddings.c.chunk_id == chunk_id, tables.embeddings.c.config_id == changed_config)).scalar_one()
    assert input_text == "document: " + original["literal_text"]
