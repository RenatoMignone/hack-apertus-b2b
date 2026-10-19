"""HTTP adapters only. Durable work runs in a separate worker, never BackgroundTasks."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from starlette.responses import Response

from backend.api import schemas as s
from backend.api.security import Actor, actor, idempotency_key

router = APIRouter(prefix="/api/v1")


@router.get("/capabilities")
async def capabilities(request: Request, who: Actor = Depends(actor)):
    settings = request.app.state.registry.settings
    return {"schema_version": "1", "service_contract_version": "1", "deployment_mode": settings.mode,
        "formats": ["pdf"] if (settings.pdf_factory and settings.template_version != "unconfigured"
            and settings.renderer_version != "unconfigured") else [], "frontend_transport": "polling",
        "reasoning_configured": bool(settings.reasoning_factory), "backbone_configured": bool(settings.backbone_factory),
        "web_configured": settings.mode == "connected" and bool(settings.web_factory)}


@router.get("/cases", response_model=list[s.CaseSummary])
async def cases(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0, le=10000), who: Actor = Depends(actor)):
    return await who.application.list_cases(who.access, limit=limit, offset=offset)


@router.post("/cases", status_code=201, response_model=s.Accepted, response_model_exclude_none=True)
async def create_case(body: s.CreateCase, request: Request, who: Actor = Depends(actor), key=Depends(idempotency_key)):
    return await who.application.execute("create", who.access, key, body.model_dump(mode="json"), request.state.request_id)


@router.get("/cases/{case_id}", response_model=s.CaseDetail, response_model_exclude_none=True)
async def case_detail(case_id: UUID, who: Actor = Depends(actor)):
    return await who.application.detail(who.access, case_id)


@router.patch("/cases/{case_id}")
async def patch_case(case_id: UUID, body: s.PatchCase, who: Actor = Depends(actor), key=Depends(idempotency_key)):
    return await who.application.execute("patch_case", who.access, key, case_id, body.model_dump(mode="json", exclude_unset=True))


@router.post("/cases/{case_id}/runs", status_code=202, response_model=s.Accepted, response_model_exclude_none=True)
async def start_run(case_id: UUID, body: s.StartRun, request: Request, who: Actor = Depends(actor), key=Depends(idempotency_key)):
    return await who.application.execute("start_command", who.access, key, case_id, body.model_dump(mode="json"), request.state.request_id)


@router.get("/cases/{case_id}/runs/{run_id}", response_model=s.RunView, response_model_exclude_none=True)
async def run(case_id: UUID, run_id: UUID, who: Actor = Depends(actor)):
    return await who.application.execute("run_view", who.access, case_id, run_id)


@router.post("/cases/{case_id}/messages", status_code=202)
@router.post("/cases/{case_id}/inputs", status_code=202)
async def message(case_id: UUID, body: s.Message, request: Request, who: Actor = Depends(actor), key=Depends(idempotency_key)):
    return await who.application.execute("edit", who.access, key, case_id, body.model_dump(mode="json"), request.state.request_id)


@router.post("/cases/{case_id}/runs/{run_id}/answers", status_code=202)
async def answer(case_id: UUID, run_id: UUID, body: s.Answer, who: Actor = Depends(actor), key=Depends(idempotency_key)):
    return await who.application.execute("answer", who.access, key, case_id, run_id, body.model_dump(mode="json"))


@router.post("/cases/{case_id}/runs/{run_id}/cancel", status_code=202)
async def cancel(case_id: UUID, run_id: UUID, who: Actor = Depends(actor), key=Depends(idempotency_key)):
    return await who.application.execute("cancel", who.access, key, case_id, run_id)


@router.get("/cases/{case_id}/evidence-packs/{pack_id}")
async def pack(case_id: UUID, pack_id: UUID, who: Actor = Depends(actor)):
    record = await who.application.execute("pack", who.access, pack_id)
    await who.application.execute("run_view", who.access, case_id, record["run_id"])
    return {"id": str(pack_id), "hash": record["pack_hash"], "payload": record["payload"]}


@router.get("/cases/{case_id}/evidence/{evidence_id}")
async def evidence(case_id: UUID, evidence_id: UUID, run_id: UUID, pack_id: UUID | None = None, who: Actor = Depends(actor)):
    return await who.application.evidence(who.access, case_id, run_id, evidence_id, pack_id)


@router.post("/cases/{case_id}/reports", status_code=202)
async def create_report(case_id: UUID, body: s.ReportRequest, request: Request, who: Actor = Depends(actor), key=Depends(idempotency_key)):
    return await who.application.execute("report", who.access, key, case_id, body.model_dump(mode="json"), request.state.request_id)


@router.post('/cases/{case_id}/memory')
async def case_memory(case_id: UUID, body: s.MemoryRequest, who: Actor = Depends(actor), key=Depends(idempotency_key)):
    from backend.contracts.services import ServiceUnavailable
    if not who.application.services.memory:
        raise ServiceUnavailable()
    return await who.application.services.memory.set(who.access, case_id, key, body.model_dump(mode='json'))


@router.get("/cases/{case_id}/runs/{run_id}/matches")
async def matches(case_id: UUID, run_id: UUID, who: Actor = Depends(actor)):
    return await who.application.execute("run_content", who.access, case_id, run_id)


@router.get("/cases/{case_id}/exports/{export_id}")
async def export_status(case_id: UUID, export_id: UUID, who: Actor = Depends(actor)):
    return await who.application.execute("export_view", who.access, case_id, export_id)


@router.get("/cases/{case_id}/reports/{result_id}", response_model=s.BriefRevision, response_model_exclude_none=True)
async def report(case_id: UUID, result_id: UUID, who: Actor = Depends(actor)):
    detail = await who.application.detail(who.access, case_id)
    for revision in detail["revisions"]:
        if revision["id"] == str(result_id):
            return revision
    raise PermissionError()


@router.put("/cases/{case_id}/reports/{result_id}/reasons/{reason_key}/selection")
async def selection(case_id: UUID, result_id: UUID, reason_key: str, body: s.SetSelection,
                    who: Actor = Depends(actor), key=Depends(idempotency_key)):
    return await who.application.execute("select_reason", who.access, key, case_id, result_id, reason_key,
                                         body.model_dump(mode="json"))


@router.post("/cases/{case_id}/reports/{result_id}/reviews", status_code=201)
async def review(case_id: UUID, result_id: UUID, body: s.Review, who: Actor = Depends(actor), key=Depends(idempotency_key)):
    return await who.application.execute("review", who.access, key, case_id, result_id, body.model_dump(mode="json"))


@router.post("/cases/{case_id}/exports", status_code=202)
async def export(case_id: UUID, body: s.Export, who: Actor = Depends(actor), key=Depends(idempotency_key)):
    return await who.application.execute("queue_export", who.access, key, case_id, body.result_id, body.model_dump(mode="json"))


@router.get("/operations/{operation_id}", response_model=s.OperationView, response_model_exclude_none=True)
async def operation(operation_id: UUID, who: Actor = Depends(actor)):
    return await who.application.execute("operation", who.access, operation_id)


@router.get("/cases/{case_id}/exports/{export_id}/download", responses={200: {"content": {"application/pdf": {"schema": {"type": "string", "format": "binary"}}}}})
async def download(case_id: UUID, export_id: UUID, who: Actor = Depends(actor)):
    data = await who.application.execute("download", who.access, case_id, export_id)
    return Response(data, media_type="application/pdf", headers={
        "Content-Disposition": f'attachment; filename="bern-report-{export_id}.pdf"', "Cache-Control": "no-store"})


@router.get("/action-items")
async def actions(who: Actor = Depends(actor)):
    return await who.application.execute("actions", who.access)


@router.patch("/action-items/{action_id}")
async def action(action_id: UUID, body: s.ActionStatus, who: Actor = Depends(actor), key=Depends(idempotency_key)):
    return await who.application.execute("action_status", who.access, key, action_id, body.model_dump(mode="json", exclude_unset=True))


@router.post("/action-items", status_code=201)
async def create_action(body: s.CreateAction, who: Actor = Depends(actor), key=Depends(idempotency_key)):
    return await who.application.execute("create_action", who.access, key, body.model_dump(mode="json"))
