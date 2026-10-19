from dataclasses import replace
from datetime import datetime, timezone
from uuid import UUID

import pytest
from sqlalchemy import select

from backend.contracts.pipeline import ReportEvidencePack
from backend.contracts.services import BudgetExceeded, EvidenceAssessment, ClaimAssessment
from backend.data import schema as t


@pytest.mark.asyncio
@pytest.mark.parametrize('allowance', [0, 300])
async def test_draft_allowance_is_pinned_bounded_and_stable_on_reuse(harness, allowance):
    h = harness
    h.store.settings = replace(h.settings, deadline_seconds=60, draft_deadline_seconds=allowance)
    created = h.store.create(h.access, 'budget', {'prompt': 'Public sensor research'}, 'budget')
    run_id = UUID(created['run_id'])
    initial = h.store.context(h.access, run_id)
    h.store.settings = replace(h.store.settings, draft_deadline_seconds=900)
    seen = []
    original = h.reasoning.draft
    async def draft(pack, instruction, context):
        seen.append(context.deadline_at)
        return await original(pack, instruction, context)
    h.reasoning.draft = draft
    await h.worker.run_once(h.access)
    status = h.store.run_view(h.access, UUID(created['case_id']), run_id)
    assert status['status'] == 'succeeded', status
    with h.store.session(h.access) as c:
        row = c.execute(select(t.packs).where(t.packs.c.run_id == run_id)).mappings().one()
        config = c.execute(select(t.runs.c.configuration).where(t.runs.c.run_id == run_id)).scalar_one()
        assessed = c.execute(select(t.assessments.c.payload).where(t.assessments.c.run_id == run_id)).scalars().all()
    assert config['draft_deadline_seconds'] == allowance
    assert datetime.fromisoformat(config['deadline_at']) == initial.deadline_at
    elapsed_extra = (seen[0] - initial.deadline_at).total_seconds()
    assert 0 <= elapsed_extra <= allowance
    if allowance:
        assert (seen[0]-row['created_at']).total_seconds() == allowance
    else:
        assert seen[0] == initial.deadline_at
    pack = ReportEvidencePack.model_validate(row['payload'])
    assessment = EvidenceAssessment(assessments=[ClaimAssessment.model_validate(a) for a in assessed])
    first = h.store.save_pack(h.access, run_id, pack, assessment)
    second = h.store.save_pack(h.access, run_id, pack, assessment)
    assert first == second
    assert datetime.fromisoformat(second['draft_deadline_at']) == seen[0]


@pytest.mark.asyncio
async def test_failed_draft_retries_saved_pack_without_research(harness):
    h = harness
    original = h.reasoning.draft
    async def exhausted(*args):
        raise BudgetExceeded()
    h.reasoning.draft = exhausted
    created = h.store.create(h.access, 'failure', {'prompt': 'Public sensor research'}, 'failure')
    await h.worker.run_once(h.access)
    case_id, run_id = UUID(created['case_id']), UUID(created['run_id'])
    status = h.store.run_view(h.access, case_id, run_id)
    assert status['status'] == 'failed' and status['pack_id']
    assert status['step'] == 'draft.1'
    research_calls = h.backbone.calls['retrieve']
    with h.store.session(h.access) as c:
        revision = c.execute(select(t.cases.c.revision).where(t.cases.c.case_id == case_id)).scalar_one()
    h.reasoning.draft = original
    retry = h.store.report(h.access, 'retry', case_id,
        {'expected_revision': revision, 'pack_id': status['pack_id'], 'instruction': 'Write concise supported report'}, 'retry')
    assert h.store.context(h.access, UUID(retry['run_id'])).deadline_at > datetime.now(timezone.utc)
    await h.worker.run_once(h.access)
    result = h.store.run_view(h.access, case_id, UUID(retry['run_id']))
    assert result['status'] == 'succeeded', result
    assert h.backbone.calls['retrieve'] == research_calls


@pytest.mark.asyncio
async def test_draft_allowance_is_not_available_to_followup_research(harness):
    h = harness
    h.reasoning.bad_draft = True
    research_deadlines, draft_deadlines = [], []
    retrieve, draft = h.backbone.retrieve, h.reasoning.draft
    async def tracked_retrieve(plan, context):
        research_deadlines.append(context.deadline_at)
        return await retrieve(plan, context)
    async def tracked_draft(pack, instruction, context):
        draft_deadlines.append(context.deadline_at)
        return await draft(pack, instruction, context)
    h.backbone.retrieve, h.reasoning.draft = tracked_retrieve, tracked_draft
    h.store.settings = replace(h.settings, deadline_seconds=60, draft_deadline_seconds=300)
    created = h.store.create(h.access, 'draft-research', {'prompt': 'Public sensor research'}, 'draft-research')
    original = h.store.context(h.access, UUID(created['run_id'])).deadline_at
    await h.worker.run_once(h.access)
    assert draft_deadlines and all(deadline > original for deadline in draft_deadlines)
    assert research_deadlines and all(deadline == original for deadline in research_deadlines)
