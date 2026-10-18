"""Deadline enforcement and durable per-node output reuse."""
import asyncio
import json
from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, ValidationError

from backend.contracts.services import BudgetExceeded, InvalidModelOutput


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

    def remaining(self):
        remaining = (self.context.deadline_at - datetime.now(timezone.utc)).total_seconds()
        if remaining <= 0:
            raise BudgetExceeded()
        return remaining

    async def call(self, name, inputs, task):
        inputs = encoded(inputs)
        _, cached = await asyncio.to_thread(self.store.stage_output, self.context.access, self.context.run_id, name, inputs)
        if cached is not None:
            return cached["value"]
        self.remaining()
        started = datetime.now(timezone.utc)
        try:
            async with asyncio.timeout(self.remaining()):
                value = encoded(await task())
        except TimeoutError:
            raise BudgetExceeded() from None
        except ValidationError:
            raise InvalidModelOutput() from None
        result = await asyncio.to_thread(self.store.commit_stage, self.context.access, self.context.run_id,
                                        name, inputs, {"value": value})
        if self.tracer:
            self.tracer.emit({"run_id": str(self.context.run_id), "stage": "stage",
                "duration_ms": (datetime.now(timezone.utc) - started).total_seconds() * 1000})
        return result["value"]
