"""Versioned HTTP inputs and frontend projections. No caller-supplied owner IDs."""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

CaseStatus = Literal["draft", "researching", "in_review", "pitch_sent", "closed", "closed_visit", "closed_no_interest", "on_hold"]
Selection = Literal["kept", "rejected", "none"]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CreateCase(Input):
    prompt: str = Field(min_length=1, max_length=50_000)
    profile_id: UUID | None = None
    run: bool = True


class StartRun(Input):
    input_id: UUID
    profile_id: UUID | None = None


class Message(Input):
    text: str = Field(min_length=1, max_length=50_000)
    expected_revision: int = Field(ge=0)
    kind: Literal["formatting", "focus", "identity"] = "focus"
    profile_id: UUID | None = None


class Answer(Input):
    input_id: UUID
    question_id: UUID
    answer: str = Field(min_length=1, max_length=10_000)


class ReportRequest(Input):
    pack_id: UUID
    expected_revision: int = Field(ge=0)
    instruction: str = Field(default="Create a concise cited draft", min_length=1, max_length=10_000)


class SetSelection(Input):
    selection: Selection
    expected_result_hash: str = Field(pattern=r"^[a-f0-9]{64}$")


class Review(Input):
    decision: Literal["accepted", "rejected"]
    expected_result_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_selection_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")


class Export(Input):
    result_id: UUID
    review_id: UUID
    expected_result_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_selection_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    format: Literal["pdf"] = "pdf"


class PatchCase(Input):
    expected_revision: int = Field(ge=0)
    status: CaseStatus | None = None
    current_revision_id: UUID | None = None
    on_hold: bool | None = None
    outcome: Literal["visit", "no_interest"] | None = None


class ActionStatus(Input):
    status: Literal["open", "asked", "done"]
    answer: str | None = Field(default=None, max_length=10000)


class CreateAction(Input):
    case_id: UUID
    question: str = Field(min_length=1, max_length=10000)
    ask_role: str = Field(min_length=1, max_length=200)


class CaseSummary(BaseModel):
    id: str
    companyLabel: str
    oneLineNeed: str
    status: CaseStatus
    createdAt: datetime
    updatedAt: datetime
    keptCount: int
    onHold: bool = False
    outcome: Literal["visit", "no_interest"] | None = None


class CitedText(BaseModel):
    text: str
    evidenceIds: list[str]


class ReasonEntry(BaseModel):
    id: str
    name: str
    institution: Literal["UniBE", "ARTORG", "DCB", "Other"]
    evidenceIds: list[str]
    role: str | None = None


class Reason(BaseModel):
    id: str
    category: Literal["people", "groups", "projects", "ideas"]
    headline: str
    line: CitedText
    entries: list[ReasonEntry]
    kind: Literal["direct", "idea"]
    fromLead: bool = False
    selection: Selection


class Evidence(BaseModel):
    id: str
    n: int
    label: str
    url: str
    title: str
    institution: Literal["UniBE", "ARTORG", "DCB", "Other"]
    fetchedAt: datetime
    sourceDate: datetime | None = None
    excerpt: str
    highlight: str | None = None
    relevance: str
    origin: Literal["corpus", "web"]
    reviewStatus: Literal["curated", "unreviewed"]


class Coverage(BaseModel):
    snapshotDate: datetime
    institutions: list[Literal["UniBE", "ARTORG", "DCB", "Other"]]
    limitations: list[str]
    resultKind: Literal["ok", "partial", "no_match", "out_of_scope", "source_failure"]


class BriefRevision(BaseModel):
    id: str
    version: int
    parentId: str | None = None
    createdAt: datetime
    changeNote: str
    changedReasonIds: list[str]
    company: dict
    reasons: list[Reason]
    openQuestions: list[str]
    similarCases: list[dict]
    trace: dict
    coverage: Coverage
    emptyMessage: str | None = None
    resultHash: str
    packId: str
    packHash: str


class FollowUp(BaseModel):
    id: str
    question: str
    choices: list[str]
    answer: str | None = None


class Turn(BaseModel):
    id: str
    role: Literal["operator", "agent"]
    text: str
    createdAt: datetime
    followUp: FollowUp | None = None


class CaseDetail(BaseModel):
    case: CaseSummary
    revisions: list[BriefRevision]
    currentRevisionId: str | None = None
    turns: list[Turn]
    evidence: dict[str, Evidence]
    revision: int
    inputId: str
    selectionHash: str | None = None
    currentRun: dict | None = None


class Accepted(BaseModel):
    schema_version: Literal["1"] = "1"
    case_id: UUID
    input_id: UUID
    run_id: UUID | None = None
    status_url: str | None = None


class RunView(BaseModel):
    schema_version: Literal["1"] = "1"
    case_id: UUID
    run_id: UUID
    input_id: UUID
    snapshot_id: UUID
    state: str
    status: Literal["queued", "running", "waiting_for_input", "succeeded", "failed", "cancelled", "superseded"]
    stage: Literal["interpreting", "searching", "validating", "drafting", "done"] | None = None
    step: str | None = None
    error_code: str | None = None
    failure_detail: dict = Field(default_factory=dict)
    result_id: UUID | None = None
    pack_id: UUID | None = None
    outcome: str | None = None
    limitations: list[str]
    questions: list[dict]


class OperationView(BaseModel):
    id: UUID
    status: Literal["pending", "running", "committed", "failed"]
    result: dict
    download_url: str | None = None
    export_id: UUID | None = None
    error_code: str | None = None
