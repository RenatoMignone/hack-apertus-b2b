"""Prove optional release migrations do not force shared-host upgrades at startup."""
from uuid import uuid4
import os
import psycopg
from psycopg import sql
import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from alembic import command
from backend.data.database import engine_for, migration_config, check_schema, migrate


@pytest.mark.integration
def test_0008_core_is_supported_until_optional_features_are_activated():
    dsn = os.getenv('NAVIGATOR_TEST_ADMIN_DSN')
    if not dsn:
        pytest.skip('explicit disposable test admin DSN required')
    name = 'navigator_test_' + uuid4().hex
    with psycopg.connect(dsn, autocommit=True) as c:
        c.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
    engine = engine_for(make_url(dsn).set(database=name).render_as_string(hide_password=False))
    try:
        with engine.connect() as c:
            config = migration_config()
            config.attributes['connection'] = c
            command.upgrade(config, '0008_live_corpus')
        check_schema(engine)
        with pytest.raises(RuntimeError, match='maintainer must migrate'):
            check_schema(engine, require_latest=True)
        with engine.connect() as c:
            assert c.execute(text("SELECT to_regclass('cases.memory_profiles')")).scalar_one() is None
            assert c.execute(text("SELECT to_regclass('cases.business_contexts')")).scalar_one() is None
        migrate(engine)
        check_schema(engine, require_latest=True)
    finally:
        engine.dispose()
        with psycopg.connect(dsn, autocommit=True) as c:
            c.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))
