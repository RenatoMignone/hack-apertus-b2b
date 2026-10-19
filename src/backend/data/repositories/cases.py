from uuid import uuid4

from sqlalchemy import insert, select, text, update

from backend.contracts.data import configuration_hash
from backend.data import schema as tables
from backend.data.database import transaction


class CaseRepository:
    def __init__(self, engine):
        self.engine = engine

    def _case(self, connection, access, case_id):
        row = connection.execute(select(tables.cases).where(tables.cases.c.case_id == case_id).with_for_update()).mappings().one()
        if row["owner_id"] != access.principal_id or row["namespace"] != access.namespace:
            raise PermissionError("case access denied")
        return row

    def create(self, access, message):
        if not message.strip():
            raise ValueError("permitted case context is required")
        case_id, input_id = uuid4(), uuid4()
        with transaction(self.engine, access) as connection:
            connection.execute(insert(tables.cases).values(case_id=case_id, owner_id=access.principal_id,
                namespace=access.namespace, current_input_id=input_id))
            connection.execute(insert(tables.inputs).values(input_id=input_id, case_id=case_id, message=message))
        return case_id, input_id

    def start_run(self, access, case_id, input_id, snapshot_id, configuration):
        with transaction(self.engine, access) as connection:
            case = self._case(connection, access, case_id)
            if case["current_input_id"] != input_id:
                raise ValueError("stale input revision")
            snapshot = connection.execute(select(tables.snapshots).where(tables.snapshots.c.snapshot_id == snapshot_id,
                tables.snapshots.c.namespace == access.namespace)).mappings().one()
            if not (snapshot["status"] == "published" or (snapshot["status"] == "live"
                    and snapshot["manifest"].get("runtime_case_id") == str(case_id))):
                raise PermissionError("run requires a published corpus or its own live capture")
            run_id, thread_id = uuid4(), uuid4()
            pinned = {**configuration, "profile_id": str(snapshot["profile_id"]),
                      "taxonomy_version_id": str(snapshot["taxonomy_version_id"]), "build_id": str(snapshot["build_id"])}
            connection.execute(insert(tables.runs).values(run_id=run_id, case_id=case_id, input_id=input_id,
                snapshot_id=snapshot_id, thread_id=thread_id, configuration=pinned))
            return run_id, thread_id

    def edit(self, access, case_id, *, expected_revision, instruction, kind):
        if kind not in {"formatting", "focus", "identity"} or not instruction.strip():
            raise ValueError("edit requires an instruction and formatting/focus/identity kind")
        with transaction(self.engine, access) as connection:
            case = self._case(connection, access, case_id)
            if case["revision"] != expected_revision:
                raise ValueError("concurrent edit changed the case revision")
            input_id = case["current_input_id"]
            reusable_pack = None
            if kind == "formatting":
                if case["current_result_id"]:
                    reusable_pack = connection.execute(select(tables.results.c.pack_id).where(
                        tables.results.c.result_id == case["current_result_id"])).scalar_one()
            else:
                input_id = uuid4()
                parent = connection.execute(select(tables.inputs.c.message).where(
                    tables.inputs.c.input_id == case["current_input_id"])).scalar_one()
                connection.execute(insert(tables.inputs).values(input_id=input_id, case_id=case_id,
                    parent_id=case["current_input_id"], message=parent + "\n\nUser revision: " + instruction))
                connection.execute(update(tables.runs).where(tables.runs.c.case_id == case_id,
                    tables.runs.c.status.not_in(["completed", "cancelled", "superseded"])).values(status="superseded"))
            connection.execute(insert(tables.turns).values(turn_id=uuid4(), case_id=case_id, role="user",
                message=instruction, input_id=input_id))
            connection.execute(update(tables.cases).where(tables.cases.c.case_id == case_id).values(
                revision=expected_revision + 1, current_input_id=input_id, current_result_id=None, status="draft", outcome=None))
            connection.execute(update(tables.exports).where(tables.exports.c.result_id.in_(
                select(tables.results.c.result_id).where(tables.results.c.case_id == case_id))).values(status="stale"))
            return {"input_id": input_id, "reusable_pack_id": reusable_pack, "requires_retrieval": kind != "formatting",
                    "revision": expected_revision + 1}

    def ask(self, access, run_id, *, field, reason, required=True):
        with transaction(self.engine, access) as connection:
            run = self._run(connection, access, run_id)
            question_id = uuid4()
            connection.execute(insert(tables.questions).values(question_id=question_id, run_id=run_id,
                input_id=run["input_id"], field=field, reason=reason, required=required))
            connection.execute(update(tables.runs).where(tables.runs.c.run_id == run_id).values(status="needs_clarification"))
            return question_id

    def answer(self, access, question_id, message):
        with transaction(self.engine, access) as connection:
            question = connection.execute(select(tables.questions).where(
                tables.questions.c.question_id == question_id).with_for_update()).mappings().one()
            run = self._run(connection, access, question["run_id"])
            case = self._case(connection, access, run["case_id"])
            if question["status"] != "open" or question["input_id"] != case["current_input_id"]:
                raise ValueError("stale or already answered clarification")
            turn_id = uuid4()
            connection.execute(insert(tables.turns).values(turn_id=turn_id, case_id=run["case_id"], role="user",
                message=message, input_id=run["input_id"]))
            connection.execute(insert(tables.answers).values(answer_id=uuid4(), question_id=question_id, turn_id=turn_id))
            connection.execute(update(tables.questions).where(tables.questions.c.question_id == question_id).values(status="answered"))
            return run["thread_id"]

    def _run(self, connection, access, run_id):
        run = connection.execute(select(tables.runs).where(tables.runs.c.run_id == run_id).with_for_update()).mappings().one()
        case = self._case(connection, access, run["case_id"])
        if case["current_input_id"] != run["input_id"] or run["status"] in {"cancelled", "superseded"}:
            raise ValueError("run has stale input or is cancelled")
        return run

    def freeze_pack(self, access, run_id, payload, evidence_ids):
        with transaction(self.engine, access) as connection:
            run = self._run(connection, access, run_id)
            eligible = set(connection.execute(select(tables.spans.c.evidence_id).join(tables.snapshot_documents,
                tables.snapshot_documents.c.document_version_id == tables.spans.c.document_version_id).where(
                tables.snapshot_documents.c.snapshot_id == run["snapshot_id"], tables.spans.c.evidence_id.in_(evidence_ids),
                text("ops.can_access(corpus.evidence_spans.scope_id)"))).scalars())
            if not evidence_ids or eligible != set(evidence_ids):
                raise PermissionError("pack evidence must be accessible in the run's pinned snapshot")
            pack_id = uuid4()
            pack_hash = configuration_hash({"payload": payload, "evidence": sorted(str(value) for value in eligible)})
            connection.execute(insert(tables.packs).values(pack_id=pack_id, run_id=run_id, input_id=run["input_id"],
                pack_hash=pack_hash, payload=payload))
            for evidence_id in eligible:
                connection.execute(insert(tables.pack_items).values(pack_id=pack_id, evidence_id=evidence_id))
            return pack_id

    def record_result(self, access, case_id, pack_id, payload, *, expected_revision, instruction="", parent_id=None):
        with transaction(self.engine, access) as connection:
            case = self._case(connection, access, case_id)
            if case["revision"] != expected_revision:
                raise ValueError("stale result revision")
            pack = connection.execute(select(tables.packs).where(tables.packs.c.pack_id == pack_id)).mappings().one()
            run = self._run(connection, access, pack["run_id"])
            if run["case_id"] != case_id or pack["input_id"] != case["current_input_id"]:
                raise ValueError("pack belongs to another case or input revision")
            evidence = list(connection.execute(select(tables.spans.c.scope_id).select_from(
                tables.pack_items.outerjoin(tables.spans)).where(tables.pack_items.c.pack_id == pack_id)).scalars())
            from backend.data.database import require_scope
            for scope_id in evidence:
                if scope_id is None:
                    raise PermissionError("pack includes unavailable evidence")
                require_scope(connection, scope_id)
            if parent_id is not None:
                parent_case = connection.execute(select(tables.results.c.case_id).where(
                    tables.results.c.result_id == parent_id)).scalar_one()
                if parent_case != case_id:
                    raise ValueError("parent result belongs to another case")
            result_id = uuid4()
            connection.execute(insert(tables.results).values(result_id=result_id, case_id=case_id, pack_id=pack_id,
                parent_id=parent_id, instruction=instruction, payload=payload, result_hash=configuration_hash(payload)))
            connection.execute(update(tables.cases).where(tables.cases.c.case_id == case_id).values(
                current_result_id=result_id, revision=expected_revision + 1, status="ready_for_review"))
            return result_id

    def cancel(self, access, run_id):
        with transaction(self.engine, access) as connection:
            self._run(connection, access, run_id)
            connection.execute(update(tables.runs).where(tables.runs.c.run_id == run_id).values(status="cancelled"))

    def read_result(self, access, result_id):
        with transaction(self.engine, access) as connection:
            result = connection.execute(select(tables.results).where(tables.results.c.result_id == result_id)).mappings().one()
            self._case(connection, access, result["case_id"])
            self._validate_pack(connection, result["pack_id"])
            return dict(result)

    def _validate_pack(self, connection, pack_id):
        from backend.data.repositories.evidence import eligible_evidence
        pack = connection.execute(select(tables.packs).where(tables.packs.c.pack_id == pack_id)).mappings().one()
        run = connection.execute(select(tables.runs).where(tables.runs.c.run_id == pack["run_id"])).mappings().one()
        evidence_ids = list(connection.execute(select(tables.pack_items.c.evidence_id).where(
            tables.pack_items.c.pack_id == pack_id)).scalars())
        if pack["payload"].get("schema_version") == 2:
            from backend.contracts.pipeline import ReportEvidencePack
            parsed = ReportEvidencePack.model_validate(pack["payload"])
            expected_evidence = {key for claim in parsed.claims for key in claim.evidence_ids}
            actual_claims = set(connection.execute(select(tables.pack_claims.c.claim_id).where(
                tables.pack_claims.c.pack_id == pack_id)).scalars())
            pins = {name: str(run[name]) for name in ("run_id", "input_id", "snapshot_id")}
            digest = configuration_hash({"payload": pack["payload"], "pins": pins,
                "configuration": run["configuration"], "manifest_id": str(pack["manifest_id"]) if pack["manifest_id"] else None,
                "evidence": sorted(map(str, evidence_ids))})
            if (set(evidence_ids) != expected_evidence or actual_claims != {claim.claim_id for claim in parsed.claims}
                    or digest != pack["pack_hash"]):
                raise PermissionError("frozen pack membership or hash changed")
        elif not evidence_ids:
            raise PermissionError("pack evidence is unavailable")
        eligible_evidence(connection, run, evidence_ids, pack["manifest_id"])

    def review(self, access, result_id, *, expected_hash, decision, expected_selection_hash=None):
        if decision not in {"accepted", "rejected"}:
            raise ValueError("review decision must be accepted or rejected")
        with transaction(self.engine, access) as connection:
            result = connection.execute(select(tables.results).where(tables.results.c.result_id == result_id)).mappings().one()
            case = self._case(connection, access, result["case_id"])
            self._validate_pack(connection, result["pack_id"])
            if case["current_result_id"] != result_id or result["result_hash"] != expected_hash:
                raise ValueError("review must target the current exact result hash")
            from backend.data.repositories.drafts import selection_hash
            if result["payload"].get("schema_version") != 2:
                raise ValueError("legacy results need a validated v2 reason revision before review")
            selections = selection_hash(connection, result_id, require_complete=decision == "accepted")
            if decision == "accepted" and expected_selection_hash != selections:
                raise ValueError("approval requires the exact current selection hash")
            review_id = uuid4()
            connection.execute(insert(tables.reviews).values(review_id=review_id, result_id=result_id,
                reviewer_id=access.principal_id, result_hash=expected_hash, selection_hash=selections, decision=decision))
            return review_id

    def record_export(self, access, result_id, review_id, reference, *, artifacts, template_version, renderer_version, format="pdf"):
        from backend.data.repositories.corpus import save_artifact
        from backend.reports.rendering.pptx import MIME as PPTX_MIME
        if format not in {'pdf', 'pptx'} or reference.mime != {'pdf':'application/pdf', 'pptx':PPTX_MIME}[format]:
            raise ValueError('export format and MIME must agree')
        artifacts.read(reference)
        with transaction(self.engine, access) as connection:
            result = connection.execute(select(tables.results).where(tables.results.c.result_id == result_id)).mappings().one()
            case = self._case(connection, access, result["case_id"])
            self._validate_pack(connection, result["pack_id"])
            review = connection.execute(select(tables.reviews).where(tables.reviews.c.review_id == review_id)).mappings().one()
            if (case["current_result_id"] != result_id or review["result_id"] != result_id or
                    review["decision"] != "accepted" or review["result_hash"] != result["result_hash"]):
                raise ValueError("export requires the current reviewed result")
            from backend.data.repositories.drafts import selection_hash
            selections = selection_hash(connection, result_id, require_complete=True)
            if review["selection_hash"] != selections or result["payload"].get("schema_version") != 2:
                raise ValueError("reviewed selections changed or result is legacy")
            export_id = uuid4()
            connection.execute(insert(tables.exports).values(export_id=export_id, result_id=result_id, review_id=review_id,
                artifact_id=save_artifact(connection, reference), template_version=template_version,
                renderer_version=renderer_version, selection_hash=selections, format=format))
            return export_id
