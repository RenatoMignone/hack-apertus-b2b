"""Cross-lane protocol smoke checks; no infrastructure or provider credentials."""
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from backend.contracts.services import (ClaimCandidate, EntityCandidate, EvidenceRecord,
    ExtractionBatch, RunContext, ServiceUnavailable)
from backend.contracts.data import AccessContext


def test_context_roundtrip_and_deadline():
    ids = {key: uuid4() for key in ("case_id", "input_id", "run_id", "snapshot_id", "profile_id", "taxonomy_version_id", "build_id")}
    context = RunContext(access=AccessContext(principal_id=uuid4(), namespace="test"), **ids,
        embedding_config_hash="fixture", mode="offline", deadline_at=datetime.now(timezone.utc), request_id="test")
    assert RunContext.model_validate_json(context.model_dump_json()) == context
    with pytest.raises(ValidationError):
        RunContext(**{**context.model_dump(), "deadline_at": datetime.now()})
    with pytest.raises(ValidationError):
        RunContext(**{**context.model_dump(), "max_research_rounds": 4})


def test_extraction_references_and_object_xor():
    evidence = uuid4()
    entity = EntityCandidate(key="person", entity_type="person", display_label="Source name", evidence_ids=[evidence])
    claim = ClaimCandidate(key="role", subject_key="person", predicate="role", statement="Researcher",
        evidence_ids=[evidence], typed_literal={"type": "text", "value": "Researcher"})
    assert ExtractionBatch(entities=[entity], claims=[claim]).claims[0] == claim
    with pytest.raises(ValidationError):
        ExtractionBatch(entities=[], claims=[claim])
    with pytest.raises(ValidationError):
        ClaimCandidate(**{**claim.model_dump(), "object_key": "person"})


def test_literal_length_and_source_flags():
    fields = dict(evidence_id=uuid4(), document_version_id=uuid4(), scope_id=uuid4(), title="Profile",
        url="https://example.org/profile", language="en", body_hash="a" * 64, char_start=0, char_end=2,
        literal_text="éx", fetched_at=datetime.now(timezone.utc), origin="web", review_status="unreviewed")
    assert EvidenceRecord(**fields).char_end == 2
    with pytest.raises(ValidationError):
        EvidenceRecord(**{**fields, "char_end": 3})
    with pytest.raises(ValidationError):
        EvidenceRecord(**{**fields, "review_status": "curated"})


def test_safe_errors_do_not_accept_provider_payloads():
    error = ServiceUnavailable()
    assert error.retryable and error.code == "service_unavailable"
    with pytest.raises(TypeError):
        ServiceUnavailable("provider credential or response")
