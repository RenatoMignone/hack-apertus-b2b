"""Live ingestion isolation, compatibility, owner boundaries and stable reruns."""
from dataclasses import replace
from uuid import UUID, uuid4

import pytest
from psycopg import sql
from sqlalchemy import delete, insert, select, text, update
from sqlalchemy.exc import DBAPIError, NoResultFound

from backend.application.persistence.store import RuntimeStore
from backend.contracts.data import AccessContext, QueryPlan, Span
from backend.data import schema as t
from backend.data.admin import configure_runtime_access, grant_scope, provision_principal
from backend.data.database import engine_for, transaction
from backend.data.fixtures import FIXTURE_MODEL, FixtureEmbedder
from backend.data.repositories.corpus import CorpusRepository
from backend.data.retrieval.hybrid import HybridSearch

pytestmark = pytest.mark.integration


@pytest.fixture
def live_users(harness, tmp_path):
    h = harness
    configuration = tmp_path / "synthetic-embedding.json"
    configuration.write_text(FIXTURE_MODEL.model_dump_json(), encoding="utf-8")
    settings = replace(h.settings, corpus_mode="live", embedding_configuration=str(configuration),
        live_taxonomy_version_id=UUID(h.fixture["taxonomy_version_id"]))
    users, roles = [], []
    with h.store.engine.begin() as c:
        c.execute(delete(t.active_snapshots).where(t.active_snapshots.c.profile_id == settings.default_profile_id))
    try:
        for _ in range(2):
            role = "live_test_" + uuid4().hex[:12]
            principal, password = provision_principal(h.store.engine, role, h.access.namespace)
            roles.append(role)
            grant_scope(h.store.engine, principal, UUID(h.fixture["scope_id"]))
            engine = engine_for(h.store.engine.url.set(username=role, password=password).render_as_string(hide_password=False))
            users.append((RuntimeStore(engine, settings, h.store.artifacts), AccessContext(
                principal_id=principal, namespace=h.access.namespace)))
        yield users
    finally:
        for store, _ in users:
            store.engine.dispose()
        with h.store.engine.begin() as c:
            for role in roles:
                c.connection.driver_connection.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
                c.connection.driver_connection.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


def start(store, access, key):
    result = store.create(access, key, {"prompt": "Public synthetic glucose research in Bern"}, "test")
    context = store.context(access, UUID(result["run_id"]))
    plan = QueryPlan(original_request="glucose", run_id=context.run_id, case_id=context.case_id,
        input_revision_id=context.input_id, snapshot_id=context.snapshot_id, profile_id=context.profile_id,
        taxonomy_version_id=context.taxonomy_version_id, build_id=context.build_id,
        embedding_config_hash=context.embedding_config_hash)
    return context, plan


def test_live_capture_uses_ready_chunks_and_next_run_sees_ingestion(harness, live_users):
    h = harness
    store, access = live_users[0]
    first, plan = start(store, access, "before")
    search = HybridSearch(store.engine, FixtureEmbedder())
    assert len(search.search(access, plan).hits) == 4
    with transaction(store.engine, access) as c:
        snapshot = c.execute(select(t.snapshots).where(t.snapshots.c.snapshot_id == first.snapshot_id)).mappings().one()
        assert snapshot["status"] == "live" and snapshot["published_at"] is None
        assert snapshot["manifest"]["runtime_case_id"] == str(first.case_id)
        assert not c.execute(select(t.active_snapshots).where(t.active_snapshots.c.profile_id == first.profile_id)).first()
        assert not c.execute(select(t.scope_grants)).first()  # Deliberately hidden; read permission still works.
        assert c.execute(text("SELECT ops.can_access(:scope,false)"), {"scope": UUID(h.fixture["scope_id"])}).scalar_one()
    repo = CorpusRepository(h.store.engine, h.store.artifacts)
    body = "New synthetic glucose capability committed while other cases continue."
    span = Span(char_start=0, char_end=len(body), text=body)
    with h.store.engine.begin() as c:
        source = c.execute(select(t.sources.c.source_id).where(t.sources.c.scope_id == UUID(h.fixture["scope_id"])).limit(1)).scalar_one()
        config = c.execute(select(t.embedding_configs.c.config_id).where(t.embedding_configs.c.config_hash == FIXTURE_MODEL.config_hash)).scalar_one()
    version = repo.stage_document(h.access, scope_id=UUID(h.fixture["scope_id"]), source_id=source,
        url="https://fixture.invalid/new-live-document", title="New glucose capability", language="en",
        raw=body.encode(), body=body, spans=[span], parser_hash="live-test-v1")
    incomplete, incomplete_plan = start(store, access, "text-without-vector")
    assert len(search.search(access, incomplete_plan).hits) == 4
    chunk = repo.stage_chunk(h.access, version_id=version, span=span, chunker_hash="new-chunker-v1",
        config_id=config, vector=FixtureEmbedder().embed_query(body))
    after, after_plan = start(store, access, "after")
    result = search.search(access, after_plan)
    assert chunk in {hit.chunk_id for hit in result.hits}
    assert "live_corpus_incomplete_coverage" in result.limitations
    assert first.snapshot_id != after.snapshot_id != incomplete.snapshot_id
    assert len(search.search(access, plan).hits) == 4  # Running case never changes under ingestion.
    assert len(search.search(access, incomplete_plan).hits) == 4


def test_live_owner_cannot_write_public_corpus_or_reuse_other_capture(harness, live_users):
    (store, owner), (other_store, other) = live_users
    context, plan = start(store, owner, "owner")
    other_context, other_plan = start(other_store, other, "other")
    with transaction(other_store.engine, other) as c:
        assert not c.execute(select(t.snapshots).where(t.snapshots.c.snapshot_id == context.snapshot_id)).first()
    with pytest.raises((NoResultFound, PermissionError)):
        HybridSearch(other_store.engine, FixtureEmbedder()).search(other, plan)
    with pytest.raises(PermissionError):
        HybridSearch(store.engine, FixtureEmbedder()).search(owner, plan.model_copy(update={"run_id": other_context.run_id}))
    # A mistaken writable public grant must still not turn a runtime login into an ingestor.
    grant_scope(harness.store.engine, owner.principal_id, UUID(harness.fixture["scope_id"]), write=True)
    with pytest.raises(DBAPIError):
        with transaction(store.engine, owner) as c:
            c.execute(insert(t.sources).values(source_id=uuid4(), scope_id=UUID(harness.fixture["scope_id"]),
                canonical_origin="https://forbidden.invalid", registry_ref="must-rollback"))
    with pytest.raises(DBAPIError):
        with transaction(store.engine, owner) as c:
            c.execute(update(t.snapshots).where(t.snapshots.c.snapshot_id == context.snapshot_id).values(status="published"))
    # Capture membership is immutable even to the maintainer during later ingestion.
    with pytest.raises(DBAPIError):
        with harness.store.engine.begin() as c:
            c.execute(delete(t.snapshot_chunks).where(t.snapshot_chunks.c.snapshot_id == context.snapshot_id))
    with transaction(other_store.engine, other) as c:
        assert c.execute(text("SELECT ops.ensure_case_scope(:case)"), {"case": other_context.case_id}).scalar_one()
    assert HybridSearch(other_store.engine, FixtureEmbedder()).search(other, other_plan).hits


def test_live_capture_rejects_wrong_space_ungranted_scopes_and_embedding(harness, live_users):
    store, access = live_users[0]
    with harness.store.engine.begin() as c:
        c.execute(delete(t.scope_grants).where(t.scope_grants.c.principal_id == access.principal_id))
    with pytest.raises(DBAPIError):
        start(store, access, "no-grant")
    grant_scope(harness.store.engine, access.principal_id, UUID(harness.fixture["scope_id"]))
    context, plan = start(store, access, "read-restored")
    with pytest.raises(ValueError, match="incompatible"):
        HybridSearch(store.engine, FixtureEmbedder()).search(access, plan.model_copy(update={"embedding_config_hash": "0" * 64}))
    with pytest.raises(DBAPIError):
        with transaction(store.engine, access) as c:
            c.execute(text("SELECT ops.capture_live_corpus(:case,:profile,:taxonomy,:hash)"), {
                "case": context.case_id, "profile": context.profile_id, "taxonomy": context.taxonomy_version_id,
                "hash": "0" * 64})


def test_existing_login_gets_live_namespace_without_password_rotation(harness, live_users):
    store, old_access = live_users[0]
    namespace, profile = "test_live_" + uuid4().hex[:10], uuid4()
    with harness.store.engine.begin() as c:
        old_profile = dict(c.execute(select(t.profiles).where(t.profiles.c.profile_id == store.settings.default_profile_id)).mappings().one())
        old_profile.update(profile_id=profile, namespace=namespace)
        c.execute(insert(t.profiles).values(**old_profile))
        if not c.execute(text("SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='navigator_app')")).scalar_one():
            c.execute(text("CREATE ROLE navigator_app NOLOGIN"))
        c.execute(text("GRANT INSERT ON corpus.snapshots TO navigator_app"))
        c.connection.driver_connection.execute(sql.SQL("GRANT navigator_app TO {}").format(sql.Identifier(store.engine.url.username)))
    principal = configure_runtime_access(harness.store.engine, store.engine.url.username, namespace,
        [UUID(harness.fixture["scope_id"])])
    assert principal != old_access.principal_id
    assert configure_runtime_access(harness.store.engine, store.engine.url.username, namespace,
        [UUID(harness.fixture["scope_id"])]) == principal
    access = AccessContext(principal_id=principal, namespace=namespace)
    new_store = RuntimeStore(store.engine, replace(store.settings, default_profile_id=profile), store.artifacts)
    context, plan = start(new_store, access, "new-namespace")
    assert context.access.namespace == namespace
    assert HybridSearch(store.engine, FixtureEmbedder()).search(access, plan).hits
    with transaction(store.engine, access) as c:
        assert not c.execute(text("SELECT has_table_privilege(session_user,'corpus.snapshots','INSERT')")).scalar_one()
    with transaction(store.engine, old_access) as c:
        assert c.execute(select(t.principals.c.principal_id).where(t.principals.c.principal_id == old_access.principal_id)).scalar_one()
