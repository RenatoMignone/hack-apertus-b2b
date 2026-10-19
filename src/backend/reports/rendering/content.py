"""Common kept-only citation validation for deterministic export adapters."""
from backend.contracts.services import EvidenceRejected, PdfInput


def selected_content(report):
    try:
        report = PdfInput.model_validate(report.model_dump(mode='json'))
    except ValueError:
        raise EvidenceRejected() from None
    if len(report.model_dump_json()) > 180000:
        raise EvidenceRejected()
    records = {record.evidence_id: record for record in report.evidence}
    claims = {claim.claim_id: claim for claim in report.claims}
    if len(records) != len(report.evidence) or len(claims) != len(report.claims):
        raise EvidenceRejected()
    kept = [reason for reason in report.draft.reasons if reason.id in report.kept_reason_keys]
    if not kept or len(kept) != len(report.kept_reason_keys):
        raise EvidenceRejected()
    mapping = {key: claim.evidence_ids for key, claim in claims.items()}
    for reason in kept:
        for key in reason.claim_ids:
            if not mapping.get(key) or not set(mapping[key]) <= records.keys():
                raise EvidenceRejected()
            if claims[key].kind == 'adjacent' and reason.kind != 'idea':
                raise EvidenceRejected()
    ids = list(dict.fromkeys(e for reason in kept for key in reason.claim_ids for e in mapping[key]))
    return report, kept, [records[e] for e in ids], mapping
