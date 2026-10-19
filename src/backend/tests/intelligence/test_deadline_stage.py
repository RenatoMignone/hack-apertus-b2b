import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from backend.contracts.services import BudgetExceeded
from backend.workflows.execution import Execution


def test_expired_draft_budget_identifies_stage_without_calling_model(context):
    context = context.model_copy(update={'deadline_at': datetime.now(timezone.utc)-timedelta(seconds=1)})
    store = SimpleNamespace(stage_output=lambda *args: (None, None))
    async def model():
        pytest.fail('Expired run must not call a model')
    with pytest.raises(BudgetExceeded) as failure:
        asyncio.run(Execution(store, context).call('draft.1', {}, model))
    assert failure.value.failed_stage == 'draft.1'


def test_inflight_draft_deadline_identifies_stage(context):
    context = context.model_copy(update={'deadline_at': datetime.now(timezone.utc)+timedelta(milliseconds=30)})
    store = SimpleNamespace(stage_output=lambda *args: (None, None))
    async def model():
        await asyncio.sleep(1)
    with pytest.raises(BudgetExceeded) as failure:
        asyncio.run(Execution(store, context).call('draft_rewrite.1', {}, model))
    assert failure.value.failed_stage == 'draft_rewrite.1'


def test_committed_stage_output_remains_reusable_after_deadline(context):
    context = context.model_copy(update={'deadline_at': datetime.now(timezone.utc)-timedelta(seconds=1)})
    store = SimpleNamespace(stage_output=lambda *args: (None, {'value': {'saved': True}}))
    async def model():
        pytest.fail('Committed output must be reused')
    assert asyncio.run(Execution(store, context).call('draft.1', {}, model)) == {'saved': True}
