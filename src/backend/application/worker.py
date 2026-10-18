"""Separate durable worker. Browser/request lifetime never owns case execution."""
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from langgraph.types import Command
from pydantic import ValidationError

from backend.contracts.pipeline import DraftRevision, ReportEvidencePack
from backend.contracts.services import (EvidenceRejected, PdfInput, ServiceError, ServiceUnavailable, StaleRevision)
from backend.workflows.checkpoints import CheckpointPort, async_checkpoint
from backend.workflows.graph import build_graph


class Worker:
    def __init__(self, application, *, worker_id=None, checkpoint_factory=None, tracer=None):
        self.app, self.store, self.services = application, application.store, application.services
        self.worker_id = worker_id or "runtime-" + uuid4().hex
        self.checkpoint_factory, self.tracer = checkpoint_factory, tracer or application.tracer

    async def db(self, name, *args, **kwargs):
        return await asyncio.to_thread(getattr(self.store, name), *args, **kwargs)

    @asynccontextmanager
    async def checkpoints(self, access, run_id):
        if self.checkpoint_factory:
            async with self.checkpoint_factory(access, run_id) as value:
                yield value
        else:
            url = self.store.settings.langgraph_database_url
            if not url:
                raise ServiceUnavailable()
            async with async_checkpoint(CheckpointPort(self.store.engine, url), access, run_id,
                                        authorize=self.store.checkpoint_configuration) as value:
                yield value

    @asynccontextmanager
    async def run_lock(self, run_id):
        import psycopg
        dsn = self.store.engine.url.render_as_string(hide_password=False).replace("postgresql+psycopg://", "postgresql://")
        connection = await psycopg.AsyncConnection.connect(dsn, autocommit=True, connect_timeout=5)
        key = "runtime:" + str(run_id)
        acquired = False
        try:
            cursor = await connection.execute("SELECT pg_try_advisory_lock(hashtextextended(%s,0))", [key])
            acquired = (await cursor.fetchone())[0]
            yield acquired
        finally:
            try:
                if acquired:
                    await connection.execute("SELECT pg_advisory_unlock(hashtextextended(%s,0))", [key])
            finally:
                await connection.close()

    async def run_once(self, access):
        row = await self.db("claim_job", access, self.worker_id)
        if row is None:
            return False
        job = dict(row)
        async with self.run_lock(job["run_id"]) as acquired:
            if not acquired:
                await self.db("defer_job", access, job["attempt_id"], self.worker_id)
                return False
            operation = asyncio.create_task(self.perform(access, job))
            heartbeat = asyncio.create_task(self.keep_alive(access, job, operation))
            try:
                result = await operation
                await self.db("finish_job", access, job["attempt_id"], self.worker_id, result)
            except asyncio.CancelledError:
                if asyncio.current_task().cancelling():
                    operation.cancel()
                    await asyncio.gather(operation, return_exceptions=True)
                    raise
            except Exception as error:
                code = error.code if isinstance(error, ServiceError) else "service_unavailable"
                if isinstance(error, ValidationError):
                    code = "invalid_model_output"
                try:
                    if job["stage"] == "runtime.execute":
                        await self.db("mark_run", access, job["run_id"], "failed", code)
                    await self.db("finish_job", access, job["attempt_id"], self.worker_id, {"error_code": code}, failed=True)
                except (StaleRevision, ValueError):
                    pass
            finally:
                heartbeat.cancel()
                await asyncio.gather(heartbeat, return_exceptions=True)
        return True

    async def keep_alive(self, access, job, operation):
        try:
            while True:
                await asyncio.sleep(self.store.settings.worker_lease_seconds / 3)
                await self.db("heartbeat", access, job["attempt_id"], self.worker_id)
        except asyncio.CancelledError:
            raise
        except Exception:
            operation.cancel()

    async def perform(self, access, job):
        if job["stage"] == "runtime.export":
            return await self.export(access, job)
        run_id = job["run_id"]
        await self.db("execution_configuration", access, run_id)
        await self.db("mark_run", access, run_id, "running")
        async with self.checkpoints(access, run_id) as (saver, config):
            graph = build_graph(self.store, self.services.reasoning, self.services.backbone,
                                self.services.web, saver, self.tracer)
            config = {**config, "recursion_limit": 120}
            snapshot = await graph.aget_state(config)
            if snapshot.values and not snapshot.next:
                result = snapshot.values
            elif snapshot.values and any(task.interrupts for task in snapshot.tasks):
                answers = await self.db("answers", access, run_id)
                ids = {q["id"] for q in snapshot.values.get("questions", [])}
                answers = [a for a in answers if str(a["question_id"]) in ids]
                if len(answers) != len(ids):
                    await self.db("mark_run", access, run_id, "needs_clarification")
                    return {"run_id": str(run_id), "status": "waiting_for_input"}
                result = await graph.ainvoke(Command(resume={"answers": answers}), config)
            else:
                initial = None if snapshot.values else await self.db("initial_state", access, run_id)
                result = await graph.ainvoke(initial, config)
            if result.get("__interrupt__"):
                await self.db("mark_run", access, run_id, "needs_clarification")
                return {"run_id": str(run_id), "status": "waiting_for_input"}
            if not result.get("result_id"):
                raise EvidenceRejected()
        await self.db("mark_run", access, run_id, "completed")
        return {"run_id": str(run_id), "result_id": result["result_id"], "status": "succeeded"}

    async def export(self, access, job):
        command = job["outputs"]["command"]
        case_id, result_id = UUID(command["case_id"]), UUID(command["result_id"])
        prepared = await self.db("export_input", access, case_id, result_id, command)
        pack = ReportEvidencePack.model_validate(prepared["pack"]["payload"])
        draft = DraftRevision.model_validate(prepared["draft"])
        kept_claims = {key for reason in draft.reasons if reason.id in prepared["kept"] for key in reason.claim_ids}
        claims = [claim for claim in pack.claims if claim.claim_id in kept_claims]
        ids = sorted({e for claim in claims for e in claim.evidence_ids}, key=str)
        context = (await self.db("context", access, prepared["run_id"])).model_copy(update={
            "deadline_at": datetime.now(timezone.utc) + timedelta(seconds=60)})
        async with asyncio.timeout(60):
            evidence = await self.services.backbone.read_evidence(ids, context)
            if {e.evidence_id for e in evidence} != set(ids):
                raise EvidenceRejected()
            await self.db("validate_evidence", access, prepared["run_id"], evidence)
            report = PdfInput(result_id=result_id, review_id=UUID(command["review_id"]),
                result_hash=prepared["result_hash"], selection_hash=prepared["selection_hash"], draft=draft,
                interpretation=pack.interpretation, claims=claims,
                kept_reason_keys=prepared["kept"], evidence=evidence, limitations=pack.gaps,
                template_version=self.store.settings.template_version)
            data = await self.services.pdf.render(report)
        if not isinstance(data, bytes) or not data.startswith(b"%PDF-") or len(data) > 20_000_000:
            raise EvidenceRejected()
        reference = await asyncio.to_thread(self.store.artifacts.put, data, "application/pdf")
        await asyncio.to_thread(self.store.artifacts.read, reference)
        export_id = await self.db("register_export", access, job, reference, data)
        return {"export_id": str(export_id), "download_url": f"/api/v1/cases/{case_id}/exports/{export_id}/download"}
