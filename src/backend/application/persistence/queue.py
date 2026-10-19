"""Durable runtime queue and worker leases in existing stage_attempts."""
from uuid import uuid4

from sqlalchemy import insert, select, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from backend.contracts.data import configuration_hash
from backend.contracts.services import StaleRevision
from backend.data import schema as t


class Queue:
    def enqueue(self, c, access, run_id, stage, command, suffix="initial"):
        key = configuration_hash({"run": str(run_id), "stage": stage, "suffix": suffix})
        c.execute(pg_insert(t.attempts).values(attempt_id=uuid4(), run_id=run_id, namespace=access.namespace,
            stage=stage, input_hash=configuration_hash(command), config_hash=configuration_hash({"runtime": "1"}),
            idempotency_key=key, outputs={"command": command}).on_conflict_do_nothing(index_elements=["idempotency_key"]))
        return c.execute(select(t.attempts.c.attempt_id).where(t.attempts.c.idempotency_key == key)).scalar_one()

    def claim_job(self, access, worker):
        with self.session(access) as c:
            return c.execute(text("""
                WITH next AS (
                  SELECT a.attempt_id FROM ops.stage_attempts a JOIN cases.runs r USING(run_id)
                  JOIN cases.cases c ON c.case_id=r.case_id
                  WHERE a.namespace=:namespace AND c.owner_id=:owner AND c.current_input_id=r.input_id
                    AND r.status NOT IN ('cancelled','superseded')
                    AND a.stage IN ('runtime.execute','runtime.export')
                    AND (a.status='pending' OR (a.status='running' AND a.lease_until<now()))
                  ORDER BY a.created_at,a.attempt_id FOR UPDATE OF a SKIP LOCKED LIMIT 1)
                UPDATE ops.stage_attempts a SET status='running',worker_id=:worker,attempt_count=attempt_count+1,
                  lease_until=now()+make_interval(secs=>:lease)
                FROM next WHERE a.attempt_id=next.attempt_id RETURNING a.*
            """), {"namespace": access.namespace, "owner": access.principal_id, "worker": worker,
                    "lease": self.settings.worker_lease_seconds}).mappings().one_or_none()

    def heartbeat(self, access, job_id, worker):
        with self.session(access) as c:
            job = c.execute(select(t.attempts).where(t.attempts.c.attempt_id == job_id)).mappings().one()
            # Lease renewal is not a case mutation. Registration may hold the
            # case row while committing sources; waiting on it can expire our
            # own lease and cancel healthy work. Keep owner/current-input checks.
            self.run(c, access, job["run_id"], active=True, lock=False)
            changed = c.execute(update(t.attempts).where(t.attempts.c.attempt_id == job_id,
                t.attempts.c.worker_id == worker, t.attempts.c.status == "running", t.attempts.c.lease_until > text("now()"))
                .values(lease_until=text(f"now()+make_interval(secs=>{self.settings.worker_lease_seconds})"))).rowcount
            if not changed:
                raise StaleRevision()

    def finish_job(self, access, job_id, worker, output, *, failed=False):
        with self.session(access) as c:
            job = c.execute(select(t.attempts).where(t.attempts.c.attempt_id == job_id).with_for_update()).mappings().one()
            self.run(c, access, job["run_id"], active=True)
            if (job["status"] != "running" or job["worker_id"] != worker or not
                    c.execute(text("SELECT :deadline > now()"), {"deadline": job["lease_until"]}).scalar_one()):
                raise StaleRevision()
            c.execute(update(t.attempts).where(t.attempts.c.attempt_id == job_id).values(
                status="failed" if failed else "committed", lease_until=None,
                outputs={"command": job["outputs"]["command"], "result": output}))

    def operation(self, access, job_id):
        with self.session(access) as c:
            job = c.execute(select(t.attempts).where(t.attempts.c.attempt_id == job_id)).mappings().one()
            self.run(c, access, job["run_id"])
            if job["stage"] not in {"runtime.execute", "runtime.export"}:
                raise PermissionError()
            result = job["outputs"].get("result", {})
            return {"id": str(job_id), "status": job["status"], "result": result,
                **{key: result[key] for key in ("download_url", "export_id", "error_code") if key in result}}

    def start_activity(self, access, run_id, name):
        key = configuration_hash({"run": str(run_id), "activity": name})
        with self.session(access) as c:
            self.run(c, access, run_id, active=True, lock=False)
            c.execute(pg_insert(t.attempts).values(attempt_id=uuid4(), run_id=run_id, namespace=access.namespace,
                stage=f"runtime.progress.{name}", input_hash=key, config_hash=configuration_hash({"runtime": "1"}),
                idempotency_key=key, status="running", outputs={}).on_conflict_do_update(
                    index_elements=["idempotency_key"], set_={"status": "running", "created_at": text("now()"), "outputs": {}}))

    def finish_activity(self, access, run_id, name, *, failed=False):
        key = configuration_hash({"run": str(run_id), "activity": name})
        with self.session(access) as c:
            self.run(c, access, run_id, lock=False)
            c.execute(update(t.attempts).where(t.attempts.c.idempotency_key == key).values(
                status="failed" if failed else "committed"))

    def stage_output(self, access, run_id, name, inputs):
        key = configuration_hash({"run": str(run_id), "node": name, "inputs": inputs})
        with self.session(access) as c:
            self.run(c, access, run_id, active=True, lock=False)
            output = c.execute(select(t.attempts.c.outputs).where(t.attempts.c.idempotency_key == key,
                t.attempts.c.status == "committed")).scalar_one_or_none()
            return key, output

    def commit_stage(self, access, run_id, name, inputs, output, callback=None):
        key = configuration_hash({"run": str(run_id), "node": name, "inputs": inputs})
        with self.session(access) as c:
            self.run(c, access, run_id, active=True)
            old = c.execute(select(t.attempts.c.outputs).where(t.attempts.c.idempotency_key == key)).scalar_one_or_none()
            if old is not None:
                return old
            if callback:
                output = callback(c)
            c.execute(insert(t.attempts).values(attempt_id=uuid4(), run_id=run_id, namespace=access.namespace,
                stage=f"runtime.node.{name}", input_hash=configuration_hash(inputs),
                config_hash=configuration_hash({"runtime": "1"}), idempotency_key=key,
                status="committed", outputs=output))
            c.execute(update(t.runs).where(t.runs.c.run_id == run_id).values(last_successful_stage=name))
            return output

    def mark_run(self, access, run_id, status, error=None):
        with self.session(access) as c:
            run = self.run(c, access, run_id, active=True)
            c.execute(update(t.runs).where(t.runs.c.run_id == run_id).values(status=status, failure_reason=error))
            if status == "running":
                c.execute(update(t.cases).where(t.cases.c.case_id == run["case_id"], t.cases.c.status == "draft").values(status="researching"))
            elif status == "failed":
                c.execute(update(t.cases).where(t.cases.c.case_id == run["case_id"], t.cases.c.status == "researching").values(status="draft"))

    def defer_job(self, access, job_id, worker):
        with self.session(access) as c:
            job = c.execute(select(t.attempts).where(t.attempts.c.attempt_id == job_id)).mappings().one()
            self.run(c, access, job["run_id"], active=True)
            c.execute(update(t.attempts).where(t.attempts.c.attempt_id == job_id,
                t.attempts.c.worker_id == worker, t.attempts.c.status == "running").values(
                    status="pending", worker_id=None, lease_until=None))
