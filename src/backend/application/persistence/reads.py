"""Authorized runtime reads and execution context construction, no model calls."""
from datetime import datetime
from uuid import UUID

from sqlalchemy import select

from backend.data.snapshot_projection import snapshot_metadata
from backend.contracts.data import configuration_hash
from backend.contracts.services import EvidenceRejected, RunContext
from backend.data import schema as t
from backend.data.database import require_scope


class Reads:
    def current_run(self, access, case_id):
        with self.session(access) as c:
            case = self.case(c, access, case_id)
            return c.execute(select(t.runs.c.run_id).where(t.runs.c.case_id == case_id,
                t.runs.c.input_id == case["current_input_id"]).order_by(
                t.runs.c.created_at.desc(), t.runs.c.run_id.desc()).limit(1)).scalar_one_or_none()

    def context(self, access, run_id):
        with self.session(access) as c:
            run = self.run(c, access, run_id)
            pin = c.execute(select(*snapshot_metadata(), t.embedding_configs.c.config_hash).select_from(
                t.snapshots.join(t.builds).join(t.embedding_configs)).where(
                t.snapshots.c.snapshot_id == run["snapshot_id"])).mappings().one()
            cfg = run["configuration"]
            return RunContext(access=access, case_id=run["case_id"], input_id=run["input_id"], run_id=run_id,
                snapshot_id=pin["snapshot_id"], profile_id=pin["profile_id"], taxonomy_version_id=pin["taxonomy_version_id"],
                build_id=pin["build_id"], embedding_config_hash=pin["config_hash"], mode=cfg["mode"],
                deadline_at=datetime.fromisoformat(cfg["deadline_at"]), request_id=cfg["request_id"],
                max_research_rounds=cfg["max_research_rounds"], max_output_tokens=cfg["max_output_tokens"],
                max_tool_calls=cfg["max_tool_calls"])

    def initial_state(self, access, run_id):
        context = self.context(access, run_id)
        with self.session(access) as c:
            run = self.run(c, access, run_id, active=True)
            message = c.execute(select(t.inputs.c.message).where(t.inputs.c.input_id == run["input_id"])).scalar_one()
            cfg = run["configuration"]
            return {"context": context.model_dump(mode="json"), "message": message,
                "instruction": cfg["instruction"], "expected_revision": cfg["expected_revision"],
                "parent_result_id": cfg["parent_result_id"], "pack_id": cfg["reuse_pack_id"],
                "round": 0, "clarification_round": 0, "tools_used": 0}

    def run_view(self, access, case_id, run_id):
        with self.session(access) as c:
            run = self.run(c, access, run_id)
            if run["case_id"] != case_id:
                raise PermissionError()
            questions = c.execute(select(t.questions).where(t.questions.c.run_id == run_id).order_by(
                t.questions.c.created_at, t.questions.c.question_id)).mappings().all()
            step = run["last_successful_stage"] or ""
            stage = ("done" if run["status"] == "completed" else "drafting" if step.startswith("draft") else
                "validating" if step.startswith(("extract", "persist_extraction", "evidence", "assess", "propose_pack", "pack")) else
                "searching" if step.startswith(("replan", "retrieve", "discover", "fetch", "register", "merge")) else
                "interpreting" if step or run["status"] == "running" else None)
            result = c.execute(select(t.attempts.c.outputs).where(t.attempts.c.run_id == run_id,
                t.attempts.c.stage == "runtime.node.draft.persist").order_by(t.attempts.c.created_at.desc()).limit(1)).scalar_one_or_none()
            pack = c.execute(select(t.packs).where(t.packs.c.run_id == run_id).order_by(
                t.packs.c.created_at.desc(), t.packs.c.pack_id.desc()).limit(1)).mappings().one_or_none()
            failure = c.execute(select(t.attempts.c.outputs).where(t.attempts.c.run_id == run_id,
                t.attempts.c.stage == "runtime.execute", t.attempts.c.status == "failed").order_by(
                t.attempts.c.created_at.desc(), t.attempts.c.attempt_id.desc()).limit(1)).scalar_one_or_none()
            detail = (failure or {}).get("result", {}) if run["status"] == "failed" else {}
            return {"schema_version": "1", "case_id": str(case_id), "run_id": str(run_id), "input_id": str(run["input_id"]),
                "snapshot_id": str(run["snapshot_id"]), "state": run["status"],
                "status": {"needs_clarification": "waiting_for_input", "completed": "succeeded"}.get(run["status"], run["status"]),
                "stage": stage, "step": step or None, "error_code": run["failure_reason"],
                "failure_detail": {k: detail[k] for k in ("failed_stage", "model_task", "validation_issues") if k in detail},
                "result_id": result.get("result_id") if result else None,
                "pack_id": str(pack["pack_id"]) if pack else run["configuration"].get("reuse_pack_id"),
                "outcome": pack["payload"].get("outcome") if pack else None,
                "limitations": pack["payload"].get("gaps", []) if pack else [],
                "questions": [{"id": str(q["question_id"]), "question": q["reason"], "status": q["status"]} for q in questions]}


    def answers(self, access, run_id):
        with self.session(access) as c:
            self.run(c, access, run_id, active=True)
            return [dict(row) for row in c.execute(select(t.questions.c.question_id, t.questions.c.reason,
                t.turns.c.message).select_from(t.questions.join(t.answers).join(t.turns)).where(
                t.questions.c.run_id == run_id).order_by(t.questions.c.created_at, t.questions.c.question_id)).mappings()]

    def pack(self, access, pack_id):
        with self.session(access) as c:
            record = c.execute(select(t.packs).where(t.packs.c.pack_id == pack_id)).mappings().one()
            self.run(c, access, record["run_id"])
            self.repositories(c)[0]._validate_pack(c, pack_id)
            return dict(record)

    def validate_evidence(self, access, run_id, records):
        with self.session(access) as c:
            run = self.run(c, access, run_id, active=True)
            for record in records:
                row = c.execute(select(t.spans, t.versions.c.body_hash, t.versions.c.body_text,
                    t.scopes.c.kind, t.scopes.c.case_id, t.documents.c.canonical_url, t.versions.c.title, t.versions.c.language).select_from(t.spans.join(t.versions).join(t.documents).join(t.scopes,
                    t.scopes.c.scope_id == t.spans.c.scope_id)).where(
                    t.spans.c.evidence_id == record.evidence_id)).mappings().one()
                require_scope(c, row["scope_id"])
                if (record.scope_id != row["scope_id"] or record.document_version_id != row["document_version_id"]
                    or record.body_hash != row["body_hash"] or record.char_start != row["char_start"]
                    or record.char_end != row["char_end"] or record.literal_text != row["literal_text"]
                    or row["body_text"][record.char_start:record.char_end] != record.literal_text
                    or record.url != row["canonical_url"] or record.title != row["title"] or record.language != row["language"]):
                    raise EvidenceRejected()
                if row["kind"] == "case":
                    if row["case_id"] != run["case_id"]:
                        raise EvidenceRejected()
                elif not c.execute(select(t.snapshot_documents).where(
                    t.snapshot_documents.c.snapshot_id == run["snapshot_id"],
                    t.snapshot_documents.c.document_version_id == row["document_version_id"])).first():
                    raise EvidenceRejected()

    def case_rows(self, access, case_id=None, *, limit=None, offset=0):
        with self.session(access) as c:
            if case_id:
                self.case(c, access, case_id)
            query = select(t.cases).where(t.cases.c.owner_id == access.principal_id, t.cases.c.namespace == access.namespace)
            if case_id:
                query = query.where(t.cases.c.case_id == case_id)
            if limit is not None:
                query = query.limit(limit).offset(offset)
            cases = [dict(row) for row in c.execute(query.order_by(t.cases.c.created_at, t.cases.c.case_id)).mappings()]
            output = []
            for case in cases:
                results = [dict(row) for row in c.execute(select(t.results).where(t.results.c.case_id == case["case_id"])
                    .order_by(t.results.c.created_at, t.results.c.result_id)).mappings()]
                for result in results:
                    self.repositories(c)[0]._validate_pack(c, result["pack_id"])
                    if configuration_hash(result["payload"]) != result["result_hash"]:
                        raise EvidenceRejected()
                result_ids = [row["result_id"] for row in results]
                packs = {str(row["pack_id"]): dict(row) for row in c.execute(select(t.packs, t.snapshots.c.published_at.label("snapshot_date")).select_from(t.packs.join(t.runs).join(t.snapshots)).where(
                    t.packs.c.pack_id.in_([result["pack_id"] for result in results]))).mappings()}
                reasons = [dict(row) for row in c.execute(select(t.reasons, t.reason_selections.c.selection)
                    .outerjoin(t.reason_selections).where(t.reasons.c.result_id.in_(result_ids))).mappings()]
                turns = [dict(row) for row in c.execute(select(t.turns).where(t.turns.c.case_id == case["case_id"])
                    .order_by(t.turns.c.created_at, t.turns.c.turn_id)).mappings()]
                questions = [dict(row) for row in c.execute(select(t.questions).join(t.runs).where(
                    t.runs.c.case_id == case["case_id"])).mappings()]
                for question in questions:
                    question["answer"] = c.execute(select(t.turns.c.message).join(t.answers,
                        t.answers.c.turn_id == t.turns.c.turn_id).where(
                        t.answers.c.question_id == question["question_id"])).scalar_one_or_none()
                interpretations = [row for row in c.execute(select(t.interpretations.c.payload).join(t.runs).where(
                    t.runs.c.case_id == case["case_id"], t.runs.c.input_id == case["current_input_id"])).scalars()]
                claim_types = {str(row["claim_id"]): row["entity_type"] for row in c.execute(
                    select(t.claims.c.claim_id, t.entities.c.entity_type).join(t.entities,
                        t.entities.c.entity_id == t.claims.c.subject_id).join(t.pack_claims).where(
                        t.pack_claims.c.pack_id.in_([r["pack_id"] for r in results]))).mappings()}
                output.append({"claim_types": claim_types, "case": case, "results": results, "packs": packs, "reasons": reasons,
                    "turns": turns, "questions": questions, "interpretation": interpretations[-1] if interpretations else {}})
            return output

    def run_content(self, access, case_id, run_id):
        with self.session(access) as c:
            run = self.run(c, access, run_id)
            if run["case_id"] != case_id:
                raise PermissionError()
            record = c.execute(select(t.packs).where(t.packs.c.run_id == run_id).order_by(
                t.packs.c.created_at.desc(), t.packs.c.pack_id.desc()).limit(1)).mappings().one_or_none()
            if record is None and run["configuration"].get("reuse_pack_id"):
                record = c.execute(select(t.packs).where(t.packs.c.pack_id == UUID(run["configuration"]["reuse_pack_id"]))).mappings().one()
            if record is None:
                return {"status": run["status"], "matches": [], "limitations": ["Evidence preparation has not completed"]}
            self.repositories(c)[0]._validate_pack(c, record["pack_id"])
            return {"pack_id": str(record["pack_id"]), "matches": record["payload"].get("matches", []),
                    "outcome": record["payload"].get("outcome"), "limitations": record["payload"].get("gaps", [])}

    def execution_configuration(self, access, run_id):
        from backend.contracts.services import ServiceUnavailable
        with self.session(access) as c:
            run = self.run(c, access, run_id, active=True)
            cfg = run["configuration"]
            if (cfg["mode"] != self.settings.mode or cfg["model"] != self.settings.llm_name
                    or cfg["model_endpoint"] != self.settings.llm_base_url):
                raise ServiceUnavailable()
            return cfg

    def checkpoint_configuration(self, access, run_id):
        with self.session(access) as c:
            run = self.run(c, access, run_id, active=True)
            return {"configurable": {"thread_id": str(run["thread_id"]), "checkpoint_ns": ""}}
