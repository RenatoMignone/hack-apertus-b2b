from concurrent.futures import ThreadPoolExecutor
from uuid import UUID, uuid4

import psycopg
from psycopg import sql
import pytest
from sqlalchemy import insert, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError

from backend.contracts.data import AccessContext
from backend.data import schema as tables
from backend.data.admin import grant_scope, provision_principal
from backend.data.database import engine_for, transaction
from backend.data.fixtures import FixtureEmbedder
from backend.data.repositories.cases import CaseRepository
from backend.data.repositories.corpus import CorpusRepository
from backend.data.repositories.jobs import JobRepository
from backend.data.retrieval.hybrid import HybridSearch
from backend.tests.test_database import context, make_run, plan_for
from backend.workflows.checkpoints import CheckpointPort


pytestmark = pytest.mark.integration


def test_four_developer_roles_concurrent_and_rls(database, corpus):
    fixture, _ = corpus
    roles, engines = [], []
    try:
        accesses = []
        for index in range(4):
            role = "test_dev_" + uuid4().hex[:12]
            principal_id, password = provision_principal(database, role, fixture["namespace"])
            roles.append(role)
            grant_scope(database, principal_id, UUID(fixture["scope_id"]))
            engine = engine_for(database.url.set(username=role, password=password).render_as_string(hide_password=False))
            engines.append(engine)
            accesses.append(AccessContext(principal_id=principal_id, namespace=fixture["namespace"]))
        def search(index):
            return HybridSearch(engines[index], FixtureEmbedder()).search(accesses[index], plan_for(database, fixture))
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(search, range(4)))
        assert all(len(result.hits) == 4 for result in results)
        case_id, _ = CaseRepository(engines[0]).create(accesses[0], "Permitted public need")
        with transaction(engines[1], accesses[1]) as connection:
            assert not connection.execute(select(tables.cases).where(tables.cases.c.case_id == case_id)).first()
        with pytest.raises(PermissionError):
            with transaction(engines[0], accesses[1]):
                pass
        with engines[0].connect() as connection:
            assert not connection.execute(select(tables.chunks)).first()
        with pytest.raises(DBAPIError):
            with engines[0].begin() as connection:
                connection.execute(text("CREATE TABLE public.forbidden(id integer)"))
    finally:
        for engine in engines:
            engine.dispose()
        for role in roles:
            with database.begin() as connection:
                connection.connection.driver_connection.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
                connection.connection.driver_connection.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


def test_checkpoint_restart_after_business_commit(database, corpus):
    fixture, _ = corpus
    access = context(fixture)
    _, _, _, run_id, _ = make_run(database, fixture)
    jobs = JobRepository(database)
    attempt_id = jobs.enqueue_stage(access, run_id, "retrieval", "input", "config")
    jobs.claim(access, "worker")
    jobs.complete(access, attempt_id, "worker", {"evidence_count": 4})
    name = "navigator_test_graph_" + uuid4().hex
    url = database.url.set(database="postgres").render_as_string(hide_password=False).replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(url, autocommit=True) as connection:
        connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    checkpoint_url = make_url(url).set(database=name).render_as_string(hide_password=False)
    try:
        from langgraph.checkpoint.base import empty_checkpoint
        port = CheckpointPort(database, checkpoint_url)
        port.setup()
        with port.for_run(access, run_id) as bound:
            assert bound.get() is None
            checkpoint = empty_checkpoint()
            checkpoint["channel_values"] = {"attempt_id": str(attempt_id)}
            bound.put(checkpoint, {"source": "update", "step": 0, "parents": {}}, {})
        restarted = CheckpointPort(database, checkpoint_url)
        with restarted.for_run(access, run_id) as bound:
            assert bound.get().checkpoint["channel_values"]["attempt_id"] == str(attempt_id)
        assert jobs.committed(access, attempt_id) == {"evidence_count": 4}
    finally:
        with psycopg.connect(url, autocommit=True) as connection:
            connection.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))


def test_claim_support_and_dimension_constraints(database, corpus):
    fixture, _ = corpus
    with database.connect() as connection:
        chunk = connection.execute(select(tables.chunks).where(tables.chunks.c.chunk_id == UUID(fixture["chunk_ids"][0]))).mappings().one()
        config_id = connection.execute(select(tables.embeddings.c.config_id).where(tables.embeddings.c.chunk_id == chunk["chunk_id"])).scalar_one()
    with pytest.raises(DBAPIError):
        with database.begin() as connection:
            connection.execute(insert(tables.embeddings).values(embedding_id=uuid4(), chunk_id=chunk["chunk_id"], config_id=config_id,
                input_hash="wrong", vector=[1, 0]))
    with pytest.raises(DBAPIError):
        with database.begin() as connection:
            entity_id = uuid4()
            connection.execute(insert(tables.entities).values(entity_id=entity_id, scope_id=chunk["scope_id"],
                entity_type="unit", display_label="Synthetic unit"))
            connection.execute(insert(tables.claims).values(claim_id=uuid4(), scope_id=chunk["scope_id"], subject_id=entity_id,
                predicate="capability", typed_literal={"type": "text", "value": "synthetic"}, status="accepted"))
