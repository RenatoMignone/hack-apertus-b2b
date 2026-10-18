"""Runtime-local fixtures; shared backend bootstrap remains untouched."""
import hashlib
import asyncio
import sys
from types import SimpleNamespace
from uuid import UUID

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from backend.application.adapters import Services
from backend.application.persistence.store import RuntimeStore
from backend.application.service import RuntimeApplication
from backend.config.runtime import IdentityBinding, RuntimeSettings
from backend.tests.runtime.fakes import FixtureBackbone, FixturePdf, FixtureReasoning
from backend.application.worker import Worker
from contextlib import asynccontextmanager


@pytest.fixture(scope="session")
def event_loop_policy():
    # Match the CLI worker's selector loop for Psycopg on Windows.
    return (asyncio.WindowsSelectorEventLoopPolicy() if sys.platform == "win32"
            else asyncio.DefaultEventLoopPolicy())


@pytest.fixture
def harness(database, corpus):
    fixture, artifacts = corpus
    token = "runtime-test-token"
    binding = IdentityBinding(token_sha256=hashlib.sha256(token.encode()).hexdigest(),
        principal_id=UUID(fixture["principal_id"]), namespace=fixture["namespace"])
    settings = RuntimeSettings(bindings=(binding,), default_profile_id=UUID(fixture["profile_id"]),
        template_version="synthetic-template-v1", renderer_version="synthetic-registration-fixture-v1")
    store = RuntimeStore(database, settings, artifacts)
    reasoning, backbone, pdf = FixtureReasoning(), FixtureBackbone(store, fixture), FixturePdf()
    services = Services(reasoning=reasoning, backbone=backbone, pdf=pdf)
    application = RuntimeApplication(store, services)
    saver = InMemorySaver()
    @asynccontextmanager
    async def checkpoint(access, run_id):
        yield saver, {"configurable": {"thread_id": str(run_id)}}
    worker = Worker(application, checkpoint_factory=checkpoint)
    class Registry:
        def __init__(self):
            self.settings = settings
        def application(self, supplied):
            assert supplied == binding
            return application
        def close(self):
            pass
    from backend.api.app import create_app
    return SimpleNamespace(store=store, access=binding.access, settings=settings, binding=binding, fixture=fixture,
        application=application, worker=worker, saver=saver, checkpoint=checkpoint, reasoning=reasoning,
        backbone=backbone, pdf=pdf, services=services, app=create_app(Registry()),
        headers={"Authorization": "Bearer " + token, "Idempotency-Key": "initial"})
