from concurrent.futures import ThreadPoolExecutor
from uuid import UUID, uuid4

import pytest
from sqlalchemy import insert, select, text, update
from sqlalchemy.exc import DBAPIError

from backend.contracts.data import AccessContext, QueryPlan
from backend.data import schema as tables
from backend.data.admin import revoke_scope
from backend.data.database import check_schema, migrate, transaction
from backend.data.fixtures import FIXTURE_MODEL, FixtureEmbedder
from backend.data.repositories.cases import CaseRepository
from backend.data.repositories.corpus import CorpusRepository
from backend.data.repositories.jobs import JobRepository
from backend.data.repositories.snapshots import SnapshotRepository
from backend.data.retrieval.hybrid import HybridSearch


pytestmark = pytest.mark.integration


def context(fixture):
    return AccessContext(principal_id=fixture["principal_id"], namespace=fixture["namespace"])


def plan_for(database, fixture, query="glucose monitoring", **changes):
    snapshot = SnapshotRepository(database).get(context(fixture), profile_id=UUID(fixture["profile_id"]))
    return QueryPlan(original_request=query, snapshot_id=fixture["snapshot_id"], profile_id=fixture["profile_id"],
        taxonomy_version_id=fixture["taxonomy_version_id"], build_id=snapshot["build_id"],
        embedding_config_hash=fixture["embedding_config_hash"], **changes)


def make_run(database, fixture):
    repository = CaseRepository(database)
    access = context(fixture)
    case_id, input_id = repository.create(access, "Public synthetic glucose-monitoring need")
    run_id, thread_id = repository.start_run(access, case_id, input_id, UUID(fixture["snapshot_id"]), {})
    return repository, case_id, input_id, run_id, thread_id


def test_migration_is_repeatable_and_schema_is_checked(database):
    migrate(database)
    check_schema(database)
    with database.connect() as connection:
        assert connection.execute(text("SELECT extversion FROM pg_extension WHERE extname='vector'")).scalar_one()
        assert len(tables.metadata.tables) == 63


def test_hybrid_multilingual_and_semantic_branch(database, corpus):
    fixture, artifacts = corpus
    result = HybridSearch(database, FixtureEmbedder()).search(context(fixture), plan_for(database, fixture, "unseen wording"))
    assert len(result.hits) == 4
    assert all(hit.lexical_rank is None and hit.vector_rank for hit in result.hits)
    assert {hit.language for hit in result.hits} == {"en", "de", "fr", "it"}
    german = HybridSearch(database, FixtureEmbedder()).search(context(fixture), plan_for(database, fixture, "Glukose", languages=["de"]))
    assert len(german.hits) == 1
    assert german.hits[0].lexical_rank == 1
    rows = CorpusRepository(database, artifacts).get_evidence(context(fixture), UUID(fixture["snapshot_id"]), german.hits[0].evidence_ids)
    assert rows[0]["literal_text"] == german.hits[0].text


def test_embedding_space_and_reranker_validation(database, corpus):
    fixture, _ = corpus
    plan = plan_for(database, fixture)
    with pytest.raises(ValueError, match="incompatible"):
        HybridSearch(database, FixtureEmbedder()).search(context(fixture), plan.model_copy(update={"embedding_config_hash": "other"}))
    class InvalidReranker:
        def score(self, query, passages):
            return [float("nan")] * len(passages)
    with pytest.raises(ValueError, match="reranker"):
        HybridSearch(database, FixtureEmbedder(), InvalidReranker()).search(context(fixture), plan)


def test_authentication_scope_isolation_and_revocation(database, corpus):
    fixture, _ = corpus
    access = context(fixture)
    with pytest.raises(PermissionError):
        HybridSearch(database, FixtureEmbedder()).search(access.model_copy(update={"principal_id": uuid4()}), plan_for(database, fixture))
    revoke_scope(database, UUID(fixture["scope_id"]))
    result = HybridSearch(database, FixtureEmbedder()).search(access, plan_for(database, fixture))
    assert not result.hits


def test_database_enforces_literal_scope_and_immutability(database, corpus):
    fixture, _ = corpus
    with database.connect() as connection:
        chunk = connection.execute(select(tables.chunks).where(tables.chunks.c.chunk_id == UUID(fixture["chunk_ids"][0]))).mappings().one()
    with pytest.raises(DBAPIError):
        with database.begin() as connection:
            connection.execute(update(tables.chunks).where(tables.chunks.c.chunk_id == chunk["chunk_id"]).values(literal_text="rewritten"))
    with pytest.raises(DBAPIError):
        with database.begin() as connection:
            connection.execute(insert(tables.spans).values(evidence_id=uuid4(), document_version_id=chunk["document_version_id"],
                scope_id=chunk["scope_id"], char_start=1, char_end=3, literal_text="wrong", extraction_method="test"))
    with pytest.raises(DBAPIError):
        with database.begin() as connection:
            connection.execute(insert(tables.snapshot_documents).values(snapshot_id=UUID(fixture["snapshot_id"]), document_version_id=chunk["document_version_id"]))


def test_failed_publication_preserves_active_and_test_model_gate(database, corpus):
    fixture, _ = corpus
    access = context(fixture)
    with transaction(database, access) as connection:
        build = connection.execute(select(tables.builds).join(tables.snapshots).where(
            tables.snapshots.c.snapshot_id == UUID(fixture["snapshot_id"]))).mappings().one()
    snapshots = SnapshotRepository(database)
    staged = snapshots.stage(access, profile_id=UUID(fixture["profile_id"]), taxonomy_version_id=UUID(fixture["taxonomy_version_id"]),
        config_id=build["config_id"], chunk_ids=[UUID(fixture["chunk_ids"][0])], chunker_hash=build["chunker_hash"])
    with pytest.raises(ValueError, match="active snapshot changed"):
        snapshots.publish(access, staged)
    with pytest.raises(ValueError, match="coverage"):
        snapshots.publish(access, staged, expected_active=UUID(fixture["snapshot_id"]))
    assert snapshots.get(access, profile_id=UUID(fixture["profile_id"]))["snapshot_id"] == UUID(fixture["snapshot_id"])
    assert FIXTURE_MODEL.test_only


def test_case_edit_clarification_and_frozen_pack(database, corpus):
    fixture, _ = corpus
    access = context(fixture)
    repository, case_id, _, run_id, thread_id = make_run(database, fixture)
    question = repository.ask(access, run_id, field="need", reason="Which public capability?")
    assert repository.answer(access, question, "Sensors") == thread_id
    with pytest.raises(ValueError):
        repository.answer(access, question, "Again")
    hit = HybridSearch(database, FixtureEmbedder()).search(access, plan_for(database, fixture)).hits[0]
    pack = repository.freeze_pack(access, run_id, {"facts": "synthetic"}, hit.evidence_ids)
    result = repository.record_result(access, case_id, pack, {"brief": "synthetic"}, expected_revision=0)
    formatting = repository.edit(access, case_id, expected_revision=1, instruction="Shorten it", kind="formatting")
    assert formatting["reusable_pack_id"] == pack
    assert not formatting["requires_retrieval"]
    repository.record_result(access, case_id, pack, {"brief": "short"}, expected_revision=2, parent_id=result)
    focus = repository.edit(access, case_id, expected_revision=3, instruction="Focus on digital tools", kind="focus")
    assert focus["requires_retrieval"]
    with pytest.raises(ValueError):
        repository.record_result(access, case_id, pack, {}, expected_revision=4)


def test_stage_outbox_recovery_and_worker_leases(database, corpus):
    fixture, _ = corpus
    access = context(fixture)
    _, _, _, run_id, _ = make_run(database, fixture)
    jobs = JobRepository(database)
    attempt_id = jobs.enqueue_stage(access, run_id, "retrieval", "input", "config")
    assert attempt_id == jobs.enqueue_stage(access, run_id, "retrieval", "input", "config")
    with ThreadPoolExecutor(max_workers=2) as pool:
        claims = list(pool.map(lambda worker: jobs.claim(access, worker), ["one", "two"]))
    assert sum(claim is not None for claim in claims) == 1
    owner = next(claim["worker_id"] for claim in claims if claim)
    with pytest.raises(ValueError):
        jobs.complete(access, attempt_id, "stranger", {"hits": 4})
    assert jobs.complete(access, attempt_id, owner, {"hits": 4}) == {"hits": 4}
    assert jobs.committed(access, attempt_id) == {"hits": 4}
    assert jobs.complete(access, attempt_id, owner, {"hits": 4}) == {"hits": 4}
    with database.connect() as connection:
        count = connection.execute(text("SELECT count(*) FROM ops.outbox WHERE idempotency_key=:key"),
            {"key": f"stage:{attempt_id}"}).scalar_one()
    assert count == 1


def test_cancel_prevents_late_stage_commit(database, corpus):
    fixture, _ = corpus
    access = context(fixture)
    repository, _, _, run_id, _ = make_run(database, fixture)
    jobs = JobRepository(database)
    attempt = jobs.enqueue_stage(access, run_id, "retrieval", "input", "config")
    jobs.claim(access, "worker")
    repository.cancel(access, run_id)
    with pytest.raises(ValueError, match="cancelled"):
        jobs.complete(access, attempt, "worker", {})
