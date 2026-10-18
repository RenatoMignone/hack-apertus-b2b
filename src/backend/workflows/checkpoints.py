from contextlib import contextmanager

from langgraph.checkpoint.postgres import PostgresSaver

from backend.data.database import transaction
from backend.data.repositories.cases import CaseRepository


class CheckpointPort:
    def __init__(self, engine, checkpoint_url):
        self.engine = engine
        self.checkpoint_url = checkpoint_url.replace("@localhost:", "@127.0.0.1:")

    def setup(self):
        with PostgresSaver.from_conn_string(self.checkpoint_url) as saver:
            saver.setup()

    @contextmanager
    def for_run(self, access, run_id):
        with transaction(self.engine, access) as connection:
            run = CaseRepository(self.engine)._run(connection, access, run_id)
            configuration = {"configurable": {"thread_id": str(run["thread_id"]), "checkpoint_ns": ""}}
        with PostgresSaver.from_conn_string(self.checkpoint_url) as saver:
            yield BoundCheckpoint(saver, configuration)


class BoundCheckpoint:
    def __init__(self, saver, configuration):
        self._saver = saver
        self.configuration = configuration

    def get(self):
        return self._saver.get_tuple(self.configuration)

    def put(self, checkpoint, metadata, new_versions):
        self.configuration = self._saver.put(self.configuration, checkpoint, metadata, new_versions)
        return self.configuration

    def put_writes(self, writes, task_id):
        return self._saver.put_writes(self.configuration, writes, task_id)
