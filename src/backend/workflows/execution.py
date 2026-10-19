"""Deadline enforcement and durable per-node output reuse."""
import asyncio
import json
from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, ValidationError

from backend.observability.logging import activity, event

from backend.contracts.services import BudgetExceeded, InvalidModelOutput, ServiceError


def encoded(value):
    def default(item):
        if isinstance(item, BaseModel):
            return item.model_dump(mode="json")
        if isinstance(item, (UUID, datetime)):
            return str(item) if isinstance(item, UUID) else item.isoformat()
        raise TypeError("stage output must be JSON serializable")
    return json.loads(json.dumps(value, default=default))


class Execution:
    def __init__(self, store, context, tracer=None):
        self.store, self.context, self.tracer = store, context, tracer

    def remaining(self, stage=None):
        remaining = (self.context.deadline_at - datetime.now(timezone.utc)).total_seconds()
        if remaining <= 0:
            error = BudgetExceeded()
            if stage:
                error.failed_stage = stage
            raise error
        return remaining

    async def call(self, name, inputs, task):
        inputs = encoded(inputs)
        _, cached = await asyncio.to_thread(self.store.stage_output, self.context.access, self.context.run_id, name, inputs)
        if cached is not None:
            event("stage.reused", run_id=self.context.run_id, case_id=self.context.case_id, stage=name)
            return cached["value"]
        self.remaining(name)
        started = datetime.now(timezone.utc)
        progress = hasattr(self.store, "start_activity")
        if progress:
            try:
                await asyncio.to_thread(self.store.start_activity, self.context.access, self.context.run_id, name)
            except Exception:
                progress = False
                event("stage.progress_unavailable", run_id=self.context.run_id, stage=name)
        succeeded = False
        try:
            async with activity("stage", run_id=self.context.run_id, case_id=self.context.case_id, stage=name), asyncio.timeout(self.remaining(name)):
                value = encoded(await task())
                succeeded = True
        except TimeoutError:
            error = BudgetExceeded()
            error.failed_stage = name
            raise error from None
        except ValidationError:
            error = InvalidModelOutput()
            error.failed_stage = name
            raise error from None
        except ServiceError as error:
            error.failed_stage = name
            raise
        finally:
            if progress:
                try:
                    await asyncio.to_thread(self.store.finish_activity, self.context.access, self.context.run_id, name, failed=not succeeded)
                except Exception:
                    event("stage.progress_unavailable", run_id=self.context.run_id, stage=name)
        result = await asyncio.to_thread(self.store.commit_stage, self.context.access, self.context.run_id,
                                        name, inputs, {"value": value})
        if self.tracer:
            self.tracer.emit({"run_id": str(self.context.run_id), "stage": "stage",
                "duration_ms": (datetime.now(timezone.utc) - started).total_seconds() * 1000})
        return result["value"]
