"""Atomic HTTP commands/idempotency using existing outbox and repositories."""
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy import insert, select, text, update

from backend.contracts.data import configuration_hash
from backend.contracts.services import ServiceUnavailable, StaleRevision
from backend.data import schema as t

ACTIVE = {"queued", "running", "needs_clarification"}


class Commands:
    def command(self, access, key, name, body, callback):
        digest = configuration_hash({"principal": str(access.principal_id), "namespace": access.namespace,
                                     "operation": name, "key": key})
        body_hash = configuration_hash(body)
        with self.session(access) as c:
            c.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:key,0))"), {"key": digest})
            old = c.execute(select(t.outbox.c.payload).where(t.outbox.c.idempotency_key == digest)).scalar_one_or_none()
            if old is not None:
                if old["body_hash"] != body_hash:
                    raise StaleRevision()
                return old["response"]
            response = callback(c)
            c.execute(insert(t.outbox).values(event_id=uuid4(), namespace=access.namespace, idempotency_key=digest,
                event_type="runtime.command", status="delivered", payload={"body_hash": body_hash,
                    "principal_id": str(access.principal_id), "response": response}))
            return response

    def start(self, c, access, case_id, input_id, profile_id, request_id, *, instruction="", parent_id=None, pack_id=None):
        case = self.case(c, access, case_id)
        # The restricted DB function verifies session identity and locks this owned case.
        # It grants only this case's owner, never a browser-supplied principal/scope.
        c.execute(text("SELECT ops.ensure_case_scope(:case)"), {"case": case_id})
        if c.execute(select(t.runs.c.run_id).where(t.runs.c.case_id == case_id, t.runs.c.status.in_(ACTIVE))).first():
            raise StaleRevision()
        if pack_id:
            previous = c.execute(select(t.packs).where(t.packs.c.pack_id == pack_id)).mappings().one()
            original = self.run(c, access, previous["run_id"])
            if previous["input_id"] != input_id or original["case_id"] != case_id:
                raise StaleRevision()
            snapshot = c.execute(select(t.snapshots).where(t.snapshots.c.snapshot_id == original["snapshot_id"])).mappings().one()
        else:
            if self.settings.corpus_mode == "live":
                from backend.data.repositories.live import capture_live_corpus
                snapshot = capture_live_corpus(c, self.settings, case_id, profile_id)
            else:
                snapshot = c.execute(select(t.snapshots).join(t.active_snapshots,
                    t.active_snapshots.c.snapshot_id == t.snapshots.c.snapshot_id).where(
                    t.active_snapshots.c.profile_id == profile_id, t.snapshots.c.namespace == access.namespace,
                    t.snapshots.c.status == "published")).mappings().one_or_none()
            if snapshot is None:
                raise ServiceUnavailable()
        config = {"runtime_version": "1", "mode": self.settings.mode, "model": self.settings.llm_name,
            "model_endpoint": self.settings.llm_base_url, "deadline_at": (datetime.now(timezone.utc) +
                timedelta(seconds=self.settings.deadline_seconds)).isoformat(),
            "max_research_rounds": self.settings.max_research_rounds, "max_output_tokens": self.settings.max_output_tokens,
            "max_tool_calls": self.settings.max_tool_calls, "request_id": request_id,
            "expected_revision": case["revision"], "instruction": instruction,
            "corpus_mode": "live" if snapshot["status"] == "live" else "published",
            "parent_result_id": str(parent_id) if parent_id else None, "reuse_pack_id": str(pack_id) if pack_id else None}
        repo, _, _, jobs = self.repositories(c)
        run_id, _ = repo.start_run(access, case_id, input_id, snapshot["snapshot_id"], config)
        self.enqueue(c, access, run_id, "runtime.execute", {"run_id": str(run_id)})
        c.execute(update(t.runs).where(t.runs.c.run_id == run_id).values(status="queued"))
        return {"case_id": str(case_id), "input_id": str(input_id), "run_id": str(run_id),
                "status_url": f"/api/v1/cases/{case_id}/runs/{run_id}"}

    def create(self, access, key, body, request_id):
        def callback(c):
            repo = self.repositories(c)[0]
            case_id, input_id = repo.create(access, body["prompt"])
            c.execute(insert(t.turns).values(turn_id=uuid4(), case_id=case_id, input_id=input_id,
                                            role="user", message=body["prompt"]))
            response = {"case_id": str(case_id), "input_id": str(input_id)}
            if body.get("run", True):
                profile = body.get("profile_id") or self.settings.default_profile_id
                if not profile:
                    raise ServiceUnavailable()
                response = self.start(c, access, case_id, input_id, UUID(str(profile)), request_id)
            return response
        return self.command(access, key, "create", body, callback)

    def start_command(self, access, key, case_id, body, request_id):
        return self.command(access, key, f"run:{case_id}", body, lambda c: self.start(c, access, case_id,
            UUID(body["input_id"]), UUID(body["profile_id"]) if body.get("profile_id") else self.settings.default_profile_id,
            request_id))

    def edit(self, access, key, case_id, body, request_id):
        def callback(c):
            case = self.case(c, access, case_id)
            if case["revision"] != body["expected_revision"]:
                raise StaleRevision()
            old_result = case["current_result_id"]
            change = self.repositories(c)[0].edit(access, case_id, expected_revision=body["expected_revision"],
                instruction=body["text"], kind=body["kind"])
            self.copy_business_context(c, access, case_id, case["current_input_id"], change["input_id"])
            if body["kind"] == "formatting" and not change["reusable_pack_id"]:
                raise StaleRevision()
            profile = body.get("profile_id") or self.settings.default_profile_id
            if not profile and not change["reusable_pack_id"]:
                raise ServiceUnavailable()
            return self.start(c, access, case_id, change["input_id"], UUID(str(profile)) if profile else None, request_id,
                instruction=body["text"], parent_id=old_result, pack_id=change["reusable_pack_id"])
        return self.command(access, key, f"edit:{case_id}", body, callback)

    def answer(self, access, key, case_id, run_id, body):
        def callback(c):
            run = self.run(c, access, run_id, active=True)
            if run["case_id"] != case_id or str(run["input_id"]) != body["input_id"]:
                raise StaleRevision()
            q = c.execute(select(t.questions).where(t.questions.c.question_id == UUID(body["question_id"]),
                                                  t.questions.c.run_id == run_id)).mappings().one()
            self.repositories(c)[0].answer(access, q["question_id"], body["answer"])
            remaining = c.execute(select(t.questions.c.question_id).where(t.questions.c.run_id == run_id,
                                                                         t.questions.c.status == "open")).first()
            if not remaining:
                self.enqueue(c, access, run_id, "runtime.execute", {"run_id": str(run_id), "resume": True},
                             suffix=body["question_id"])
                c.execute(update(t.runs).where(t.runs.c.run_id == run_id).values(status="queued"))
            return {"run_id": str(run_id), "status_url": f"/api/v1/cases/{case_id}/runs/{run_id}"}
        return self.command(access, key, f"answer:{run_id}", body, callback)

    def cancel(self, access, key, case_id, run_id):
        def callback(c):
            run = self.run(c, access, run_id, active=True)
            if run["case_id"] != case_id:
                raise PermissionError()
            self.repositories(c)[0].cancel(access, run_id)
            c.execute(update(t.cases).where(t.cases.c.case_id == case_id, t.cases.c.status == "researching").values(status="draft"))
            c.execute(update(t.attempts).where(t.attempts.c.run_id == run_id,
                t.attempts.c.status.in_(["pending", "running"])).values(status="failed", lease_until=None))
            return {"run_id": str(run_id), "status": "cancelled"}
        return self.command(access, key, f"cancel:{run_id}", {}, callback)

    def report(self, access, key, case_id, body, request_id):
        def callback(c):
            case = self.case(c, access, case_id)
            if case["revision"] != body["expected_revision"]:
                raise StaleRevision()
            pack_id = UUID(body["pack_id"])
            self.repositories(c)[0]._validate_pack(c, pack_id)
            return self.start(c, access, case_id, case["current_input_id"], None, request_id,
                instruction=body["instruction"], parent_id=case["current_result_id"], pack_id=pack_id)
        return self.command(access, key, f"report:{case_id}", body, callback)
