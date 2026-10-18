"""Behavioral boundary fixtures; no live model or web requests."""
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from backend.contracts.data import content_hash
from backend.contracts.pipeline import (CaseInterpretation, DraftReason, FetchedSource,
                                        ReportEvidencePack, SupportedClaim, canonical_url)


def interpretation(**changes):
    return CaseInterpretation(company_summary="A public example makes insulin pumps.", activity_label="insulin pumps",
        needs=["closed-loop algorithms"], bern_intents=["R&D lab"], **changes)


def test_optional_name_and_multi_label_interpretation():
    parsed = interpretation(additional_fields=["medtech", "digital_health"])
    assert parsed.company_name is None
    assert not parsed.blocking_questions
    with pytest.raises(ValidationError, match="targeted question"):
        CaseInterpretation(company_summary="Unknown", activity_label="medical tools")
    waiting = CaseInterpretation(company_summary="Unknown", activity_label="medical tools",
        blocking_questions=["Which capability do you need?"])
    with pytest.raises(ValidationError, match="clarification"):
        ReportEvidencePack(interpretation=waiting, outcome="no_match", gaps=["Unknown intent"])


def test_source_identity_keeps_meaningful_queries_and_checks_content():
    assert canonical_url("HTTPS://EXAMPLE.ORG:443/page?utm_source=demo&id=2#top") == "https://example.org/page?id=2"
    assert canonical_url("https://example.org/?id=2") != canonical_url("https://example.org/?id=3")
    with pytest.raises(ValueError):
        canonical_url("file:///etc/passwd")
    body = "Literal source text"
    source = FetchedSource(title="Example", url="https://example.org", canonical_url="https://example.org/",
        content=body, content_hash=content_hash(body.encode()), fetched_at=datetime.now(timezone.utc))
    assert source.review_status == "unreviewed"
    with pytest.raises(ValidationError, match="hash"):
        FetchedSource.model_validate({**source.model_dump(), "content": "changed"})


def test_empty_pack_requires_honest_limitation_and_hash_covers_support():
    with pytest.raises(ValidationError, match="limitations"):
        ReportEvidencePack(interpretation=interpretation(), outcome="complete")
    assert ReportEvidencePack(interpretation=interpretation(), outcome="no_match", gaps=["No supported source"])
    key = uuid4()
    claim = SupportedClaim(claim_id=key, text="A supported statement", evidence_ids=[uuid4()])
    reason = DraftReason(id="a", headline="Bern capability", text="A plain explanation", claim_ids=[key])
    changed = claim.model_copy(update={"evidence_ids": [uuid4()]})
    assert reason.support_hash({key: claim}) != reason.support_hash({key: changed})


def test_frontend_projection_preserves_citations_and_new_source_flag():
    from backend.contracts.frontend import reason_view, web_evidence_view
    key, ev = uuid4(), uuid4()
    claim = SupportedClaim(claim_id=key, text="The lab studies glucose.", evidence_ids=[ev])
    reason = DraftReason(id="one", headline="Related work", text=claim.text, claim_ids=[key])
    view = reason_view(reason, {key: claim}, "rejected")
    assert view["line"]["evidenceIds"] == [str(ev)]
    assert view["selection"] == "rejected"
    source = FetchedSource(title="Research", url="https://example.org", canonical_url="https://example.org/",
        content=claim.text, content_hash=content_hash(claim.text.encode()), fetched_at=datetime.now(timezone.utc))
    evidence = web_evidence_view(source, evidence_id=ev, number=1, excerpt=claim.text, highlight="glucose",
        label="Research", relevance="Related capability")
    assert evidence["reviewStatus"] == "unreviewed"
    assert evidence["sourceDate"] is None
    with pytest.raises(ValueError, match="literal"):
        web_evidence_view(source, evidence_id=ev, number=1, excerpt="Invented", label="Research", relevance="No")
