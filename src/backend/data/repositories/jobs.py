from uuid import uuid4

from sqlalchemy import insert, select, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from backend.contracts.data import configuration_hash
from backend.data import schema as tables
from backend.data.database import transaction
from backend.data.repositories.cases import CaseRepository


class JobRepository:
    def __init__(self, engine):
        self.engine = engine

    def enqueue_stage(self, access, run_id, stage, input_hash, config_hash):
        key = configuration_hash({"namespace": access.namespace, "run": str(run_id), "stage": stage,
                                  "input": input_hash, "config": config_hash})
        with transaction(self.engine, access) as connection:
            CaseRepository(self.engine)._run(connection, access, run_id)
            connection.execute(pg_insert(tables.attempts).values(attempt_id=uuid4(), run_id=run_id, namespace=access.namespace,
                stage=stage, input_hash=input_hash, config_hash=config_hash, idempotency_key=key)
                .on_conflict_do_nothing(index_elements=["idempotency_key"]))
            return connection.execute(select(tables.attempts.c.attempt_id).where(
                tables.attempts.c.idempotency_key == key)).scalar_one()

    def claim(self, access, worker_id, *, lease_seconds=60):
        if not 1 <= lease_seconds <= 3600:
            raise ValueError("lease must be between 1 and 3600 seconds")
        with transaction(self.engine, access) as connection:
            return connection.execute(text("""
                WITH candidate AS (
                  SELECT a.attempt_id FROM ops.stage_attempts a JOIN cases.runs r USING(run_id)
                  JOIN cases.cases c ON c.case_id=r.case_id
                  WHERE a.namespace=:namespace AND c.owner_id=:principal
                    AND c.current_input_id=r.input_id AND r.status NOT IN ('cancelled','superseded')
                    AND (a.status='pending' OR (a.status='running' AND a.lease_until<now()))
                  ORDER BY a.created_at,a.attempt_id FOR UPDATE OF a SKIP LOCKED LIMIT 1)
                UPDATE ops.stage_attempts a SET status='running',worker_id=:worker,
                  lease_until=now()+make_interval(secs=>:seconds),attempt_count=attempt_count+1
                FROM candidate WHERE a.attempt_id=candidate.attempt_id RETURNING a.*
            """), {"namespace": access.namespace, "principal": access.principal_id,
                    "worker": worker_id, "seconds": lease_seconds}).mappings().one_or_none()

    def complete(self, access, attempt_id, worker_id, outputs):
        with transaction(self.engine, access) as connection:
            attempt = connection.execute(select(tables.attempts).where(
                tables.attempts.c.attempt_id == attempt_id).with_for_update()).mappings().one()
            if attempt["namespace"] != access.namespace:
                raise PermissionError("worker namespace mismatch")
            CaseRepository(self.engine)._run(connection, access, attempt["run_id"])
            if attempt["status"] == "committed":
                if attempt["outputs"] != outputs:
                    raise ValueError("idempotent stage output changed")
                return dict(attempt["outputs"])
            valid = connection.execute(text("SELECT :deadline > now()"), {"deadline": attempt["lease_until"]}).scalar()
            if attempt["status"] != "running" or attempt["worker_id"] != worker_id or not valid:
                raise ValueError("worker does not own a live lease")
            connection.execute(update(tables.attempts).where(tables.attempts.c.attempt_id == attempt_id).values(
                status="committed", outputs=outputs, lease_until=None))
            connection.execute(update(tables.runs).where(tables.runs.c.run_id == attempt["run_id"]).values(
                last_successful_stage=attempt["stage"]))
            connection.execute(pg_insert(tables.outbox).values(event_id=uuid4(), namespace=access.namespace,
                run_id=attempt["run_id"], idempotency_key=f"stage:{attempt_id}", event_type="stage.committed",
                payload={"attempt_id": str(attempt_id), "stage": attempt["stage"], "outputs": outputs})
                .on_conflict_do_nothing(index_elements=["idempotency_key"]))
            return outputs

    def committed(self, access, attempt_id):
        with transaction(self.engine, access) as connection:
            attempt = connection.execute(select(tables.attempts).where(
                tables.attempts.c.attempt_id == attempt_id, tables.attempts.c.namespace == access.namespace)).mappings().one()
            CaseRepository(self.engine)._run(connection, access, attempt["run_id"])
            return dict(attempt["outputs"]) if attempt["status"] == "committed" else None

    def claim_event(self, access, worker_id, lease_seconds=60):
        with transaction(self.engine, access) as connection:
            row = connection.execute(text("""
                WITH candidate AS (
                  SELECT event_id FROM ops.outbox WHERE namespace=:namespace AND next_retry<=now()
                    AND (status='pending' OR (status='running' AND lease_until<now()))
                  ORDER BY created_at,event_id FOR UPDATE SKIP LOCKED LIMIT 1)
                UPDATE ops.outbox o SET status='running',worker_id=:worker,
                  lease_until=now()+make_interval(secs=>:seconds),attempts=attempts+1
                FROM candidate WHERE o.event_id=candidate.event_id RETURNING o.*
            """), {"namespace": access.namespace, "worker": worker_id, "seconds": lease_seconds}).mappings().one_or_none()
            return dict(row) if row else None

    def acknowledge_event(self, access, event_id, worker_id, *, success=True):
        with transaction(self.engine, access) as connection:
            changed = connection.execute(text("""
                UPDATE ops.outbox SET status=:status,lease_until=NULL,
                  next_retry=now()+make_interval(secs=>LEAST(300,attempts*5))
                WHERE event_id=:event AND namespace=:namespace AND worker_id=:worker
                  AND status='running' AND lease_until>now()
            """), {"event": event_id, "namespace": access.namespace, "worker": worker_id,
                    "status": "delivered" if success else "pending"}).rowcount
            if not changed:
                raise ValueError("outbox event lease lost")
