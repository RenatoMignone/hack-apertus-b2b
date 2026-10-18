"""Real A/B/C code together; synthetic transport/embedding, no external providers."""
import hashlib
import json
from dataclasses import replace
from io import BytesIO
from uuid import UUID, uuid4

import httpx
import pytest
from psycopg import sql
from pypdf import PdfReader
from sqlalchemy import insert, select, text
from sqlalchemy.exc import DBAPIError

from backend.application.adapters import Services
from backend.application.persistence.store import RuntimeStore
from backend.application.service import RuntimeApplication
from backend.application.worker import Worker
from backend.config.runtime import IdentityBinding
from backend.contracts.data import AccessContext
from backend.data import schema as t
from backend.data.admin import grant_scope, provision_principal
from backend.data.backbone import create_backbone
from backend.data.database import engine_for, transaction
from backend.data.fixtures import FixtureEmbedder
from backend.evidence import create_reasoning_services
from backend.models.reasoning import ModelSettings
from backend.reports.rendering import create_pdf_renderer

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


@pytest.fixture
def restricted(harness):
    h = harness
    roles, engines, users = [], [], []
    for _ in range(2):
        role = "integrated_" + uuid4().hex[:12]
        principal, password = provision_principal(h.store.engine, role, h.access.namespace)
        grant_scope(h.store.engine, principal, UUID(h.fixture["scope_id"]))
        engine = engine_for(h.store.engine.url.set(username=role, password=password).render_as_string(hide_password=False))
        roles.append(role)
        engines.append(engine)
        access = AccessContext(principal_id=principal, namespace=h.access.namespace)
        users.append((RuntimeStore(engine, h.settings, h.store.artifacts), access))
    try:
        yield users
    finally:
        for engine in engines:
            engine.dispose()
        with h.store.engine.begin() as c:
            for role in roles:
                c.connection.driver_connection.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
                c.connection.driver_connection.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


def synthetic_transport(request):
    body = json.loads(request.content)
    task = body["messages"][0]["content"].split("TASK: ")[1].splitlines()[0]
    data = json.loads(body["messages"][1]["content"])
    if task == "interpret":
        result = {"company_name": "Synthetic Company", "company_summary": "An operator-described sensor developer.",
            "activity_label": "glucose sensors", "bern_intents": ["Research in Bern"],
            "needs": ["Glucose sensor research"], "search_terms": ["glucose monitoring"]}
    elif task == "extract":
        record = next(e for e in data["evidence"] if e["language"] == "en")
        result = {"entities": [{"key": "unit", "entity_type": "unit", "display_label": "Synthetic example",
            "evidence_ids": [record["evidence_id"]]}], "claims": [{"key": "cap", "subject_key": "unit",
            "predicate": "capability", "typed_literal": {"type": "text", "value": record["literal_text"]},
            "statement": record["literal_text"], "evidence_ids": [record["evidence_id"]]}]}
    elif task == "assess_claims":
        result = {"decisions": [{"claim_id": c["claim_id"], "status": "supported",
            "explanation": "Explicit synthetic transport response; no semantic-quality claim."} for c in data["claims"]]}
    elif task == "fit_opportunities":
        result = {"matches": [{"need_index": 0, "claim_ids": [data["claims"][0]["claim_id"]],
            "rationale": "Glucose research", "potential_benefit": "Investigate research fit", "kind": "direct"}]}
    elif task == "draft":
        claim = data["pack"]["claims"][0]
        result = {"reasons": [{"id": "sensor", "headline": "Synthetic glucose research",
            "text": claim["text"], "claim_ids": [claim["claim_id"]]}]}
    elif task == "assess_draft":
        result = {"status": "supported", "explanation": "Synthetic transport fixture verdict."}
    else:
        raise AssertionError(task)
    return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": json.dumps(result)}}]})


async def test_real_lanes_restricted_role_review_and_actual_pdf(harness, restricted):
    from backend.api.app import create_app
    store, access = restricted[0]
    token = "explicit-integration-token"
    binding = IdentityBinding(token_sha256=hashlib.sha256(token.encode()).hexdigest(),
        principal_id=access.principal_id, namespace=access.namespace)
    store.settings = replace(store.settings, bindings=(binding,))
    services = Services(reasoning=create_reasoning_services(ModelSettings(api_key="fixture-only"),
        transport=httpx.MockTransport(synthetic_transport)),
        backbone=create_backbone(store.engine, store.artifacts, FixtureEmbedder()), pdf=create_pdf_renderer())
    application = RuntimeApplication(store, services)
    worker = Worker(application, checkpoint_factory=harness.checkpoint)
    class Registry:
        settings = store.settings
        def application(self, supplied):
            assert supplied == binding
            return application
        def close(self):
            pass
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=create_app(Registry())), base_url="http://test",
        headers={"Authorization": "Bearer " + token, "Idempotency-Key": "create"}) as client:
        created = await client.post("/api/v1/cases", json={"prompt": "Public glucose research in Bern"})
        assert created.status_code == 201, created.text
        assert await worker.run_once(access)
        run = await client.get(created.json()["status_url"])
        assert run.json()["status"] == "succeeded", run.text
        case_url = "/api/v1/cases/" + created.json()["case_id"]
        detail = (await client.get(case_url)).json()
        result = detail["revisions"][0]
        assert detail["evidence"] and result["reasons"][0]["line"]["evidenceIds"]
        report_url = case_url + "/reports/" + result["id"]
        selected = await client.put(report_url + "/reasons/sensor/selection", headers={"Idempotency-Key": "keep"},
            json={"selection": "kept", "expected_result_hash": result["resultHash"]})
        assert selected.status_code == 200, selected.text
        digest = selected.json()["selection_hash"]
        review = await client.post(report_url + "/reviews", headers={"Idempotency-Key": "review"},
            json={"decision": "accepted", "expected_result_hash": result["resultHash"], "expected_selection_hash": digest})
        assert review.status_code == 201, review.text
        queued = await client.post(case_url + "/exports", headers={"Idempotency-Key": "pdf"}, json={
            "result_id": result["id"], "review_id": review.json()["review_id"],
            "expected_result_hash": result["resultHash"], "expected_selection_hash": digest})
        assert queued.status_code == 202, queued.text
        assert await worker.run_once(access)
        operation = await client.get(queued.json()["status_url"])
        assert operation.json()["status"] == "committed", operation.text
        downloaded = await client.get(operation.json()["download_url"])
        assert downloaded.status_code == 200, downloaded.text[:200]
        output = "\n".join(page.extract_text() for page in PdfReader(BytesIO(downloaded.content)).pages)
        assert "Synthetic Company" in output and "Glucose sensor research" in output
        assert "Operator-provided context" in output and "Synthetic example: glucose monitoring" in output
        changed = await client.post(case_url + "/messages", headers={"Idempotency-Key": "focus"}, json={
            "text": "Focus on sensor measurements", "kind": "focus", "expected_revision": detail["revision"]})
        assert changed.status_code == 202, changed.text
        assert await worker.run_once(access)
        state = await client.get(changed.json()["status_url"])
        assert state.json()["status"] == "succeeded", state.text
        history = await client.get(case_url)
        assert history.status_code == 200, history.text
        assert len(history.json()["revisions"]) == 2
        assert (await client.get(operation.json()["download_url"])).status_code == 409


async def test_case_scope_provisioning_and_direct_db_runtime_isolation(restricted):
    (one, owner), (two, other) = restricted
    created = one.create(owner, "create", {"prompt": "Public synthetic glucose research"}, "req")
    case_id, run_id = UUID(created["case_id"]), UUID(created["run_id"])
    with transaction(one.engine, owner) as c:
        first = c.execute(text("SELECT ops.ensure_case_scope(:case)"), {"case": case_id}).scalar_one()
        assert first == c.execute(text("SELECT ops.ensure_case_scope(:case)"), {"case": case_id}).scalar_one()
        assert c.execute(select(t.scopes).where(t.scopes.c.scope_id == first)).first()
    with transaction(two.engine, other) as c:
        assert not c.execute(select(t.attempts).where(t.attempts.c.run_id == run_id)).first()
        assert not c.execute(select(t.outbox).where(t.outbox.c.event_type == "runtime.command")).first()
    with pytest.raises(DBAPIError):
        with transaction(two.engine, other) as c:
            c.execute(text("SELECT ops.ensure_case_scope(:case)"), {"case": case_id})
    with pytest.raises(DBAPIError):
        with transaction(two.engine, other) as c:
            c.execute(insert(t.attempts).values(attempt_id=uuid4(), run_id=run_id, namespace=owner.namespace,
                stage="runtime.stolen", input_hash="x", config_hash="x", idempotency_key=uuid4().hex))
    with pytest.raises(DBAPIError):
        with transaction(two.engine, other) as c:
            c.execute(insert(t.scope_grants).values(principal_id=other.principal_id, scope_id=first, can_write=True))


async def test_http_lifecycle_flags_actions_and_notes_persist(harness):
    h = harness
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=h.app), base_url="http://test", headers=h.headers) as client:
        created = await client.post("/api/v1/cases", json={"prompt": "Permitted company context", "run": False})
        assert created.status_code == 201, created.text
        case_url = "/api/v1/cases/" + created.json()["case_id"]
        for key, body in [("close", {"expected_revision": 0, "status": "closed"}),
            ("hold", {"expected_revision": 1, "on_hold": True, "outcome": "visit"})]:
            response = await client.patch(case_url, headers={"Idempotency-Key": key}, json=body)
            assert response.status_code == 200, response.text
        detail = (await client.get(case_url)).json()
        assert detail["case"]["status"] == "closed" and detail["case"]["outcome"] == "visit" and detail["case"]["onHold"]
        action = await client.post("/api/v1/action-items", headers={"Idempotency-Key": "action"}, json={
            "case_id": created.json()["case_id"], "question": "Who knows this unit?", "ask_role": "Account owner"})
        assert action.status_code == 201, action.text
        answered = await client.patch("/api/v1/action-items/" + action.json()["id"], headers={"Idempotency-Key": "answer"},
            json={"status": "done", "answer": "Ask the existing contact."})
        assert answered.status_code == 200, answered.text
        actions = (await client.get("/api/v1/action-items")).json()
        assert actions[0]["answer"] == "Ask the existing contact."
        assert actions[0]["status"] == "done"
        reopened = await client.patch(case_url, headers={"Idempotency-Key": "reopen"},
            json={"expected_revision": 2, "status": "in_review", "on_hold": False})
        assert reopened.status_code == 200, reopened.text
        again = (await client.get(case_url)).json()["case"]
        assert again["status"] == "in_review" and not again["onHold"] and "outcome" not in again
