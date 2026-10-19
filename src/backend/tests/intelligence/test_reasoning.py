import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from backend.contracts.data import configuration_hash
from backend.contracts.pipeline import ClaimAssessment, ReportEvidencePack
from backend.contracts.services import (BudgetExceeded, EvidenceAssessment, EvidenceRejected,
    InvalidModelOutput, PersistedClaims, ResearchBundle)
from backend.evidence import create_reasoning_services
from backend.models.reasoning.fixtures import FixtureChatModel, draft_findings


def run(awaitable):
    return asyncio.run(awaitable)


def services(*responses):
    model = FixtureChatModel(responses=list(responses))
    return create_reasoning_services(model=model), model


def decision(claim, status="supported"):
    return {"decisions": [{"claim_id": str(claim.claim_id), "status": status,
                          "explanation": "Literal fixture supports this statement."}], "gaps": []}


def assessment(claim, status="supported"):
    return EvidenceAssessment(assessments=[ClaimAssessment(claim_id=claim.claim_id,
        statement=claim.text, evidence_ids=claim.evidence_ids, status=status,
        validator="explicit-test", explanation="Synthetic assessment fixture.")])


def fit(claim):
    return {"matches": [{"need_index": 0, "claim_ids": [str(claim.claim_id)],
        "rationale": "Sensor capability addresses sensor development.", "kind": "direct",
        "potential_benefit": "Could support research if collaboration is agreed.",
        "prerequisites": ["Confirm suitability and availability."]}], "gaps": []}


def test_interpret_preserves_negation_and_unknown_company(context, interpretation):
    service, model = services(interpretation.model_dump(mode="json"))
    result = run(service.interpret("We need sensor R&D in Bern.\nExclude animal testing.", {}, context))
    assert result.company_name is None
    assert "Exclude animal testing." in result.constraints
    assert not result.blocking_questions
    assert len(model.calls) == 1


def test_empty_request_asks_without_model(context):
    service, model = services()
    assert run(service.interpret(" ", {}, context)).blocking_questions
    assert not model.calls


def test_one_repair_only_and_unknown_taxonomy_rejected(context, interpretation):
    value = interpretation.model_dump(mode="json")
    value["concepts"] = ["invented-concept"]
    service, model = services(value, value, value)
    with pytest.raises(InvalidModelOutput):
        run(service.interpret("Find sensors in Bern", {"concepts": []}, context))
    assert len(model.calls) == 2


def test_malformed_json_repaired(context, interpretation):
    service, model = services("not JSON", interpretation.model_dump(mode="json"))
    assert run(service.interpret("Find sensor R&D in Bern", {}, context)).needs
    assert len(model.calls) == 2


def test_material_ambiguity_requires_question(context, interpretation):
    value = interpretation.model_dump(mode="json")
    value["ambiguities"] = ["Sensor development or clinical validation?"]
    repaired = {**value, "blocking_questions": ["Which capability are you seeking?"]}
    service, model = services(value, repaired)
    assert run(service.interpret("Sensors", {}, context)).blocking_questions
    repair = model.calls[1][-1].content
    assert "blocking_questions:" in repair and "Preserve unresolved ambiguities" in repair


def test_extract_uses_local_keys_and_literal_evidence(context, interpretation, evidence):
    batch = {"entities": [{"key": "e1", "entity_type": "unit", "display_label": "Example Laboratory",
        "evidence_ids": [str(evidence.evidence_id)]}], "claims": [{"key": "c1", "subject_key": "e1",
        "predicate": "develops", "typed_literal": {"type": "string", "value": "glucose sensors"},
        "statement": "Example Laboratory develops glucose sensors.",
        "evidence_ids": [str(evidence.evidence_id)]}], "gaps": []}
    service, _ = services(batch)
    result = run(service.extract(interpretation, ResearchBundle(evidence=[evidence]), context))
    assert result.claims[0].subject_key == "e1"
    assert result.entities[0].existing_entity_id is None


def test_extraction_rejects_invented_entity_label(context, interpretation, evidence):
    bad = {"entities": [{"key": "e1", "entity_type": "person", "display_label": "Invented Professor",
                        "evidence_ids": [str(evidence.evidence_id)]}], "claims": [], "gaps": []}
    service, _ = services(bad, bad)
    with pytest.raises(InvalidModelOutput):
        run(service.extract(interpretation, ResearchBundle(evidence=[evidence]), context))


@pytest.mark.parametrize("status", ["supported", "unsupported", "contradicted"])
def test_semantic_assessment_preserves_exact_statement_and_ids(context, claim, evidence, status):
    service, _ = services(decision(claim, status))
    result = run(service.assess(PersistedClaims(claims=[claim]), [evidence], context))
    assert result.assessments[0].statement == claim.text
    assert result.assessments[0].evidence_ids == claim.evidence_ids
    assert result.assessments[0].status == status


def test_missing_evidence_is_unsupported_without_model(context, claim):
    service, model = services()
    result = run(service.assess(PersistedClaims(claims=[claim]), [], context))
    assert result.assessments[0].status == "unsupported"
    assert not model.calls


def test_supported_pack_proposal_checks_fit_and_keeps_source_flags(context, interpretation, claim, evidence):
    service, _ = services(fit(claim))
    pack = run(service.propose_pack(interpretation, PersistedClaims(claims=[claim]), assessment(claim),
        ResearchBundle(evidence=[evidence]), context))
    assert pack.claims == [claim] and pack.matches and pack.arguments
    assert pack.coverage["sources"][0]["review_status"] == "unreviewed"
    assert pack.outcome == "complete"


@pytest.mark.parametrize("status", ["unsupported", "contradicted"])
def test_bad_claims_never_enter_pack(context, interpretation, claim, evidence, status):
    service, model = services()
    pack = run(service.propose_pack(interpretation, PersistedClaims(claims=[claim]), assessment(claim,status),
        ResearchBundle(evidence=[evidence]), context))
    assert pack.outcome == "no_match" and pack.gaps and not pack.claims
    assert not model.calls


def test_assessment_of_different_statement_rejected(context, interpretation, claim, evidence):
    wrong = assessment(claim)
    wrong = wrong.model_copy(update={"assessments": [wrong.assessments[0].model_copy(
        update={"statement": "Invented clinical approval."})]})
    service, _ = services()
    with pytest.raises(EvidenceRejected):
        run(service.propose_pack(interpretation, PersistedClaims(claims=[claim]), wrong,
            ResearchBundle(evidence=[evidence]), context))


def test_no_fit_is_honest_no_match(context, interpretation, claim, evidence):
    service, _ = services({"matches": [], "gaps": ["Capability does not address the requested need."]})
    pack = run(service.propose_pack(interpretation, PersistedClaims(claims=[claim]), assessment(claim),
        ResearchBundle(evidence=[evidence]), context))
    assert not pack.claims and pack.outcome == "no_match"
    assert pack.coverage["fit_assessment"] == {
        "supported_claim_count": 1, "matched_claim_count": 0, "match_count": 0}
    assert any("relevance remains unresolved" in gap for gap in pack.gaps)
    assert any(gap.startswith("Fit assessment (assessed supported claims only;") for gap in pack.gaps)


def test_pack_only_drafting_and_exact_hash_assessment(context, interpretation, claim, pdf_input):
    pack = ReportEvidencePack(interpretation=interpretation, claims=[claim], outcome="complete",
                             gaps=["Confirm expert availability."])
    draft = pdf_input.draft.model_copy(deep=True)
    draft = draft.model_copy(update={"reasons": draft.reasons[:1]})
    service, model = services(draft.model_dump(mode="json"),
        draft_findings(draft.model_dump(mode="json"), pack.gaps))
    result = run(service.draft(pack, "Shorter", context))
    checked = run(service.assess_draft(result, pack, context))
    assert checked.draft_hash == configuration_hash(result.model_dump(mode="json"))
    assert "Confirm expert availability." in result.open_questions
    result = result.model_copy(update={"reasons": [result.reasons[0].model_copy(
        update={"text": result.reasons[0].text + " Changed."})]})
    assert checked.draft_hash != configuration_hash(result.model_dump(mode="json"))


def test_draft_kind_instructions_and_bounded_repair(context, interpretation, claim, pdf_input):
    pack = ReportEvidencePack(interpretation=interpretation, claims=[claim], outcome='complete')
    valid = pdf_input.draft.model_copy(update={'reasons': pdf_input.draft.reasons[:1]}).model_dump(mode='json')
    invalid = {**valid, 'reasons': [{**valid['reasons'][0], 'kind': 'documented'}]}
    service, model = services(invalid, valid)
    draft = run(service.draft(pack, 'Write report', context))
    assert draft.reasons[0].kind == 'direct'
    assert len(model.calls) == 2
    assert 'kind must be exactly direct or idea' in model.calls[0][0].content
    assert 'literal_error' in model.calls[1][-1].content


def test_invalid_draft_kind_is_never_silently_reclassified(context, interpretation, claim, pdf_input):
    pack = ReportEvidencePack(interpretation=interpretation, claims=[claim], outcome='complete')
    value = pdf_input.draft.model_copy(update={'reasons': pdf_input.draft.reasons[:1]}).model_dump(mode='json')
    value['reasons'][0]['kind'] = 'adjacent'
    service, model = services(value, value)
    with pytest.raises(InvalidModelOutput):
        run(service.draft(pack, 'Write report', context))
    assert len(model.calls) == 2


def test_invented_citations_fail_draft_check(context, interpretation, claim, pdf_input):
    pack = ReportEvidencePack(interpretation=interpretation, claims=[], gaps=["No evidence"], outcome="no_match")
    service, model = services()
    checked = run(service.assess_draft(pdf_input.draft, pack, context))
    assert checked.status == "unsupported" and not model.calls


def test_adjacent_claim_cannot_be_rendered_as_direct(context, interpretation, claim, pdf_input):
    claim = claim.model_copy(update={"kind": "adjacent"})
    pack = ReportEvidencePack(interpretation=interpretation, claims=[claim], outcome="partial", gaps=["Transfer unverified"])
    service, _ = services()
    assert run(service.assess_draft(pdf_input.draft, pack, context)).status == "unsupported"


def test_expired_task_does_not_call_model(context):
    service, model = services()
    expired = context.model_copy(update={"deadline_at": datetime.now(timezone.utc)-timedelta(seconds=1)})
    with pytest.raises(BudgetExceeded):
        run(service.interpret("Sensors", {}, expired))
    assert not model.calls


def test_missing_draft_support_returns_typed_gap(context,interpretation,claim):
    from backend.reports.generation.draft import DraftEvidenceGap
    pack=ReportEvidencePack(interpretation=interpretation,claims=[claim],outcome="partial",gaps=["Need more context."])
    service,model=services({"reasons":[],"open_questions":["Need more source detail."]})
    with pytest.raises(DraftEvidenceGap) as error:
        run(service.draft(pack,"Write report",context))
    assert error.value.gaps==("Need more source detail.",) and len(model.calls)==1


def test_no_match_draft_and_assessment_are_explicit_without_model(context,interpretation):
    pack=ReportEvidencePack(interpretation=interpretation,outcome="no_match",gaps=["No supported result."])
    service,model=services()
    draft=run(service.draft(pack,"Write report",context))
    checked=run(service.assess_draft(draft,pack,context))
    assert not draft.reasons and checked.status=="supported" and draft.open_questions
    assert not model.calls


def test_draft_overclaim_can_fail_semantic_assessment(context,interpretation,claim,pdf_input):
    pack=ReportEvidencePack(interpretation=interpretation,claims=[claim],outcome="complete")
    draft=pdf_input.draft.model_copy(update={"reasons":[pdf_input.draft.reasons[0].model_copy(
        update={"text":"This technology guarantees clinical success."})]})
    service,_=services(draft_findings(draft.model_dump(mode="json"), status="unsupported"))
    assert run(service.assess_draft(draft,pack,context)).status=="unsupported"


def test_writer_cannot_invent_operator_leads_or_trace(context,interpretation,claim,pdf_input):
    pack=ReportEvidencePack(interpretation=interpretation,claims=[claim],outcome="complete")
    for change in ({"trace":{"invented_path":"claim"}},
                   {"reasons":[pdf_input.draft.reasons[0].model_copy(update={"from_lead":True})]}):
        service,model=services()
        draft=pdf_input.draft.model_copy(update=change)
        assert run(service.assess_draft(draft,pack,context)).status=="unsupported"
        assert not model.calls


def test_duplicate_assessments_and_foreign_support_rejected(context,interpretation,claim,evidence):
    service,_=services()
    a=assessment(claim)
    duplicate=a.model_copy(update={"assessments":a.assessments*2})
    with pytest.raises(EvidenceRejected):
        run(service.propose_pack(interpretation,PersistedClaims(claims=[claim]),duplicate,
            ResearchBundle(evidence=[evidence]),context))


def test_supported_but_missing_canonical_evidence_cannot_enter_pack(context,interpretation,claim):
    service,model=services()
    pack=run(service.propose_pack(interpretation,PersistedClaims(claims=[claim]),assessment(claim),
        ResearchBundle(),context))
    assert not pack.claims and pack.outcome=="no_match" and not model.calls


def test_blocking_questions_prevent_extraction_or_pack(context,interpretation):
    blocked=interpretation.model_copy(update={"blocking_questions":["Which capability?"]})
    service,model=services()
    with pytest.raises(EvidenceRejected):
        run(service.extract(blocked,ResearchBundle(),context))
    with pytest.raises(EvidenceRejected):
        run(service.propose_pack(blocked,PersistedClaims(),EvidenceAssessment(),ResearchBundle(),context))
    assert not model.calls


@pytest.mark.parametrize('fault', ['omitted_reason', 'changed_text', 'foreign_claim', 'omitted_caveat'])
def test_draft_findings_require_exact_complete_coverage(context, interpretation, claim, pdf_input, fault):
    from copy import deepcopy
    pack = ReportEvidencePack(interpretation=interpretation, claims=[claim], outcome='partial', gaps=['Unknown availability'])
    draft = pdf_input.draft
    bad = draft_findings(draft.model_dump(mode='json'), pack.gaps)
    if fault == 'omitted_reason':
        bad['reasons'].pop()
    elif fault == 'changed_text':
        bad['reasons'][0]['text'] = 'Different wording'
    elif fault == 'foreign_claim':
        bad['reasons'][0]['claim_ids'] = []
    else:
        bad['caveats'] = []
    service, model = services(bad, deepcopy(bad))
    with pytest.raises(InvalidModelOutput):
        run(service.assess_draft(draft, pack, context))
    assert len(model.calls) == 2


def test_draft_failure_cannot_be_overridden_by_positive_explanation(context, interpretation, claim, pdf_input):
    pack = ReportEvidencePack(interpretation=interpretation, claims=[claim], outcome='partial', gaps=['Unknown availability'])
    findings = draft_findings(pdf_input.draft.model_dump(mode='json'), pack.gaps)
    findings['reasons'][0].update(status='unsupported', explanation='Everything is supported.')
    service, _ = services(findings)
    assert run(service.assess_draft(pdf_input.draft, pack, context)).status == 'unsupported'
    findings['reasons'][0]['status'] = 'supported'
    findings['caveats'][0]['preserved'] = False
    service, _ = services(findings)
    assert run(service.assess_draft(pdf_input.draft, pack, context)).status == 'unsupported'


def test_extraction_short_support_references_resolve_exact_ids(context, interpretation, evidence):
    response = {'entities': [{'key': 'e1', 'entity_type': 'unit', 'display_label': 'Example Laboratory',
                             'evidence_ids': ['S1']}], 'claims': [], 'gaps': []}
    service, model = services(response)
    result = run(service.extract(interpretation, ResearchBundle(evidence=[evidence]), context))
    assert result.entities[0].evidence_ids == [evidence.evidence_id]
    assert '"evidence_id":"S1"' in model.calls[0][-1].content


def test_extraction_unknown_support_alias_cannot_create_evidence(context, interpretation, evidence):
    response = {'entities': [{'key': 'e1', 'entity_type': 'unit', 'display_label': 'Example Laboratory',
                             'evidence_ids': ['S999']}], 'claims': [], 'gaps': []}
    service, _ = services(response, response)
    with pytest.raises(InvalidModelOutput):
        run(service.extract(interpretation, ResearchBundle(evidence=[evidence]), context))


def test_fit_short_claim_aliases_resolve_without_weakening_support(context, interpretation, claim, evidence):
    response = fit(claim)
    response['matches'][0]['claim_ids'] = ['C1']
    service, model = services(response)
    pack = run(service.propose_pack(interpretation, PersistedClaims(claims=[claim]), assessment(claim),
        ResearchBundle(evidence=[evidence]), context))
    assert pack.claims == [claim]
    assert pack.matches[0]['claim_ids'] == [str(claim.claim_id)]
    assert '"claim_id":"C1"' in model.calls[0][-1].content


def test_fit_unknown_claim_alias_is_repaired_with_targeted_diagnostic(context, interpretation, claim, evidence):
    bad = fit(claim)
    bad['matches'][0]['claim_ids'] = ['S1']
    service, model = services(bad, fit(claim))
    pack = run(service.propose_pack(interpretation, PersistedClaims(claims=[claim]), assessment(claim),
        ResearchBundle(evidence=[evidence]), context))
    assert pack.claims == [claim]
    assert 'never evidence IDs' in model.calls[1][-1].content
