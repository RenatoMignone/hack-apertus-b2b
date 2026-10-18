"""Real PostgreSQL checkpoints across worker instances and execution safety."""
from dataclasses import replace
from uuid import UUID, uuid4

import psycopg
from psycopg import sql
import pytest
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from backend.application.worker import Worker

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_postgres_checkpoint_clarification_survives_worker_restart(harness):
    h = harness
    name = "navigator_runtime_graph_" + uuid4().hex
    admin_url = h.store.engine.url.set(database="postgres").render_as_string(hide_password=False).replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(admin_url, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    checkpoint_url = h.store.engine.url.set(database=name).render_as_string(hide_password=False).replace("postgresql+psycopg://", "postgresql://")
    try:
        async with AsyncPostgresSaver.from_conn_string(checkpoint_url) as saver:
            await saver.setup()
        h.store.settings = replace(h.settings, langgraph_database_url=checkpoint_url)
        h.reasoning.block = True
        case = h.store.create(h.access, "new", {"prompt": "Research context requiring clarification"}, "req")
        await Worker(h.application).run_once(h.access)
        state = h.store.run_view(h.access, UUID(case["case_id"]), UUID(case["run_id"]))
        assert state["state"] == "needs_clarification", state
        h.store.answer(h.access, "answer", UUID(case["case_id"]), UUID(case["run_id"]), {
            "question_id": state["questions"][0]["id"], "input_id": case["input_id"], "answer": "Glucose sensing"})
        await Worker(h.application).run_once(h.access)
        state = h.store.run_view(h.access, UUID(case["case_id"]), UUID(case["run_id"]))
        assert state["state"] == "completed", state
        assert h.reasoning.calls["interpret"] == 2
    finally:
        with psycopg.connect(admin_url, autocommit=True) as admin:
            admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))


async def test_deadline_stops_uncommitted_work(harness):
    h = harness
    h.store.settings = replace(h.settings, deadline_seconds=1)
    h.backbone.delay = 5
    case = h.store.create(h.access, "new", {"prompt": "Public research capability"}, "req")
    await h.worker.run_once(h.access)
    state = h.store.run_view(h.access, UUID(case["case_id"]), UUID(case["run_id"]))
    assert state["state"] == "failed" and state["error_code"] == "budget_exceeded"
    assert not h.reasoning.calls["extract"]


async def test_only_one_worker_can_claim_a_job(harness):
    import asyncio
    h = harness
    h.store.create(h.access, "new", {"prompt": "Public research capability"}, "req")
    a, b = await asyncio.gather(h.worker.run_once(h.access), Worker(h.application, checkpoint_factory=h.checkpoint).run_once(h.access))
    assert sum([a, b]) == 1
    assert h.reasoning.calls["draft"] == 1


async def test_stale_answers_fail_without_creating_a_new_job(harness):
    from backend.contracts.services import StaleRevision
    h = harness
    h.reasoning.block = True
    case = h.store.create(h.access, "new", {"prompt": "Public research capability"}, "req")
    await h.worker.run_once(h.access)
    state = h.store.run_view(h.access, UUID(case["case_id"]), UUID(case["run_id"]))
    h.store.edit(h.access, "focus", UUID(case["case_id"]), {"text": "A different objective",
        "kind": "focus", "expected_revision": 0}, "req")
    with pytest.raises(StaleRevision):
        h.store.answer(h.access, "answer", UUID(case["case_id"]), UUID(case["run_id"]), {
            "question_id": state["questions"][0]["id"], "input_id": case["input_id"], "answer": "Glucose"})


async def test_model_configuration_cannot_switch_under_a_queued_run(harness):
    h = harness
    case = h.store.create(h.access, "new", {"prompt": "Public research capability"}, "req")
    h.store.settings = replace(h.settings, llm_name="apertus-v1-5-70b")
    await h.worker.run_once(h.access)
    view = h.store.run_view(h.access, UUID(case["case_id"]), UUID(case["run_id"]))
    assert view["state"] == "failed" and view["error_code"] == "service_unavailable"
    assert not h.reasoning.calls
