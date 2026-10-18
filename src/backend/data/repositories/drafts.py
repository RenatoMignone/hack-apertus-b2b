"""Immutable draft cards and mutable editorial choices, independent of claim truth."""
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import insert, select, update

from backend.contracts.data import configuration_hash
from backend.contracts.pipeline import DraftAssessment, DraftRevision, ReportEvidencePack
from backend.data import schema as t
from backend.data.database import transaction
from backend.data.repositories.cases import CaseRepository


def selection_hash(connection, result_id, *, require_complete=False):
    rows = connection.execute(select(t.reasons.c.reason_row_id, t.reason_selections.c.selection).outerjoin(
        t.reason_selections).where(t.reasons.c.result_id == result_id).order_by(t.reasons.c.reason_key)).all()
    if require_complete and (not rows or any(row.selection not in {"kept", "rejected"} for row in rows)
                             or not any(row.selection == "kept" for row in rows)):
        raise ValueError("review all reason cards and keep at least one before approval/export")
    return configuration_hash({"selections": [[str(row.reason_row_id), row.selection or "none"] for row in rows]})


class DraftRepository:
    def __init__(self, engine):
        self.engine = engine
        self.cases = CaseRepository(engine)

    def create(self, access, case_id, pack_id, draft: DraftRevision, *, expected_revision, assessment: DraftAssessment, parent_id=None):
        with transaction(self.engine, access) as connection:
            case = self.cases._case(connection, access, case_id)
            if case["revision"] != expected_revision:
                raise ValueError("stale result revision")
            stored = connection.execute(select(t.packs).where(t.packs.c.pack_id == pack_id)).mappings().one()
            run = self.cases._run(connection, access, stored["run_id"])
            if run["case_id"] != case_id or stored["input_id"] != case["current_input_id"]:
                raise ValueError("pack belongs to another case/input")
            self.cases._validate_pack(connection, pack_id)
            pack = ReportEvidencePack.model_validate(stored["payload"])
            claims = {claim.claim_id: claim for claim in pack.claims}
            if pack.outcome == "no_match" and draft.reasons:
                raise ValueError("no-match pack cannot have reasons")
            if pack.claims and not draft.reasons:
                raise ValueError("supported pack requires draft reasons")
            previous = {}
            if parent_id:
                parent = connection.execute(select(t.results).where(t.results.c.result_id == parent_id)).mappings().one()
                if parent["case_id"] != case_id:
                    raise ValueError("parent belongs to another case")
                previous = {row["reason_key"]: row for row in connection.execute(
                    select(t.reasons, t.reason_selections.c.selection).outerjoin(t.reason_selections).where(
                    t.reasons.c.result_id == parent_id)).mappings()}
            body = draft.model_dump(mode="json")
            if assessment.status != "supported" or assessment.draft_hash != configuration_hash(body):
                raise ValueError("draft requires supported assessment of exact wording and citations")
            body["validation"] = assessment.model_dump(mode="json")
            result_id = uuid4()
            connection.execute(insert(t.results).values(result_id=result_id, case_id=case_id, pack_id=pack_id,
                parent_id=parent_id, instruction=draft.change_note, payload=body, result_hash=configuration_hash(body)))
            for reason in draft.reasons:
                if not set(reason.claim_ids) <= claims.keys():
                    raise ValueError("reason claims must resolve in frozen pack")
                digest = reason.support_hash(claims)
                old = previous.get(reason.id)
                choice = old["selection"] if old and old["support_hash"] == digest else "none"
                reason_row_id = uuid4()
                connection.execute(insert(t.reasons).values(reason_row_id=reason_row_id, result_id=result_id,
                    reason_key=reason.id, support_hash=digest, payload=reason.model_dump(mode="json")))
                for claim_id in set(reason.claim_ids):
                    connection.execute(insert(t.reason_claims).values(reason_row_id=reason_row_id, claim_id=claim_id))
                connection.execute(insert(t.reason_selections).values(reason_row_id=reason_row_id,
                    selection=choice or "none", reviewer_id=access.principal_id))
            connection.execute(update(t.cases).where(t.cases.c.case_id == case_id).values(
                current_result_id=result_id, revision=expected_revision + 1, status="ready_for_review"))
            connection.execute(update(t.exports).where(t.exports.c.result_id.in_(select(t.results.c.result_id).where(
                t.results.c.case_id == case_id)), t.exports.c.status == "ready").values(status="stale"))
            return result_id

    def select(self, access, result_id, reason_key, selection, *, expected_hash):
        if selection not in {"none", "kept", "rejected"}:
            raise ValueError("invalid editorial selection")
        with transaction(self.engine, access) as connection:
            result = connection.execute(select(t.results).where(t.results.c.result_id == result_id)).mappings().one()
            case = self.cases._case(connection, access, result["case_id"])
            self.cases._validate_pack(connection, result["pack_id"])
            if case["current_result_id"] != result_id or result["result_hash"] != expected_hash:
                raise ValueError("selection requires exact current revision")
            reason_id = connection.execute(select(t.reasons.c.reason_row_id).where(
                t.reasons.c.result_id == result_id, t.reasons.c.reason_key == reason_key)).scalar_one()
            connection.execute(update(t.reason_selections).where(t.reason_selections.c.reason_row_id == reason_id).values(
                selection=selection, reviewer_id=access.principal_id, updated_at=datetime.now(timezone.utc)))
            connection.execute(update(t.exports).where(t.exports.c.result_id == result_id,
                t.exports.c.status == "ready").values(status="stale"))
            return selection_hash(connection, result_id)

    def action(self, access, case_id, question, ask_role):
        if not question.strip() or not ask_role.strip():
            raise ValueError("action needs question and colleague role")
        with transaction(self.engine, access) as connection:
            self.cases._case(connection, access, case_id)
            key = uuid4()
            connection.execute(insert(t.action_items).values(action_id=key, case_id=case_id,
                question=question, ask_role=ask_role))
            return key

    def set_action_status(self, access, action_id, status):
        if status not in {"open", "asked", "done"}:
            raise ValueError("invalid action status")
        with transaction(self.engine, access) as connection:
            action = connection.execute(select(t.action_items).where(t.action_items.c.action_id == action_id)).mappings().one()
            self.cases._case(connection, access, action["case_id"])
            connection.execute(update(t.action_items).where(t.action_items.c.action_id == action_id).values(status=status))
