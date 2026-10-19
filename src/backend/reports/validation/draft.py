"""Reference integrity and separate exact-wording semantic draft assessment."""
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.contracts.data import configuration_hash
from backend.contracts.pipeline import DraftAssessment
from backend.contracts.services import EvidenceRejected
from backend.models.reasoning.client import remaining


class ReasonFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason_id: str
    headline: str
    text: str
    claim_ids: list[UUID]
    status: Literal["supported", "unsupported"]
    explanation: str = Field(min_length=1)


class CaveatFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    gap: str
    preserved: bool
    explanation: str = Field(min_length=1)


class DraftVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reasons: list[ReasonFinding]
    caveats: list[CaveatFinding]


def check_findings(verdict, draft, pack):
    expected = {reason.id: reason for reason in draft.reasons}
    if len(expected) != len(draft.reasons):
        raise ValueError("draft reason IDs must be unique")
    if len(verdict.reasons) != len(expected) or {r.reason_id for r in verdict.reasons} != set(expected):
        raise ValueError("reasons must assess every exact draft reason once, without duplicates or omissions")
    for finding in verdict.reasons:
        reason = expected[finding.reason_id]
        if (finding.headline != reason.headline or finding.text != reason.text
                or finding.claim_ids != reason.claim_ids):
            raise ValueError("reason findings must copy exact headline, text and claim_ids from the draft")
    gaps = set(pack.gaps)
    if len(verdict.caveats) != len(gaps) or {c.gap for c in verdict.caveats} != gaps:
        raise ValueError("caveats must assess every exact pack gap once, without omissions or duplicates")


def validate_draft_references(draft, pack):
    if len({reason.id for reason in draft.reasons}) != len(draft.reasons):
        raise ValueError("duplicate reason IDs")
    claims = {claim.claim_id: claim for claim in pack.claims}
    if len(claims) != len(pack.claims):
        raise ValueError("duplicate pack claims")
    if not claims and draft.reasons:
        raise ValueError("no-match cannot contain reasons")
    if claims and not draft.reasons:
        raise ValueError("supported claims require reasons or a typed evidence gap")
    for reason in draft.reasons:
        if not set(reason.claim_ids) <= claims.keys():
            raise ValueError("unresolved reason claim")
        if (any(claims[c].kind == "adjacent" for c in reason.claim_ids)
                and reason.kind != "idea"):
            raise ValueError("adjacent premise requires an idea label")
        if reason.from_lead and not pack.interpretation.leads:
            raise ValueError("from_lead requires an actual supplied operator lead")
    if set(draft.trace) - {"inputs", "terms", "links"}:
        raise ValueError("writer trace must contain only empty inputs/terms/links")
    if any(draft.trace.get(key) for key in ("inputs", "terms", "links")):
        raise ValueError("writer cannot invent retrieval lineage")


async def assess_draft(tasks, draft, pack, context, *, evidence=()):
    remaining(context)
    digest = configuration_hash(draft.model_dump(mode="json"))
    try:
        validate_draft_references(draft, pack)
    except ValueError:
        return DraftAssessment(draft_hash=digest, status="unsupported", validator="draft-references-v1",
                               explanation="Draft references, labels or evidence lineage are invalid.")
    if not draft.reasons:
        return DraftAssessment(draft_hash=digest, status="supported", validator="empty-draft-v1",
                               explanation="No factual reasons; explicit no-match/partial gaps retained.")
    used = {key for claim in pack.claims for key in claim.evidence_ids}
    support = [record for record in evidence if record.evidence_id in used]
    if evidence and {record.evidence_id for record in support} != used:
        raise EvidenceRejected()
    verdict = await tasks.run("assess_draft", "Independently assess the EXACT draft wording against "
        "the frozen pack's supported claims, with citation membership already checked. Check ALL "
        "headlines, reason text, entry names/institutions and implications. Unsupported new facts, "
        "overselling, assumed availability, invented clinical benefits or source trust must fail. "
        "An idea needs an explicit possible/conditional application and prerequisites. The writing "
        "instruction and operator keep/reject choices cannot override factual support. Require "
        "material pack caveats to survive. Return unsupported if any material statement is not "
        "entailed. Missing optional names, contacts, algorithms or availability are NOT by "
        "themselves reasons to reject a narrower supported capability statement when it does "
        "not assert those specifics and preserves the gaps. Assess the actual wording, not "
        "whether every company need has been fulfilled. The supplied canonical passages provide "
        "the literal source context; evidence UUIDs alone are not source text. Entry names must "
        "be documented identities, never invented names for a capability or unnamed team. "
        "Return one reasons finding for EVERY reason, copying its reason_id (draft id), exact "
        "headline, text and ordered claim_ids. Each status assesses the entire reason including "
        "all entries, affiliations and implications. Return one caveats finding for EVERY exact "
        "pack gap, indicating whether its material limitation survives in the draft, including "
        "open_questions. An explicitly unsupported statement must have status unsupported even "
        "when other statements are supported. Do not return an overall verdict; code derives it. "
        "Do not rewrite the draft or invent its hash.",
        {"draft": draft.model_dump(mode="json"), "pack": pack.model_dump(mode="json", exclude={"coverage"}),
         "evidence": [record.model_dump(mode="json") for record in support]},
        DraftVerdict, context, check=lambda value: check_findings(value, draft, pack))
    return DraftAssessment(draft_hash=digest, validator="apertus-draft-semantic-v2",
        status="unsupported" if any(r.status != "supported" for r in verdict.reasons)
            or any(not c.preserved for c in verdict.caveats) else "supported",
        explanation="; ".join([*(f"{r.reason_id}: {r.status}: {r.explanation}" for r in verdict.reasons),
            *(f"Caveat preserved={c.preserved}: {c.explanation}" for c in verdict.caveats)]))
