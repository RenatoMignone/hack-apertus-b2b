"""Async use cases: transport-independent and backed by durable PostgreSQL state."""
import asyncio
from datetime import datetime, timedelta, timezone

from backend.contracts.frontend import case_view
from backend.contracts.pipeline import ReportEvidencePack
from backend.contracts.services import EvidenceRecord, EvidenceRejected


class RuntimeApplication:
    def __init__(self, store, services, tracer=None):
        self.store, self.services, self.tracer = store, services, tracer

    async def execute(self, method, *args, **kwargs):
        return await asyncio.to_thread(getattr(self.store, method), *args, **kwargs)

    async def detail(self, access, case_id):
        data = (await self.execute("case_rows", access, case_id))[0]
        evidence = {}
        for row in data["results"]:
            pack = data["packs"][str(row["pack_id"])]
            payload = ReportEvidencePack.model_validate(pack["payload"])
            ids = sorted({e for claim in payload.claims for e in claim.evidence_ids}, key=str)
            if ids:
                context = (await self.execute("context", access, pack["run_id"])).model_copy(update={
                    "deadline_at": datetime.now(timezone.utc) + timedelta(seconds=30)})
                records = await self.read_evidence(ids, context)
                if {record.evidence_id for record in records} != set(ids):
                    raise EvidenceRejected()
                # Read access/hash checked by repositories above; source projections come from C.
                evidence.update({record.evidence_id: record for record in records})
        projected = case_view(data, list(sorted(evidence.values(), key=lambda record: str(record.evidence_id))))
        current = data["case"]["current_result_id"]
        if current:
            projected["selectionHash"] = await self.execute("selection_state", access, case_id, current)
        run_id = await self.execute("current_run", access, case_id)
        if run_id:
            projected["currentRun"] = await self.execute("run_view", access, case_id, run_id)
        return projected

    async def list_cases(self, access, *, limit=50, offset=0):
        data = await self.execute("case_rows", access, limit=limit, offset=offset)
        return [case_view(row, [])["case"] for row in data]

    async def evidence(self, access, case_id, run_id, evidence_id, pack_id=None):
        await self.execute("run_view", access, case_id, run_id)
        if pack_id:
            pack = await self.execute("pack", access, pack_id)
            if pack["run_id"] != run_id:
                raise PermissionError()
            ids = {e for claim in ReportEvidencePack.model_validate(pack["payload"]).claims for e in claim.evidence_ids}
            if evidence_id not in ids:
                raise PermissionError()
        else:
            # Raw arbitrary case-local evidence IDs cannot be requested without pack membership.
            data = await self.execute("case_rows", access, case_id)
            packs = [p for p in data[0]["packs"].values() if p["run_id"] == run_id]
            if not any(evidence_id in {e for claim in ReportEvidencePack.model_validate(p["payload"]).claims for e in claim.evidence_ids}
                       for p in packs):
                raise PermissionError()
        context = (await self.execute("context", access, run_id)).model_copy(update={
            "deadline_at": datetime.now(timezone.utc) + timedelta(seconds=30)})
        records = await self.read_evidence([evidence_id], context)
        if len(records) != 1 or records[0].evidence_id != evidence_id:
            raise EvidenceRejected()
        return records[0]

    async def read_evidence(self, ids, context):
        from backend.contracts.services import ServiceError, ServiceUnavailable
        try:
            async with asyncio.timeout(30):
                records = await self.services.backbone.read_evidence(ids, context)
                return [EvidenceRecord.model_validate(record) for record in records]
        except ServiceError:
            raise
        except Exception:
            raise ServiceUnavailable() from None
