"""Pure projections onto the existing React contract; transport wiring is separate."""
from backend.contracts.pipeline import DraftReason, FetchedSource


def reason_view(reason: DraftReason, claims: dict, selection="none") -> dict:
    """Resolve claims to evidence; never ask a model to invent citation links."""
    def evidence_ids(keys):
        return sorted({str(evidence) for key in keys for evidence in claims[key].evidence_ids})
    return {"id": reason.id, "headline": reason.headline,
            "line": {"text": reason.text, "evidenceIds": evidence_ids(reason.claim_ids)},
            "entries": [{"id": entry.id, "name": entry.name, "institution": entry.institution,
                         "evidenceIds": evidence_ids(entry.claim_ids)} for entry in reason.entries],
            "kind": reason.kind, "fromLead": reason.from_lead, "selection": selection}


def web_evidence_view(source: FetchedSource, *, evidence_id, number, excerpt, highlight=None,
                      label, relevance, institution="Other") -> dict:
    if excerpt not in source.content or (highlight and highlight not in excerpt):
        raise ValueError("frontend quotations/highlights must be literal source slices")
    return {"id": str(evidence_id), "n": number, "label": label, "url": source.canonical_url,
            "title": source.title, "institution": institution, "fetchedAt": source.fetched_at.isoformat(),
            "sourceDate": source.published_at.isoformat() if source.published_at else None,
            "excerpt": excerpt, "highlight": highlight, "relevance": relevance,
            "origin": source.origin, "reviewStatus": source.review_status}
