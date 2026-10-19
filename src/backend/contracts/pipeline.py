"""Typed case-processing boundaries; no model, scraper or HTTP implementation."""
from datetime import datetime
from enum import StrEnum
from typing import Literal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import UUID

from pydantic import Field, model_validator

from backend.contracts.data import Contract, configuration_hash, content_hash


class CompanyField(StrEnum):
    MEDTECH = "medtech"
    BIOTECHNOLOGY = "biotechnology"
    PHARMACEUTICALS = "pharmaceuticals"
    DIGITAL_HEALTH = "digital_health"
    HEALTHCARE_SERVICES = "healthcare_services"
    OTHER = "other"
    UNKNOWN = "unknown"


class CaseInterpretation(Contract):
    company_name: str | None = None
    company_summary: str = Field(min_length=1)
    primary_field: CompanyField = CompanyField.UNKNOWN
    additional_fields: list[CompanyField] = Field(default_factory=list)
    activity_label: str = Field(min_length=1, pattern=r"^\S+(?:\s+\S+){0,2}$",
        description="One to three words only, e.g. glucose sensors or insulin pumps. Put longer technical detail in needs/company_summary.")
    bern_intents: list[str] = Field(default_factory=list)
    needs: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)
    search_terms: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    leads: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)
    research_questions: list[str] = Field(default_factory=list)
    blocking_questions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_interpretation(self):
        if not 1 <= len(self.activity_label.split()) <= 3:
            raise ValueError("activity label must contain at most three words")
        if (not self.needs or not self.bern_intents or self.ambiguities) and not self.blocking_questions:
            raise ValueError("missing need/intent or material ambiguity needs a targeted question")
        return self


def canonical_url(url: str) -> str:
    """Conservative identity normalization; network/redirect safety is a future fetch adapter."""
    parts = urlsplit(url.strip())
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname or parts.username or parts.password:
        raise ValueError("public HTTP(S) URL without credentials required")
    host = parts.hostname.lower().encode("idna").decode()
    if ":" in host:
        host = f"[{host}]"
    port = parts.port
    if port and (parts.scheme.lower(), port) not in {("http", 80), ("https", 443)}:
        host += f":{port}"
    query = [(key, val) for key, val in parse_qsl(parts.query, keep_blank_values=True)
             if not key.lower().startswith("utm_") and key.lower() not in {"gclid", "fbclid"}]
    return urlunsplit((parts.scheme.lower(), host, parts.path or "/", urlencode(query), ""))


class FetchedSource(Contract):
    title: str = Field(min_length=1)
    url: str
    canonical_url: str
    content: str = Field(min_length=1)
    fetched_at: datetime
    published_at: datetime | None = None
    content_hash: str
    origin: Literal["web"] = "web"
    review_status: Literal["unreviewed"] = "unreviewed"

    @model_validator(mode="after")
    def validate_source(self):
        canonical_url(self.url)
        if self.canonical_url != canonical_url(self.canonical_url):
            raise ValueError("canonical URL is not normalized")
        if self.content_hash != content_hash(self.content.encode()):
            raise ValueError("source content hash mismatch")
        if self.fetched_at.tzinfo is None or (self.published_at and self.published_at.tzinfo is None):
            raise ValueError("source dates must be timezone-aware")
        return self


class ClaimAssessment(Contract):
    claim_id: UUID
    evidence_ids: list[UUID] = Field(min_length=1)
    status: Literal["supported", "unsupported", "contradicted"]
    statement: str = Field(min_length=1)
    validator: str = Field(min_length=1)
    explanation: str = Field(min_length=1)


class SupportedClaim(Contract):
    claim_id: UUID
    text: str = Field(min_length=1)
    evidence_ids: list[UUID] = Field(min_length=1)
    kind: Literal["direct", "adjacent"] = "direct"


class ReportEvidencePack(Contract):
    schema_version: Literal[2] = 2
    interpretation: CaseInterpretation
    claims: list[SupportedClaim] = Field(default_factory=list)
    matches: list[dict] = Field(default_factory=list)
    arguments: list[dict] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    actions: list[dict] = Field(default_factory=list)
    coverage: dict = Field(default_factory=dict)
    outcome: Literal["complete", "partial", "no_match"]
    # Authoritative run/input/snapshot/profile/model pins are stored on the run,
    # and added to the manifest/hash by persistence, never supplied by the model.
    @model_validator(mode="after")
    def validate_pack(self):
        ids = [claim.claim_id for claim in self.claims]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate pack claim")
        if self.interpretation.blocking_questions:
            raise ValueError("blocking clarification must be resolved before freezing a pack")
        if not self.claims and (self.outcome == "complete" or not self.gaps):
            raise ValueError("empty pack needs explicit partial/no-match limitations")
        return self


class ReasonEntry(Contract):
    id: str
    name: str
    institution: Literal["UniBE", "ARTORG", "DCB", "Other"]
    claim_ids: list[UUID] = Field(min_length=1)


class DraftReason(Contract):
    id: str = Field(min_length=1)
    headline: str = Field(min_length=1)
    text: str = Field(min_length=1)
    claim_ids: list[UUID] = Field(min_length=1)
    entries: list[ReasonEntry] = Field(default_factory=list)
    kind: Literal["direct", "idea"] = "direct"
    from_lead: bool = False

    @model_validator(mode="after")
    def validate_entries(self):
        if any(not set(entry.claim_ids) <= set(self.claim_ids) for entry in self.entries):
            raise ValueError("entry support must be contained in reason claims")
        return self

    def support_hash(self, claims: dict[UUID, SupportedClaim]) -> str:
        return configuration_hash({"reason": self.model_dump(mode="json"), "support": [
            claims[key].model_dump(mode="json") for key in sorted(set(self.claim_ids), key=str)]})


class DraftAssessment(Contract):
    draft_hash: str
    status: Literal["supported", "unsupported"]
    validator: str = Field(min_length=1)
    explanation: str = Field(min_length=1)


class DraftRevision(Contract):
    schema_version: Literal[2] = 2
    reasons: list[DraftReason]
    open_questions: list[str] = Field(default_factory=list)
    trace: dict = Field(default_factory=lambda: {"inputs": [], "terms": [], "links": []})
    change_note: str = "Initial draft"

    @model_validator(mode="after")
    def unique_reasons(self):
        if len({reason.id for reason in self.reasons}) != len(self.reasons):
            raise ValueError("duplicate reason ID")
        return self


Selection = Literal["kept", "rejected", "none"]


class ExportRequest(Contract):
    result_id: UUID
    review_id: UUID
    expected_result_hash: str
    expected_selection_hash: str
    format: Literal["pdf"] = "pdf"
