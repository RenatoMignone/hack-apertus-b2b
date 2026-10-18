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


def evidence_view(record, number):
    return {"id": str(record.evidence_id), "n": number, "label": record.title, "url": record.url,
            "title": record.title, "institution": "Other", "fetchedAt": record.fetched_at.isoformat(),
            "sourceDate": record.published_at.isoformat() if record.published_at else None,
            "excerpt": record.literal_text, "highlight": record.literal_text,
            "relevance": "Source passage supporting the cited claim", "origin": record.origin,
            "reviewStatus": record.review_status}


def case_view(data, evidence):
    """Project actual stored records onto CaseDetail, retaining review hash extensions."""
    from backend.contracts.pipeline import DraftRevision, ReportEvidencePack
    from backend.contracts.presentation import public_limitations
    case = data["case"]
    interpretation = data["interpretation"]
    choices = {str(row["result_id"]) + ":" + row["reason_key"]: row["selection"] or "none" for row in data["reasons"]}
    current = str(case["current_result_id"]) if case["current_result_id"] else None
    revisions = []
    for version, row in enumerate(data["results"], 1):
        body = {k: v for k, v in row["payload"].items() if k != "validation"}
        draft = DraftRevision.model_validate(body)
        pack_row = data["packs"][str(row["pack_id"])]
        pack = ReportEvidencePack.model_validate(pack_row["payload"])
        claims = {claim.claim_id: claim for claim in pack.claims}
        reasons = []
        for reason in draft.reasons:
            view = reason_view(reason, claims, choices.get(str(row["result_id"]) + ":" + reason.id, "none"))
            types = [data.get("claim_types", {}).get(str(key)) for key in reason.claim_ids]
            primary = next((kind for kind in types if kind), None)
            view["category"] = "ideas" if reason.kind == "idea" else {"person": "people", "project": "projects"}.get(primary, "groups")
            reasons.append(view)
        revisions.append({"id": str(row["result_id"]), "version": version,
            "parentId": str(row["parent_id"]) if row["parent_id"] else None, "createdAt": row["created_at"].isoformat(),
            "changeNote": draft.change_note, "changedReasonIds": [r["id"] for r in reasons],
            "company": {"summary": pack.interpretation.company_summary, "facts": []},
            "reasons": reasons, "openQuestions": public_limitations(draft.open_questions), "similarCases": [], "trace": draft.trace,
            "coverage": {"snapshotDate": (pack_row.get("snapshot_date") or pack_row["created_at"]).isoformat(), "institutions": sorted({entry["institution"] for reason in reasons for entry in reason["entries"] if entry["institution"] != "Other"}),
                "limitations": public_limitations(pack.gaps), "resultKind": {"complete": "ok", "partial": "partial", "no_match": "no_match"}[pack.outcome]},
            "emptyMessage": "No supported match in the available sources" if pack.outcome == "no_match" else None,
            "resultHash": row["result_hash"], "packId": str(row["pack_id"]), "packHash": pack_row["pack_hash"]})
    status = {"ready_for_review": "in_review", "draft": "researching", "on_hold": "researching",
        "closed_visit": "closed", "closed_no_interest": "closed"}.get(case["status"], case["status"])
    if status not in {"researching", "in_review", "pitch_sent", "closed"}:
        status = "researching"
    summary = {"id": str(case["case_id"]), "companyLabel": interpretation.get("company_name") or "New case",
        "oneLineNeed": interpretation.get("company_summary") or "Research pending", "status": status,
        "onHold": case.get("on_hold", False) or case["status"] == "on_hold",
        "outcome": case.get("outcome") or (case["status"][7:] if case["status"].startswith("closed_") else None),
        "createdAt": case["created_at"].isoformat(),
        "updatedAt": (data["results"][-1]["created_at"] if data["results"] else case["created_at"]).isoformat(),
        "keptCount": sum(value == "kept" for key, value in choices.items() if current and key.startswith(current + ":"))}
    turns = [{"id": str(turn["turn_id"]), "role": "operator" if turn["role"] == "user" else "agent",
              "text": turn["message"], "createdAt": turn["created_at"].isoformat()} for turn in data["turns"]]
    # Questions have their own durable IDs; they are not invented assistant messages.
    for q in data["questions"]:
        turns.append({"id": str(q["question_id"]), "role": "agent", "text": q["reason"],
            "createdAt": q["created_at"].isoformat(), "followUp": {"id": str(q["question_id"]),
            "question": q["reason"], "choices": [], "answer": q.get("answer")}})
    turns.sort(key=lambda turn: (turn["createdAt"], turn["id"]))
    return {"case": summary, "revisions": revisions, "currentRevisionId": current, "turns": turns,
            "evidence": {str(record.evidence_id): evidence_view(record, n) for n, record in enumerate(evidence, 1)},
            "revision": case["revision"], "inputId": str(case["current_input_id"])}
