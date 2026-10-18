"""Exercise the API/worker through a real restricted application DB role."""
from dataclasses import replace
from uuid import UUID, uuid4
import hashlib

import httpx
import pytest
from psycopg import sql

from backend.application.adapters import Services
from backend.application.persistence.store import RuntimeStore
from backend.application.service import RuntimeApplication
from backend.application.worker import Worker
from backend.api.app import create_app
from backend.config.runtime import IdentityBinding
from backend.data.admin import provision_principal, grant_scope
from backend.data.database import engine_for
from backend.tests.runtime.fakes import FixtureBackbone, FixtureReasoning

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_http_and_empty_pack_pipeline_under_application_role(harness):
    h = harness
    role = "runtime_test_" + uuid4().hex[:12]
    principal, password = provision_principal(h.store.engine, role, h.access.namespace)
    grant_scope(h.store.engine, principal, UUID(h.fixture["scope_id"]))
    engine = engine_for(h.store.engine.url.set(username=role, password=password).render_as_string(hide_password=False))
    try:
        token = "restricted-runtime-test"
        binding = IdentityBinding(token_sha256=hashlib.sha256(token.encode()).hexdigest(), principal_id=principal,
                                  namespace=h.access.namespace)
        settings = replace(h.settings, bindings=(binding,))
        store = RuntimeStore(engine, settings, h.store.artifacts)
        reasoning, backbone = FixtureReasoning(), FixtureBackbone(store, h.fixture)
        reasoning.empty = backbone.empty = True
        application = RuntimeApplication(store, Services(reasoning=reasoning, backbone=backbone))
        class Registry:
            def __init__(self):
                self.settings = settings
            def application(self, supplied):
                return application
            def close(self):
                pass
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=create_app(Registry())), base_url="http://test",
            headers={"Authorization": "Bearer " + token, "Idempotency-Key": "new"}) as client:
            response = await client.post("/api/v1/cases", json={"prompt": "Public synthetic research in Bern"})
            assert response.status_code == 201, response.text
            case = response.json()
            await Worker(application, checkpoint_factory=h.checkpoint).run_once(binding.access)
            run = await client.get(case["status_url"])
            assert run.json()["status"] == "succeeded", run.text
            detail = await client.get(f"/api/v1/cases/{case['case_id']}")
            assert detail.status_code == 200, detail.text
            assert detail.json()["revisions"][0]["coverage"]["resultKind"] == "no_match"
    finally:
        engine.dispose()
        with h.store.engine.begin() as connection:
            connection.connection.driver_connection.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
            connection.connection.driver_connection.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))
