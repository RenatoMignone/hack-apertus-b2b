from uuid import UUID

import httpx
import pytest
from sqlalchemy import select

from backend.contracts.services import ResearchQueries
from backend.data import schema as t
from backend.evidence import create_reasoning_services
from backend.models.reasoning.fixtures import FixtureChatModel
from backend.workflows.lineage import search_trace


def test_lineage_resolves_mirrors_and_omits_unrecorded_links():
    from backend.tests.intelligence.benchmark import fixture
    _, original, _, _ = fixture()
    mirror = original.model_copy(update={'evidence_id':UUID(int=44),'document_version_id':UUID(int=45)})
    trace = search_trace(UUID(int=1),[{'query':'glucose sensors','evidence_ids':[str(original.evidence_id)]},
        {'query':'invented path','evidence_ids':[str(UUID(int=99))]}],[original],[mirror])
    assert [q['label'] for q in trace['terms']] == ['glucose sensors']
    assert any(e['target'] == str(mirror.evidence_id) for e in trace['links'])
    assert not search_trace(UUID(int=1),[],[original],[mirror])['links']


@pytest.mark.integration
@pytest.mark.asyncio
async def test_gap_research_keeps_earlier_claims_and_freezes_only_final_pack(harness):
    h = harness
    original = h.reasoning.propose_pack
    async def pack(*args):
        value = await original(*args)
        return value.model_copy(update={'gaps':['Need testing infrastructure details'] if h.reasoning.calls['pack']==1 else []})
    h.reasoning.propose_pack = pack
    plans = []
    retrieve = h.backbone.retrieve
    async def tracked(plan, context):
        plans.append(plan)
        return await retrieve(plan, context)
    h.backbone.retrieve = tracked
    async def revise(interpretation, gaps, previous, context):
        assert 'Need testing infrastructure details' in gaps
        return ResearchQueries(variants=['sensor testing infrastructure Bern'])
    h.reasoning.revise_queries = revise
    created = h.store.create(h.access,'gap',{'prompt':'Public glucose sensor research'},'test-gap')
    await h.worker.run_once(h.access)
    state = h.store.run_view(h.access,UUID(created['case_id']),UUID(created['run_id']))
    assert state['status']=='succeeded',state
    assert len(plans)==2 and plans[0].variants != plans[1].variants
    assert plans[0].original_request == plans[1].original_request
    with h.store.engine.connect() as c:
        packs = c.execute(select(t.packs).where(t.packs.c.run_id==UUID(created['run_id']))).mappings().all()
    assert len(packs)==1 and len(packs[0]['payload']['claims'])==2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_http_failure_identifies_model_task_without_provider_text(harness):
    h = harness
    h.services.reasoning = create_reasoning_services(model=FixtureChatModel(responses=['PRIVATE_RESPONSE','PRIVATE_RESPONSE']))
    created = h.store.create(h.access,'invalid',{'prompt':'Public sensor research'},'test-invalid')
    await h.worker.run_once(h.access)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=h.app),base_url='http://test',headers=h.headers) as client:
        response = await client.get(created['status_url'])
    detail = response.json()
    assert detail['status']=='failed' and detail['failure_detail']['model_task']=='interpret'
    assert detail['failure_detail']['failed_stage']=='interpret.0'
    assert detail['step']=='interpret.0' and detail['stage']=='interpreting'
    assert 'PRIVATE_RESPONSE' not in response.text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_expensive_round_leaves_time_to_publish_supported_partial_result(harness):
    from datetime import datetime,timedelta,timezone
    h=harness
    original=h.reasoning.propose_pack
    async def pack(*args):
        value=await original(*args)
        return value.model_copy(update={'gaps':['Testing infrastructure remains unknown.']})
    h.reasoning.propose_pack=pack
    from backend.workflows.evidence_nodes import PipelineNodes
    node=PipelineNodes(h.store,h.reasoning,h.backbone,None)
    created=h.store.create(h.access,'reserve',{'prompt':'Public sensor research'},'reserve')
    context=h.store.context(h.access,UUID(created['run_id'])).model_copy(update={
        'deadline_at':datetime.now(timezone.utc)+timedelta(seconds=130)})
    interpretation=await h.reasoning.interpret('Public sensor research',{},context)
    from backend.contracts.pipeline import ReportEvidencePack
    prior=ReportEvidencePack(interpretation=interpretation,outcome='no_match',gaps=['More capability context needed.'])
    state={'round':1,'round_started_at':(datetime.now(timezone.utc)-timedelta(seconds=60)).isoformat(),
           'context':context.model_dump(mode='json'),'interpretation':interpretation.model_dump(mode='json'),
           'message':'Public sensor research','pack':prior.model_dump(mode='json')}
    result=await node.plan(state)
    assert result['research_exhausted'] and h.reasoning.calls['replan']==0
    assert any('preserve time' in gap for gap in result['pack']['gaps'])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rejected_wording_gets_one_same_pack_rewrite_and_fresh_assessment(harness):
    h=harness
    h.reasoning.bad_draft=True
    assess=h.reasoning.assess_draft
    async def first_reject(draft,pack,context,**kwargs):
        verdict=await assess(draft,pack,context,**kwargs)
        h.reasoning.bad_draft=False
        return verdict
    h.reasoning.assess_draft=first_reject
    case=h.store.create(h.access,'rewrite',{'prompt':'Public sensor research'},'rewrite')
    await h.worker.run_once(h.access)
    status=h.store.run_view(h.access,UUID(case['case_id']),UUID(case['run_id']))
    assert status['status']=='succeeded',status
    assert h.reasoning.calls['draft']==2 and h.backbone.calls['retrieve']==1
    assert h.reasoning.calls['pack']==1
    with h.store.engine.connect() as c:
        rows=c.execute(select(t.attempts.c.stage).where(t.attempts.c.run_id==UUID(case['run_id']))).scalars().all()
    assert 'runtime.node.draft_rewrite.1' in rows and 'runtime.node.draft_rewrite_assessment.1' in rows


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize('entity_type', ['facility', 'service'])
async def test_infrastructure_types_reach_the_frontend_section(harness, entity_type):
    h=harness
    original=h.reasoning.extract
    async def extract(*args):
        batch=await original(*args)
        return batch.model_copy(update={'entities':[entity.model_copy(update={'entity_type':entity_type}) for entity in batch.entities]})
    h.reasoning.extract=extract
    case=h.store.create(h.access,'infrastructure',{'prompt':'Public testing facilities'},'infrastructure')
    await h.worker.run_once(h.access)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=h.app),base_url='http://test',headers=h.headers) as client:
        response=await client.get('/api/v1/cases/'+case['case_id'])
    assert response.status_code==200,response.text
    assert response.json()['revisions'][-1]['reasons'][0]['category']=='infrastructure'
