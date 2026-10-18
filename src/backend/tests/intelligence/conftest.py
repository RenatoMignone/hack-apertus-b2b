from datetime import datetime, timedelta, timezone
from uuid import NAMESPACE_DNS, uuid5

import pytest

from backend.contracts.data import AccessContext
from backend.contracts.pipeline import CaseInterpretation, DraftReason, DraftRevision, SupportedClaim
from backend.contracts.services import EvidenceRecord, PdfInput, RunContext


def ident(name):
    return uuid5(NAMESPACE_DNS, "intelligence-fixture.invalid/" + name)


@pytest.fixture
def context():
    return RunContext(access=AccessContext(principal_id=ident("principal"), namespace="test_intelligence"),
        case_id=ident("case"), input_id=ident("input"), run_id=ident("run"),
        snapshot_id=ident("snapshot"), profile_id=ident("profile"), taxonomy_version_id=ident("taxonomy"),
        build_id=ident("build"), embedding_config_hash="fixture-space", mode="connected",
        deadline_at=datetime.now(timezone.utc) + timedelta(minutes=5), request_id="fixture-request")


@pytest.fixture
def interpretation():
    return CaseInterpretation(company_summary="Operator describes a sensor company.",
        activity_label="Glucose sensors", primary_field="medtech", bern_intents=["Research collaboration"],
        needs=["Glucose sensor development"], search_terms=["glucose sensors"])


@pytest.fixture
def evidence():
    text = "Example Laboratory develops glucose sensors. No clinical approval or partnership is stated."
    return EvidenceRecord(evidence_id=ident("evidence"), document_version_id=ident("version"),
        scope_id=ident("scope"), title="Synthetic laboratory fixture", url="https://fixture.invalid/research",
        language="en", body_hash="a" * 64, char_start=0, char_end=len(text), literal_text=text,
        fetched_at=datetime(2026, 10, 18, tzinfo=timezone.utc), origin="web", review_status="unreviewed")


@pytest.fixture
def claim(evidence):
    return SupportedClaim(claim_id=ident("claim"), text="Example Laboratory develops glucose sensors.",
                          evidence_ids=[evidence.evidence_id])


@pytest.fixture
def pdf_input(evidence, claim):
    draft = DraftRevision(reasons=[DraftReason(id="kept", headline="Sensor development expertise",
        text="Example Laboratory develops glucose sensors.", claim_ids=[claim.claim_id]),
        DraftReason(id="rejected", headline="REJECTED MUST NOT APPEAR", text="Editorially excluded.",
                    claim_ids=[claim.claim_id])], open_questions=["Expert availability remains unknown."])
    return PdfInput(result_id=ident("result"), review_id=ident("review"), result_hash="b" * 64,
        selection_hash="c" * 64, draft=draft, claims=[claim], kept_reason_keys=["kept"], evidence=[evidence],
        limitations=["Synthetic fixture; no actual expertise claim."], template_version="challenge-v1")
