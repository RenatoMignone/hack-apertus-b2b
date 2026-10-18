import os
from uuid import uuid4

import psycopg
from psycopg import sql
import pytest
from sqlalchemy.engine import make_url

from backend.data.database import engine_for, migrate
from backend.data.artifacts.store import FilesystemArtifactStore
from backend.data.fixtures import load_fixture


@pytest.fixture(scope="session")
def database():
    admin_url = os.getenv("NAVIGATOR_TEST_ADMIN_DSN")
    if not admin_url:
        pytest.skip("set NAVIGATOR_TEST_ADMIN_DSN to enable disposable PostgreSQL integration tests")
    name = "navigator_test_" + uuid4().hex
    with psycopg.connect(admin_url, autocommit=True) as connection:
        connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    url = make_url(admin_url).set(database=name)
    engine = engine_for(url.render_as_string(hide_password=False))
    migrate(engine)
    try:
        yield engine
    finally:
        engine.dispose()
        with psycopg.connect(admin_url, autocommit=True) as connection:
            connection.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))


@pytest.fixture
def corpus(database, tmp_path):
    artifacts = FilesystemArtifactStore(tmp_path)
    fixture = load_fixture(database, artifacts, namespace="test_" + uuid4().hex[:12])
    return fixture, artifacts
