"""Subprocess-only synthetic worker for the disposable restart acceptance test."""
import asyncio
import json
import os
import sys
from pathlib import Path
from uuid import UUID

from backend.application.adapters import Services
from backend.application.persistence.store import RuntimeStore
from backend.application.service import RuntimeApplication
from backend.application.worker import Worker
from backend.config.runtime import RuntimeSettings
from backend.contracts.data import AccessContext
from backend.data.artifacts.store import FilesystemArtifactStore
from backend.data.database import engine_for
from backend.tests.runtime.fakes import FixtureBackbone, FixturePdf, FixtureReasoning


def main():
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    values = json.loads(Path(sys.argv[1]).read_text())
    engine = engine_for(values['database'])
    # Never allow this harness to operate on shared development or production DBs.
    if not engine.url.database.startswith('navigator_test_'):
        raise ValueError('process fixture requires a disposable test database')
    settings = RuntimeSettings(default_profile_id=UUID(values['fixture']['profile_id']),
        langgraph_database_url=values['database'], template_version='synthetic-template-v1',
        renderer_version='synthetic-registration-fixture-v1')
    store = RuntimeStore(engine, settings, FilesystemArtifactStore(Path(values['artifacts'])))
    class Reasoning(FixtureReasoning):
        async def extract(self, *args):
            with Path(values['calls']).open('a') as stream:
                stream.write('extract\n')
            return await super().extract(*args)
    if sys.argv[2] == 'crash':
        original = store.commit_stage
        def commit(*args, **kwargs):
            result = original(*args, **kwargs)
            if args[2] == 'persist_extraction.1':
                os._exit(70)  # deliberately bypass cleanup/checkpoint save
            return result
        store.commit_stage = commit
    services = Services(reasoning=Reasoning(), backbone=FixtureBackbone(store, values['fixture']), pdf=FixturePdf())
    access = AccessContext(principal_id=UUID(values['fixture']['principal_id']), namespace=values['fixture']['namespace'])
    try:
        assert asyncio.run(Worker(RuntimeApplication(store, services)).run_once(access))
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()
