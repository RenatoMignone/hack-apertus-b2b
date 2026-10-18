"""Pack-only writing. No tools, source fetching, storage or factual acceptance."""
from backend.contracts.pipeline import DraftRevision
from backend.contracts.services import EvidenceRejected
from backend.models.reasoning.client import remaining
from backend.reports.validation.draft import validate_draft_references


class DraftEvidenceGap(EvidenceRejected):
    """A can route this shared-error subtype back to evidence preparation."""
    public_message = "More supporting evidence is needed before drafting"

    def __init__(self, gaps):
        super().__init__()
        self.gaps = tuple(gaps)


async def draft_report(tasks, pack, instruction, context):
    remaining(context)
    if pack.interpretation.blocking_questions:
        raise EvidenceRejected()
    if not pack.claims:
        return DraftRevision(reasons=[], open_questions=pack.gaps,
                             change_note="No supported matches in the supplied evidence pack.")
    def check(draft):
        if not draft.reasons:
            raise DraftEvidenceGap(draft.open_questions or ["No supported reason could be drafted."])
        validate_draft_references(draft, pack)
    draft = await tasks.run("draft", "Compose concise Why Bern reason cards using ONLY the frozen "
        "pack's supported claims. Every headline, line and entry is backed by claim_ids; entries "
        "use only a subset of their reason's claims. Do not invent names, roles, contacts, facts, "
        "numbers, clinical suitability or willingness. Use kind=idea for a possible adjacent "
        "application and explain prerequisites/uncertainty, not a proven capability. Keep company "
        "context attributed to the operator. Preserve exclusions. Do not remove material caveats "
        "even if requested. No browsing, tools or retrieval. Include the pack gaps in open_questions. "
        "Use short reason/entry keys; institution=Other unless the cited claim explicitly supports "
        "UniBE/ARTORG/DCB. from_lead MUST be false unless actual operator leads are supplied. "
        "Leave trace inputs/terms/links empty: code, not the writer, owns actual "
        "retrieval lineage. If claims cannot yield a supported reason, return no reasons and a gap.",
        {"pack": pack.model_dump(mode="json"), "editorial_instruction": instruction},
        DraftRevision, context, check=check)
    return DraftRevision.model_validate({**draft.model_dump(mode="json"), "open_questions":
        list(dict.fromkeys([*draft.open_questions, *pack.gaps])),
        "trace": {"inputs": [], "terms": [], "links": []}})
