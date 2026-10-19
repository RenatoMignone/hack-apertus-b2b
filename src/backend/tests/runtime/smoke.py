"""Explicit local browser smoke server. Disposable DB; synthetic model/embedding only.

PYTHONPATH=src NAVIGATOR_TEST_ADMIN_DSN=postgresql://TEST_ADMIN@localhost:PORT/postgres \
  python -m backend.tests.runtime.smoke
"""
import asyncio
import argparse
import json
import sys
from contextlib import asynccontextmanager
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID, uuid4

import httpx
import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url
import uvicorn
from langgraph.checkpoint.memory import InMemorySaver

from backend.api.app import create_app
from backend.application.adapters import Services
from backend.application.persistence.store import RuntimeStore
from backend.application.service import RuntimeApplication
from backend.application.worker import Worker
from backend.config.runtime import IdentityBinding, RuntimeSettings
from backend.data.admin import grant_scope, provision_principal
from backend.data.artifacts.store import FilesystemArtifactStore
from backend.data.database import engine_for, migrate
from backend.data.fixtures import FixtureEmbedder, load_fixture
from backend.data.backbone import create_backbone
from backend.evidence import create_reasoning_services
from backend.models.reasoning import ModelSettings
from backend.reports.rendering import create_pdf_renderer
from backend.tests.runtime.test_integrated_lanes import synthetic_transport
from backend.tests.run import require_test_admin_dsn


async def serve(engine, artifacts, fixture, principal, *, port=8000, clarify=False):
    token = "synthetic-browser-smoke"
    binding = IdentityBinding(token_sha256=hashlib.sha256(token.encode()).hexdigest(),
        principal_id=principal, namespace=fixture["namespace"])
    settings = RuntimeSettings(mode="offline", llm_base_url="http://llm:8080/v1", bindings=(binding,),
        default_profile_id=UUID(fixture["profile_id"]), cors_origins=("http://127.0.0.1:5173", "http://localhost:5173",
            "http://127.0.0.1:5174", "http://localhost:5174"),
        template_version="challenge-v1", renderer_version="reportlab-v1",
        pdf_factory="backend.application.factories:pdf")
    store = RuntimeStore(engine, settings, artifacts)
    def transport(request):
        response = synthetic_transport(request)
        body = json.loads(request.content)
        if clarify and 'TASK: interpret\n' in body['messages'][0]['content'] and 'Clarification:' not in json.loads(body['messages'][1]['content'])['message']:
            result = response.json()
            content = json.loads(result['choices'][0]['message']['content'])
            content['blocking_questions'] = ['Which sensor application should this synthetic search focus on?']
            result['choices'][0]['message']['content'] = json.dumps(content)
            return httpx.Response(200, json=result)
        return response
    services = Services(reasoning=create_reasoning_services(ModelSettings(base_url=settings.llm_base_url, local=True),
        transport=httpx.MockTransport(transport)),
        backbone=create_backbone(engine, artifacts, FixtureEmbedder()), pdf=create_pdf_renderer())
    application = RuntimeApplication(store, services)
    saver = InMemorySaver()
    @asynccontextmanager
    async def checkpoints(access, run_id):
        yield saver, {"configurable": {"thread_id": str(run_id)}}
    worker = Worker(application, checkpoint_factory=checkpoints)
    class Registry:
        def __init__(self):
            self.settings = settings
        def application(self, supplied):
            if supplied != binding:
                raise PermissionError()
            return application
        def close(self):
            pass
    async def work():
        while True:
            await worker.run_once(binding.access)
            await asyncio.sleep(0.1)
    task = asyncio.create_task(work())
    print("LOCAL SYNTHETIC SMOKE ONLY. Access token: synthetic-browser-smoke", flush=True)
    try:
        await uvicorn.Server(uvicorn.Config(create_app(Registry()), host="127.0.0.1", port=port)).serve()
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)


def main(argv=()):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--clarify', action='store_true', help='Exercise a free-text blocking clarification before research.')
    args = parser.parse_args(argv)
    admin_dsn = require_test_admin_dsn()
    name, role = "navigator_browser_" + uuid4().hex, "browser_" + uuid4().hex[:12]
    with psycopg.connect(admin_dsn, autocommit=True) as c:
        c.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    database = engine_for(make_url(admin_dsn).set(database=name).render_as_string(hide_password=False))
    application_engine = None
    provisioned = False
    try:
        migrate(database)
        with TemporaryDirectory(prefix="navigator-browser-") as folder:
            artifacts = FilesystemArtifactStore(Path(folder))
            fixture = load_fixture(database, artifacts)
            principal, password = provision_principal(database, role, fixture["namespace"])
            provisioned = True
            grant_scope(database, principal, UUID(fixture["scope_id"]))
            application_engine = engine_for(database.url.set(username=role, password=password).render_as_string(hide_password=False))
            try:
                asyncio.run(serve(application_engine, artifacts, fixture, principal, port=args.port, clarify=args.clarify))
            except KeyboardInterrupt:
                pass
    finally:
        if application_engine:
            application_engine.dispose()
        if provisioned:
            with database.begin() as c:
                c.connection.driver_connection.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
                c.connection.driver_connection.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))
        database.dispose()
        with psycopg.connect(admin_dsn, autocommit=True) as c:
            c.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))


if __name__ == "__main__":
    main(sys.argv[1:])
