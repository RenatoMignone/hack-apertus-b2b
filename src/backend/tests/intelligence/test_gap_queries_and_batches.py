import asyncio
import json
from uuid import uuid4

import pytest

from backend.contracts.services import (EvidenceRejected, ExtractionBatch, InvalidModelOutput,
    ResearchBundle)
from backend.evidence import create_reasoning_services
from backend.evidence.extraction_batches import extract_batches
from backend.models.reasoning.fixtures import FixtureChatModel


def test_gap_queries_are_novel_and_preserve_the_original_constraints(context, interpretation):
    interpretation = interpretation.model_copy(update={'constraints':['Exclude animal testing.']})
    model = FixtureChatModel(responses=[{'variants':[' GLUCOSE sensors ', 'biosensor signal processing facilities']}])
    service = create_reasoning_services(model=model)
    result = asyncio.run(service.revise_queries(interpretation, ['Testing infrastructure not established'],
        ['glucose sensors'], context))
    assert result.variants == ['biosensor signal processing facilities']
    payload = json.loads(model.calls[0][1].content)
    assert payload['interpretation']['constraints'] == ['Exclude animal testing.']
    assert payload['gaps'] == ['Testing infrastructure not established']


def test_extraction_batches_keep_references_and_report_excluded_failed_batch(context, interpretation, evidence):
    records = [evidence.model_copy(update={'evidence_id':uuid4()}) for _ in range(13)]
    calls = []
    async def extract(interpretation, research, context):
        calls.append(research)
        if len(calls) == 1:
            raise InvalidModelOutput()
        key = research.evidence[0].evidence_id
        return ExtractionBatch.model_validate({'entities':[{'key':'e1','entity_type':'unit',
            'display_label':'Example Laboratory','evidence_ids':[key]}], 'claims':[{
            'key':'c1','subject_key':'e1','predicate':'capability',
            'typed_literal':{'type':'string','value':'glucose sensors'},
            'statement':'Example Laboratory develops glucose sensors.','evidence_ids':[key]}]})
    result = asyncio.run(extract_batches(extract, interpretation, ResearchBundle(evidence=records), context))
    assert [len(r.evidence) for r in calls] == [12, 1]
    assert result.claims[0].subject_key == result.entities[0].key == 'b1:e1'
    assert result.gaps and len(result.claims) == 1


def test_conflicting_literal_records_are_never_silently_deduplicated(context, interpretation, evidence):
    bad = evidence.model_copy(update={'title':'conflicting source'})
    async def forbidden(*args):
        pytest.fail('Conflicting identity must fail before model execution')
    with pytest.raises(EvidenceRejected):
        asyncio.run(extract_batches(forbidden, interpretation, ResearchBundle(evidence=[evidence,bad]), context))


def test_validation_details_contain_task_and_codes_without_model_text(context):
    model = FixtureChatModel(responses=['PRIVATE_PROVIDER_BODY', 'PRIVATE_PROVIDER_BODY'])
    service = create_reasoning_services(model=model)
    with pytest.raises(InvalidModelOutput) as caught:
        asyncio.run(service.interpret('Find glucose sensor R&D in Bern', {}, context))
    error = caught.value
    assert error.model_task == 'interpret'
    assert error.validation_issues == [{'field':'$response', 'type':'json_invalid'}]
    assert 'PRIVATE' not in str(error) + json.dumps(error.validation_issues)


def test_fit_task_does_not_resend_unrelated_retrieval_passages(context,interpretation,evidence,claim):
    from backend.contracts.pipeline import ClaimAssessment
    from backend.contracts.services import EvidenceAssessment,PersistedClaims
    extra=evidence.model_copy(update={'evidence_id':uuid4(),'literal_text':'x'*90000,'char_end':90000})
    model=FixtureChatModel(responses=[{'matches':[{'need_index':0,'claim_ids':[str(claim.claim_id)],
        'rationale':'Literal capability','potential_benefit':'Investigate suitability','kind':'direct'}]}])
    service=create_reasoning_services(model=model)
    assessed=EvidenceAssessment(assessments=[ClaimAssessment(claim_id=claim.claim_id,evidence_ids=claim.evidence_ids,
        status='supported',statement=claim.text,validator='fixture',explanation='Fixture exact statement')])
    pack=asyncio.run(service.propose_pack(interpretation,PersistedClaims(claims=[claim]),assessed,
        ResearchBundle(evidence=[evidence,extra]),context))
    assert pack.claims
    payload=json.loads(model.calls[0][1].content)
    assert [row['evidence_id'] for row in payload['evidence']]==[str(evidence.evidence_id)]
    assert str(extra.evidence_id) in pack.coverage['evidence_ids']


def test_writer_and_assessor_use_claims_and_caveats_without_bulk_provenance(context,interpretation,claim,pdf_input,evidence):
    from backend.contracts.pipeline import ReportEvidencePack
    pack=ReportEvidencePack(interpretation=interpretation,claims=[claim],outcome='partial',
        gaps=['Availability is unknown.'],coverage={'large_source_manifest':'x'*90000})
    draft=pdf_input.draft.model_copy(update={'reasons':pdf_input.draft.reasons[:1]})
    model=FixtureChatModel(responses=[draft.model_dump(mode='json'),
        __import__('backend.models.reasoning.fixtures', fromlist=['draft_findings']).draft_findings(draft.model_dump(mode='json'), pack.gaps)])
    service=create_reasoning_services(model=model)
    result=asyncio.run(service.draft(pack,'Concise source facts only',context))
    checked=asyncio.run(service.assess_draft(result,pack,context,evidence=[evidence]))
    assert checked.status=='supported'
    for messages in model.calls:
        sent=json.loads(messages[1].content)['pack']
        assert 'coverage' not in sent
        assert sent['claims'][0]['claim_id']==str(claim.claim_id)
        assert sent['gaps']==['Availability is unknown.']
    assert pack.coverage['large_source_manifest']=='x'*90000
    assert json.loads(model.calls[-1][1].content)['evidence'][0]['literal_text']==evidence.literal_text


@pytest.mark.asyncio
async def test_extraction_runs_two_independent_batches_with_bounded_concurrency(context, interpretation, evidence):
    import asyncio
    from uuid import uuid4
    from backend.evidence.extraction_batches import extract_batches
    from backend.contracts.services import ExtractionBatch, ResearchBundle
    records = [evidence.model_copy(update={'evidence_id':uuid4()}) for _ in range(13)]
    active = peak = calls = 0
    async def extract(_interpretation, research, _context):
        nonlocal active, peak, calls
        active += 1
        peak = max(peak, active)
        calls += 1
        try:
            await asyncio.sleep(.01)
            return ExtractionBatch()
        finally:
            active -= 1
    await extract_batches(extract, interpretation, ResearchBundle(evidence=records), context)
    assert peak == 2 and active == 0 and calls == 2
