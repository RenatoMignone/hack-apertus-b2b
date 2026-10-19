"""Explicit local browser smoke server. Disposable DB; synthetic sources/embeddings.

PYTHONPATH=src NAVIGATOR_TEST_ADMIN_DSN=postgresql://TEST_ADMIN@localhost:PORT/postgres \
  python -m backend.tests.runtime.smoke
"""
import asyncio
import argparse
import json
import os
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


async def serve(engine, artifacts, fixture, principal, *, port=8000, clarify=False, rich_outputs=False, model_settings=None, checkpoint_url=None, receipt=None):
    token = "synthetic-browser-smoke"
    binding = IdentityBinding(token_sha256=hashlib.sha256(token.encode()).hexdigest(),
        principal_id=principal, namespace=fixture["namespace"])
    settings = RuntimeSettings(mode="connected" if model_settings else "offline",
        llm_name=model_settings.model_name if model_settings else "apertus-v1-5-8b",
        llm_base_url=model_settings.base_url if model_settings else "http://llm:8080/v1",
        langgraph_database_url=checkpoint_url, bindings=(binding,),
        default_profile_id=UUID(fixture["profile_id"]), cors_origins=("http://127.0.0.1:5173", "http://localhost:5173",
            "http://127.0.0.1:5174", "http://localhost:5174"),
        rich_outputs_enabled=rich_outputs, case_memory_enabled=rich_outputs,
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
    services = Services(reasoning=create_reasoning_services(
        model_settings or ModelSettings(base_url=settings.llm_base_url, local=True),
        transport=None if model_settings else httpx.MockTransport(transport), receipt=receipt),
        backbone=create_backbone(engine, artifacts, FixtureEmbedder()), pdf=create_pdf_renderer())
    if rich_outputs:
        from backend.application.case_memory import CaseMemory
        from backend.reports.rendering.pptx import TemplatePptxRenderer
        services.memory = CaseMemory(store, FixtureEmbedder())
        services.pptx = TemplatePptxRenderer()
    application = RuntimeApplication(store, services)
    saver = InMemorySaver()
    @asynccontextmanager
    async def checkpoints(access, run_id):
        yield saver, {"configurable": {"thread_id": str(run_id)}}
    worker = Worker(application, checkpoint_factory=None if checkpoint_url else checkpoints)
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
    print("LOCAL SYNTHETIC SOURCES/EMBEDDINGS. Model: " + ("actual Apertus" if model_settings else "scripted fixture") +
          "; checkpoints: " + ("PostgreSQL" if checkpoint_url else "memory") +
          ". Access token: synthetic-browser-smoke", flush=True)
    try:
        await uvicorn.Server(uvicorn.Config(create_app(Registry()), host="127.0.0.1", port=port)).serve()
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)


def main(argv=()):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--clarify', action='store_true', help='Exercise a free-text blocking clarification before research.')
    parser.add_argument('--rich-outputs', action='store_true', help='Exercise optional plans/PPTX controls; keep fictional cases out of comparison history.')
    parser.add_argument('--real-model-env', type=Path, help='Opt in to actual configured Apertus with synthetic public-safe inputs only.')
    parser.add_argument('--postgres-checkpoints', action='store_true', help='Set up checkpoints ONLY inside the newly created disposable database.')
    parser.add_argument('--receipt', type=Path, help='JSONL model timings/token counts; no prompts or responses.')
    args = parser.parse_args(argv)
    if args.real_model_env and args.clarify:
        parser.error('--clarify forces scripted questions and cannot accompany --real-model-env')
    model_settings = None
    if args.real_model_env:
        from backend.data.cli import load_environment
        load_environment(args.real_model_env)
        model_settings = ModelSettings(base_url=os.environ['LLM_BASE_URL'],
            model_name=os.environ['LLM_NAME'], api_key=os.environ['LLM_API_KEY'])
    def receipt(value):
        if args.receipt:
            args.receipt.parent.mkdir(parents=True, exist_ok=True)
            with args.receipt.open('a') as stream:
                stream.write(json.dumps(value) + '\n')

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
            fixture = load_fixture(database, artifacts, named_sources=bool(model_settings))
            principal, password = provision_principal(database, role, fixture["namespace"])
            provisioned = True
            grant_scope(database, principal, UUID(fixture["scope_id"]))
            application_engine = engine_for(database.url.set(username=role, password=password).render_as_string(hide_password=False))
            checkpoint_url = None
            if args.postgres_checkpoints:
                from backend.workflows.checkpoints import CheckpointPort
                checkpoint_url = database.url.render_as_string(hide_password=False).replace('postgresql+psycopg://', 'postgresql://')
                CheckpointPort(database, checkpoint_url).setup()
            try:
                asyncio.run(serve(application_engine, artifacts, fixture, principal, port=args.port, clarify=args.clarify, rich_outputs=args.rich_outputs, model_settings=model_settings,
                    checkpoint_url=checkpoint_url, receipt=receipt))
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
