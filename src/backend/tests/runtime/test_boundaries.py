"""Isolation, bounded execution, durable retries and truthful failure outcomes."""
import asyncio
from dataclasses import replace
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import insert

from backend.application.adapters import Unavailable
from backend.application.worker import Worker
from backend.contracts.data import AccessContext
from backend.data import schema as t
from backend.data.repositories.cases import CaseRepository
from backend.tests.runtime.fakes import FixtureWeb

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


def new(h, prompt="Public synthetic need in Bern"):
    return h.store.create(h.access, "new", {"prompt": prompt}, "test")


async def test_auth_idempotency_and_redacted_validation(harness):
    h = harness
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=h.app), base_url="http://test") as client:
        assert (await client.get("/api/v1/cases")).status_code == 401
        assert (await client.get("/api/v1/cases", headers={"Authorization": "Bearer wrong"})).status_code == 401
        a, b = await asyncio.gather(*[client.post("/api/v1/cases", headers=h.headers,
            json={"prompt": "Public synthetic need in Bern"}) for _ in range(2)])
        assert a.status_code == b.status_code == 201
        assert a.json() == b.json()
        conflict = await client.post("/api/v1/cases", headers=h.headers, json={"prompt": "Different context"})
        assert conflict.status_code == 409
        invalid = await client.post("/api/v1/cases", headers=h.headers,
            json={"prompt": "Private text must not be echoed", "owner_id": "private-token-value"})
        assert invalid.status_code == 422
        assert "private-token-value" not in invalid.text and "Private text" not in invalid.text
        assert (await client.post("/api/v1/cases", headers={"Authorization": h.headers["Authorization"]},
            json={"prompt": "No key"})).status_code == 422
        huge = await client.post("/api/v1/cases", headers=h.headers, content=b"x" * 128001)
        assert huge.status_code == 413
        listed = await client.get("/api/v1/cases", headers=h.headers)
        assert len(listed.json()) == 1


async def test_other_owner_is_not_disclosed(harness):
    h = harness
    principal, namespace = uuid4(), "test_other_" + uuid4().hex[:12]
    with h.store.engine.begin() as c:
        c.execute(insert(t.principals).values(principal_id=principal, database_role="postgres", namespace=namespace))
    case, _ = CaseRepository(h.store.engine).create(AccessContext(principal_id=principal, namespace=namespace), "Other owner")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=h.app), base_url="http://test", headers=h.headers) as client:
        response = await client.get(f"/api/v1/cases/{case}")
        assert response.status_code == 404 and "Other owner" not in response.text


async def test_missing_adapter_is_failure_not_no_match(harness):
    h = harness
    h.services.backbone = Unavailable()
    case = new(h)
    await h.worker.run_once(h.access)
    state = h.store.run_view(h.access, UUID(case["case_id"]), UUID(case["run_id"]))
    assert state["state"] == "failed" and state["error_code"] == "service_unavailable"
    assert h.store.case_rows(h.access, UUID(case["case_id"]))[0]["results"] == []


async def test_empty_evidence_produces_honest_non_exportable_no_match(harness):
    h = harness
    h.backbone.empty = True
    h.reasoning.empty = True
    case = new(h)
    await h.worker.run_once(h.access)
    detail = await h.application.detail(h.access, UUID(case["case_id"]))
    assert detail["revisions"][0]["coverage"]["resultKind"] == "no_match"
    assert detail["revisions"][0]["reasons"] == []


async def test_semantically_rejected_draft_has_bounded_research(harness):
    h = harness
    h.reasoning.bad_draft = True
    case = new(h)
    await h.worker.run_once(h.access)
    state = h.store.run_view(h.access, UUID(case["case_id"]), UUID(case["run_id"]))
    assert state["state"] == "failed" and state["error_code"] == "evidence_rejected"
    assert h.backbone.calls["retrieve"] == h.settings.max_research_rounds
    assert h.store.case_rows(h.access, UUID(case["case_id"]))[0]["results"] == []


async def test_changed_pack_after_draft_gap_has_separate_durable_stage(harness):
    h = harness
    h.reasoning.bad_draft = True
    original = h.reasoning.propose_pack
    async def changed(*args):
        pack = await original(*args)
        return pack.model_copy(update={"gaps": [f"Synthetic research-round limitation {h.reasoning.calls['pack']}"]})
    h.reasoning.propose_pack = changed
    case = new(h)
    await h.worker.run_once(h.access)
    state = h.store.run_view(h.access, UUID(case["case_id"]), UUID(case["run_id"]))
    assert state["error_code"] == "evidence_rejected", state
    assert h.reasoning.calls["draft"] == 3


async def test_optional_real_web_tool_budget_does_not_abort_supported_database_result(harness):
    from backend.contracts.services import BudgetExceeded
    from backend.ingestion.web import PublicWebTools
    h = harness
    class Discovery:
        async def discover(self, query, limit):
            raise BudgetExceeded()
    h.services.web = PublicWebTools(discovery=Discovery())
    case = new(h)
    await h.worker.run_once(h.access)
    state = h.store.run_view(h.access, UUID(case["case_id"]), UUID(case["run_id"]))
    assert state["status"] == "succeeded", state
    assert "web_tool_budget_exhausted" in state["limitations"]


async def test_graph_runs_database_and_web_branches_concurrently(harness):
    h = harness
    h.services.web = FixtureWeb()
    db_started, web_started = asyncio.Event(), asyncio.Event()
    original = h.backbone.retrieve
    async def retrieve(plan, context):
        db_started.set()
        await asyncio.wait_for(web_started.wait(), 2)
        return await original(plan, context)
    async def discover(query, context):
        web_started.set()
        await asyncio.wait_for(db_started.wait(), 2)
        assert "Synthetic Company" not in query
        return []
    h.backbone.retrieve = retrieve
    h.services.web.discover = discover
    case = new(h)
    await h.worker.run_once(h.access)
    state = h.store.run_view(h.access, UUID(case["case_id"]), UUID(case["run_id"]))
    assert state["state"] == "completed", state
    assert h.backbone.calls["register"] == 1


async def test_offline_never_invokes_web(harness):
    h = harness
    h.store.settings = replace(h.settings, mode="offline", llm_base_url="http://127.0.0.1:8080/v1")
    h.services.web = FixtureWeb()
    case = new(h)
    await h.worker.run_once(h.access)
    assert not h.services.web.calls
    detail = await h.application.detail(h.access, UUID(case["case_id"]))
    assert any("Offline mode" in item for item in detail["revisions"][0]["coverage"]["limitations"])


async def test_cancelled_case_cannot_receive_late_results(harness):
    h = harness
    entered = asyncio.Event()
    original = h.backbone.retrieve
    async def slow(plan, context):
        entered.set()
        await asyncio.sleep(.2)
        return await original(plan, context)
    h.backbone.retrieve = slow
    case = new(h)
    running = asyncio.create_task(h.worker.run_once(h.access))
    await asyncio.wait_for(entered.wait(), 3)
    h.store.cancel(h.access, "cancel", UUID(case["case_id"]), UUID(case["run_id"]))
    await running
    rows = h.store.case_rows(h.access, UUID(case["case_id"]))[0]
    assert not rows["results"]
    assert h.store.run_view(h.access, UUID(case["case_id"]), UUID(case["run_id"]))["state"] == "cancelled"


async def test_committed_stage_reuse_survives_checkpoint_loss(harness):
    from contextlib import asynccontextmanager
    from langgraph.checkpoint.memory import InMemorySaver
    h = harness
    case = new(h)
    await h.worker.run_once(h.access)
    saved = dict(h.reasoning.calls)
    with h.store.session(h.access) as c:
        h.store.enqueue(c, h.access, UUID(case["run_id"]), "runtime.execute", {"run_id": case["run_id"]}, suffix="after-loss")
    @asynccontextmanager
    async def empty_checkpoint(access, run_id):
        yield InMemorySaver(), {"configurable": {"thread_id": str(run_id)}}
    restarted = Worker(h.application, checkpoint_factory=empty_checkpoint)
    await restarted.run_once(h.access)
    assert dict(h.reasoning.calls) == saved
    assert h.backbone.calls["persist"] == 1
    assert len(h.store.case_rows(h.access, UUID(case["case_id"]))[0]["results"]) == 1
