"""Version 1 in-process ports shared by runtime, intelligence and data lanes.

These are service boundaries, not persistence models or HTTP requests. Caller
identity, provenance and budgets are supplied by authorized application code.
"""
from datetime import datetime
from typing import Literal, Protocol, runtime_checkable
from uuid import UUID

from pydantic import Field, model_validator

from backend.contracts.data import AccessContext, Contract, EvidenceHit, QueryPlan
from backend.contracts.pipeline import (CaseInterpretation, ClaimAssessment, DraftAssessment,
    DraftRevision, FetchedSource, ReportEvidencePack, SupportedClaim, canonical_url)

CONTRACT_VERSION = "1"
EntityType = Literal["person", "unit", "organization", "project", "facility", "service"]
Digest = str


def _aware(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timezone-aware UTC-compatible date required")


class RunContext(Contract):
    access: AccessContext
    case_id: UUID
    input_id: UUID
    run_id: UUID
    snapshot_id: UUID
    profile_id: UUID
    taxonomy_version_id: UUID
    build_id: UUID
    embedding_config_hash: str = Field(min_length=1)
    mode: Literal["connected", "offline"]
    deadline_at: datetime
    max_research_rounds: int = Field(default=3, ge=1, le=3)
    max_output_tokens: int = Field(default=4096, gt=0)
    max_tool_calls: int = Field(default=6, ge=0)
    request_id: str = Field(min_length=1, max_length=128)

    @model_validator(mode="after")
    def aware_deadline(self):
        _aware(self.deadline_at)
        return self


class EvidenceRecord(Contract):
    evidence_id: UUID
    document_version_id: UUID
    scope_id: UUID
    title: str
    url: str
    language: str
    body_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    char_start: int = Field(ge=0)
    char_end: int = Field(gt=0)
    literal_text: str = Field(min_length=1)
    heading_path: list[str] = Field(default_factory=list)
    page: int | None = Field(default=None, ge=1)
    fetched_at: datetime
    published_at: datetime | None = None
    origin: Literal["corpus", "web"]
    review_status: Literal["curated", "unreviewed"]

    @model_validator(mode="after")
    def validate_record(self):
        canonical_url(self.url)
        _aware(self.fetched_at)
        if self.published_at:
            _aware(self.published_at)
        if self.char_end - self.char_start != len(self.literal_text):
            raise ValueError("evidence offsets must describe the literal Unicode slice")
        if self.origin == "web" and self.review_status != "unreviewed":
            raise ValueError("case-time web sources remain unreviewed")
        return self


class ResearchBundle(Contract):
    hits: list[EvidenceHit] = Field(default_factory=list)
    evidence: list[EvidenceRecord] = Field(default_factory=list)
    existing_entities: list[dict] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class EntityCandidate(Contract):
    key: str = Field(min_length=1)
    entity_type: EntityType
    display_label: str = Field(min_length=1)
    evidence_ids: list[UUID] = Field(min_length=1)
    existing_entity_id: UUID | None = None


class ClaimCandidate(Contract):
    key: str = Field(min_length=1)
    subject_key: str = Field(min_length=1)
    predicate: str = Field(min_length=1)
    object_key: str | None = None
    typed_literal: dict | None = None
    statement: str = Field(min_length=1)
    evidence_ids: list[UUID] = Field(min_length=1)
    kind: Literal["direct", "adjacent"] = "direct"

    @model_validator(mode="after")
    def one_object(self):
        if (self.object_key is None) == (self.typed_literal is None):
            raise ValueError("claim needs exactly one entity object or typed literal")
        if self.typed_literal is not None and not {"type", "value"} <= self.typed_literal.keys():
            raise ValueError("typed literal requires type and value")
        return self


class ExtractionBatch(Contract):
    entities: list[EntityCandidate] = Field(default_factory=list, max_length=30)
    claims: list[ClaimCandidate] = Field(default_factory=list, max_length=60)
    gaps: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def local_references(self):
        keys = {entity.key for entity in self.entities}
        if len(keys) != len(self.entities) or len({claim.key for claim in self.claims}) != len(self.claims):
            raise ValueError("extraction keys must be unique")
        if any(claim.subject_key not in keys or (claim.object_key is not None and claim.object_key not in keys)
               for claim in self.claims):
            raise ValueError("claim local entity references must resolve in its batch")
        return self


class PersistedClaims(Contract):
    claims: list[SupportedClaim] = Field(default_factory=list)
    entity_ids: dict[str, UUID] = Field(default_factory=dict)


class EvidenceAssessment(Contract):
    assessments: list[ClaimAssessment] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)


class WebResearchResult(Contract):
    status: Literal["completed", "unavailable", "failed"]
    sources: list[FetchedSource] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class RegisteredResearch(Contract):
    evidence: list[EvidenceRecord] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class PdfInput(Contract):
    result_id: UUID
    review_id: UUID
    result_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    selection_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    draft: DraftRevision
    interpretation: CaseInterpretation | None = None
    claims: list[SupportedClaim] = Field(default_factory=list)
    kept_reason_keys: list[str] = Field(min_length=1)
    evidence: list[EvidenceRecord]
    limitations: list[str] = Field(default_factory=list)
    template_version: str = Field(min_length=1)

    @model_validator(mode="after")
    def kept_reasons_resolve(self):
        keys = {reason.id for reason in self.draft.reasons}
        if len(set(self.kept_reason_keys)) != len(self.kept_reason_keys) or not set(self.kept_reason_keys) <= keys:
            raise ValueError("kept keys must be unique and present in the approved draft")
        return self


class ServiceError(Exception):
    code = "service_error"
    retryable = False
    public_message = "Service operation failed"

    def __init__(self):
        super().__init__(self.public_message)


class ServiceUnavailable(ServiceError):
    code = "service_unavailable"
    retryable = True
    public_message = "A required service is unavailable"


class BudgetExceeded(ServiceError):
    code = "budget_exceeded"
    public_message = "The operation reached its configured budget"


class InvalidModelOutput(ServiceError):
    code = "invalid_model_output"
    public_message = "The model did not produce valid supported output"


class EvidenceRejected(ServiceError):
    code = "evidence_rejected"
    public_message = "Evidence did not pass the required checks"


class StaleRevision(ServiceError):
    code = "stale_revision"
    public_message = "The case revision changed; reload before retrying"


@runtime_checkable
class ReasoningServices(Protocol):
    async def interpret(self, message: str, taxonomy_context: dict, context: RunContext) -> CaseInterpretation: ...
    async def extract(self, interpretation: CaseInterpretation, research: ResearchBundle, context: RunContext) -> ExtractionBatch: ...
    async def assess(self, claims: PersistedClaims, evidence: list[EvidenceRecord], context: RunContext) -> EvidenceAssessment: ...
    async def propose_pack(self, interpretation: CaseInterpretation, claims: PersistedClaims,
                           assessment: EvidenceAssessment, research: ResearchBundle, context: RunContext) -> ReportEvidencePack: ...
    async def draft(self, pack: ReportEvidencePack, instruction: str, context: RunContext) -> DraftRevision: ...
    async def assess_draft(self, draft: DraftRevision, pack: ReportEvidencePack, context: RunContext) -> DraftAssessment: ...


@runtime_checkable
class PdfRenderer(Protocol):
    async def render(self, report: PdfInput) -> bytes: ...


@runtime_checkable
class BackboneServices(Protocol):
    async def taxonomy(self, context: RunContext) -> dict: ...
    async def retrieve(self, plan: QueryPlan, context: RunContext) -> ResearchBundle: ...
    async def register_research(self, result: WebResearchResult, context: RunContext) -> RegisteredResearch: ...
    async def persist_extraction(self, batch: ExtractionBatch, context: RunContext) -> PersistedClaims: ...
    async def read_evidence(self, evidence_ids: list[UUID], context: RunContext) -> list[EvidenceRecord]: ...


@runtime_checkable
class WebResearchTools(Protocol):
    async def discover(self, query: str, context: RunContext) -> list[str]: ...
    async def fetch(self, urls: list[str], context: RunContext) -> WebResearchResult: ...
