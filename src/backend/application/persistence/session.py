"""Transaction adapter: reuse existing repositories in one command transaction."""
from contextlib import contextmanager

from backend.data.database import transaction
from backend.data.repositories.cases import CaseRepository
from backend.data.repositories.drafts import DraftRepository
from backend.data.repositories.evidence import EvidenceRepository
from backend.data.repositories.jobs import JobRepository


class BoundEngine:
    def __init__(self, connection):
        self.connection = connection

    @contextmanager
    def begin(self):
        yield self.connection


class Session:
    def __init__(self, engine, settings, artifacts):
        self.engine, self.settings, self.artifacts = engine, settings, artifacts

    @contextmanager
    def session(self, access):
        with transaction(self.engine, access) as connection:
            yield connection

    def repositories(self, connection):
        engine = BoundEngine(connection)
        return CaseRepository(engine), DraftRepository(engine), EvidenceRepository(engine), JobRepository(engine)

    def case(self, connection, access, case_id):
        return self.repositories(connection)[0]._case(connection, access, case_id)

    def run(self, connection, access, run_id, *, active=False):
        from sqlalchemy import select
        from backend.data import schema as t
        row = connection.execute(select(t.runs).where(t.runs.c.run_id == run_id)).mappings().one()
        case = self.case(connection, access, row["case_id"])
        if active and (case["current_input_id"] != row["input_id"] or row["status"] in {"cancelled", "superseded"}):
            from backend.contracts.services import StaleRevision
            raise StaleRevision()
        return dict(row)
