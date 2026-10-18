"""Actual LangGraph + API over disposable PostgreSQL, with explicit B/C fixtures."""
from uuid import UUID

import httpx
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_create_run_review_export_and_wording_edit(harness):
    h = harness
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=h.app), base_url="http://test", headers=h.headers) as client:
        response = await client.post("/api/v1/cases", json={"prompt": "Synthetic glucose research and a Bern lab"})
        assert response.status_code == 201, response.text
        case = response.json()
        assert await h.worker.run_once(h.access)
        run = await client.get(case["status_url"])
        assert run.json()["status"] == "succeeded", run.text
        response = await client.get(f"/api/v1/cases/{case['case_id']}")
        assert response.status_code == 200, response.text
        detail = response.json()
        result = detail["revisions"][0]
        assert detail["evidence"] and result["reasons"][0]["line"]["evidenceIds"]
        url = f"/api/v1/cases/{case['case_id']}/reports/{result['id']}"
        denied = await client.post(url + "/reviews", headers={"Idempotency-Key": "early"}, json={
            "decision": "accepted", "expected_result_hash": result["resultHash"], "expected_selection_hash": detail["selectionHash"]})
        assert denied.status_code == 409
        selected = await client.put(url + "/reasons/reason1/selection", headers={"Idempotency-Key": "keep"}, json={
            "selection": "kept", "expected_result_hash": result["resultHash"]})
        assert selected.status_code == 200, selected.text
        digest = selected.json()["selection_hash"]
        review = await client.post(url + "/reviews", headers={"Idempotency-Key": "review"}, json={
            "decision": "accepted", "expected_result_hash": result["resultHash"], "expected_selection_hash": digest})
        assert review.status_code == 201, review.text
        export = await client.post(f"/api/v1/cases/{case['case_id']}/exports", headers={"Idempotency-Key": "pdf"}, json={
            "result_id": result["id"], "review_id": review.json()["review_id"], "expected_result_hash": result["resultHash"],
            "expected_selection_hash": digest})
        assert export.status_code == 202, export.text
        assert await h.worker.run_once(h.access)
        operation = await client.get(export.json()["status_url"])
        assert operation.json()["status"] == "committed", operation.text
        download = await client.get(operation.json()["download_url"])
        assert download.status_code == 200 and download.content.startswith(b"%PDF-")
        assert h.pdf.report.claims[0].evidence_ids == [h.pdf.report.evidence[0].evidence_id]
        edited = await client.post(f"/api/v1/cases/{case['case_id']}/messages", headers={"Idempotency-Key": "rephrase"},
            json={"text": "Shorten the explanation", "kind": "formatting", "expected_revision": detail["revision"]})
        assert edited.status_code == 202, edited.text
        assert await h.worker.run_once(h.access)
        assert h.reasoning.calls["interpret"] == 1 and h.backbone.calls["retrieve"] == 1
        detail2 = await client.get(f"/api/v1/cases/{case['case_id']}")
        assert detail2.status_code == 200, detail2.text
        assert len(detail2.json()["revisions"]) == 2
        assert (await client.get(operation.json()["download_url"])).status_code == 409


async def test_clarification_is_durable_and_resumes(harness):
    h = harness
    h.reasoning.block = True
    result = h.store.create(h.access, "new", {"prompt": "Ambiguous research in Bern"}, "req")
    assert await h.worker.run_once(h.access)
    state = h.store.run_view(h.access, UUID(result["case_id"]), UUID(result["run_id"]))
    assert state["state"] == "needs_clarification"
    question = state["questions"][0]
    h.store.answer(h.access, "answer", UUID(result["case_id"]), UUID(result["run_id"]), {
        "input_id": result["input_id"], "question_id": question["id"], "answer": "Glucose monitoring"})
    assert await h.worker.run_once(h.access)
    state = h.store.run_view(h.access, UUID(result["case_id"]), UUID(result["run_id"]))
    assert state["state"] == "completed", state
    assert h.reasoning.calls["interpret"] == 2
