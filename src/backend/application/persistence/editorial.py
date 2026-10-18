"""Editorial revisions and exports, bound to existing review/support gates."""
from uuid import UUID

from sqlalchemy import select, update

from backend.contracts.services import StaleRevision
from backend.data import schema as t
from backend.data.repositories.drafts import selection_hash

CASE_STATUSES = {"draft", "researching", "in_review", "pitch_sent", "closed_visit", "closed_no_interest", "on_hold"}


class Editorial:
    def select_reason(self, access, key, case_id, result_id, reason_key, body):
        def callback(c):
            self._result(c, access, case_id, result_id)
            digest = self.repositories(c)[1].select(access, result_id, reason_key, body["selection"],
                                                    expected_hash=body["expected_result_hash"])
            return {"result_id": str(result_id), "selection_hash": digest}
        return self.command(access, key, f"select:{result_id}:{reason_key}", body, callback)

    def review(self, access, key, case_id, result_id, body):
        def callback(c):
            self._result(c, access, case_id, result_id)
            review_id = self.repositories(c)[0].review(access, result_id,
                expected_hash=body["expected_result_hash"], decision=body["decision"],
                expected_selection_hash=body.get("expected_selection_hash"))
            return {"review_id": str(review_id), "result_id": str(result_id)}
        return self.command(access, key, f"review:{result_id}", body, callback)

    def _result(self, c, access, case_id, result_id):
        self.case(c, access, case_id)
        result = c.execute(select(t.results).where(t.results.c.result_id == result_id,
                                                  t.results.c.case_id == case_id)).mappings().one()
        self.repositories(c)[0]._validate_pack(c, result["pack_id"])
        return result

    def patch_case(self, access, key, case_id, body):
        def callback(c):
            case = self.case(c, access, case_id)
            if body["expected_revision"] != case["revision"]:
                raise StaleRevision()
            values = {"revision": case["revision"] + 1}
            if body.get("status"):
                if body["status"] not in CASE_STATUSES:
                    raise ValueError("invalid case status")
                values["status"] = "ready_for_review" if body["status"] == "in_review" else body["status"]
            if body.get("current_revision_id"):
                result_id = UUID(body["current_revision_id"])
                result = self._result(c, access, case_id, result_id)
                pack = c.execute(select(t.packs).where(t.packs.c.pack_id == result["pack_id"])).mappings().one()
                if pack["input_id"] != case["current_input_id"]:
                    raise StaleRevision()
                values["current_result_id"] = result_id
                c.execute(update(t.exports).where(t.exports.c.result_id.in_(select(t.results.c.result_id).where(
                    t.results.c.case_id == case_id)), t.exports.c.status == "ready").values(status="stale"))
            c.execute(update(t.cases).where(t.cases.c.case_id == case_id).values(**values))
            return {"case_id": str(case_id), "revision": values["revision"]}
        return self.command(access, key, f"patch:{case_id}", body, callback)

    def actions(self, access):
        with self.session(access) as c:
            return [{"id": str(row["action_id"]), "caseId": str(row["case_id"]), "question": row["question"],
                "askRole": row["ask_role"], "status": row["status"]} for row in c.execute(select(t.action_items)
                .join(t.cases).where(t.cases.c.owner_id == access.principal_id, t.cases.c.namespace == access.namespace)
                .order_by(t.action_items.c.created_at, t.action_items.c.action_id)).mappings()]

    def action_status(self, access, key, action_id, body):
        def callback(c):
            action = c.execute(select(t.action_items).where(t.action_items.c.action_id == action_id)).mappings().one()
            self.case(c, access, action["case_id"])
            self.repositories(c)[1].set_action_status(access, action_id, body["status"])
            return {"id": str(action_id), "status": body["status"]}
        return self.command(access, key, f"action:{action_id}", body, callback)

    def selection_state(self, access, case_id, result_id):
        with self.session(access) as c:
            self._result(c, access, case_id, result_id)
            return selection_hash(c, result_id)
