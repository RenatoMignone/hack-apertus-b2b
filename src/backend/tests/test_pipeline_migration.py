"""Upgrade old records in a separate disposable database, without destroying history."""
from uuid import UUID, uuid4

import psycopg
from psycopg import sql
import pytest
from alembic import command
from sqlalchemy import select, text

from backend.data import schema as t
from backend.data.database import engine_for, migrate, migration_config
from backend.data.fixtures import load_fixture
from backend.data.artifacts.store import FilesystemArtifactStore
from backend.tests.test_database import context, make_run

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("old_revision", ["0003_embedding_inputs", "0004_case_pipeline"])
def test_upgrade_preserves_legacy_data_and_installs_guards(database, tmp_path, old_revision):
    name = "navigator_upgrade_" + uuid4().hex
    admin_dsn = database.url.set(database="postgres").render_as_string(hide_password=False).replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(admin_dsn, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    engine = engine_for(database.url.set(database=name).render_as_string(hide_password=False))
    try:
        with engine.connect() as connection:
            config = migration_config()
            config.attributes["connection"] = connection
            command.upgrade(config, old_revision)
            connection.commit()
        # Reproduce the pre-U8 column shape; new tables must not exist yet.
        with engine.begin() as c:
            if old_revision == "0003_embedding_inputs":
                assert c.execute(text("SELECT to_regclass('cases.draft_reasons')")).scalar_one() is None
                c.execute(text("ALTER TABLE cases.reviews DROP COLUMN selection_hash"))
                c.execute(text("ALTER TABLE cases.exports DROP COLUMN format"))
        # Emulate the old writer's redundant chunk column while using current fixtures.
        with engine.begin() as c:
            c.execute(text("""
                CREATE FUNCTION public.historical_chunk_writer() RETURNS trigger LANGUAGE plpgsql AS $$
                BEGIN NEW.embedding_text=NEW.literal_text; RETURN NEW; END $$;
                CREATE TRIGGER historical_chunk_writer BEFORE INSERT ON retrieval.chunks
                  FOR EACH ROW EXECUTE FUNCTION public.historical_chunk_writer();
            """))
        fixture = load_fixture(engine, FilesystemArtifactStore(tmp_path), namespace="test_upgrade")
        with engine.begin() as c:
            c.execute(text("DROP TRIGGER historical_chunk_writer ON retrieval.chunks"))
            c.execute(text("DROP FUNCTION public.historical_chunk_writer()"))
        repository, case_id, input_id, run_id, _ = make_run(engine, fixture)
        evidence = None
        with engine.connect() as c:
            evidence = c.execute(select(t.spans.c.evidence_id)).scalars().first()
        pack = repository.freeze_pack(context(fixture), run_id, {"legacy": True}, [evidence])
        result = repository.record_result(context(fixture), case_id, pack, {"legacy": "result"}, expected_revision=0)
        query_plan = uuid4()
        with engine.begin() as c:
            c.execute(text("INSERT INTO cases.query_plans(query_plan_id,run_id,payload) VALUES(:id,:run,jsonb_build_object('old',true))"),
                      {"id": query_plan, "run": run_id})
            # Nonredundant discarded fields must also survive in the owner-only archive.
            c.execute(text("ALTER TABLE retrieval.chunks DISABLE TRIGGER immutable"))
            c.execute(text("UPDATE retrieval.chunks SET context_prefix='historical prefix'"))
            c.execute(text("ALTER TABLE retrieval.chunks ENABLE TRIGGER immutable"))
        migrate(engine)
        migrate(engine)
        assert repository.read_result(context(fixture), result)["payload"] == {"legacy": "result"}
        with pytest.raises(ValueError, match="legacy"):
            repository.review(context(fixture), result, expected_hash=repository.read_result(context(fixture), result)["result_hash"], decision="accepted")
        with engine.connect() as c:
            assert c.execute(select(t.inputs.c.input_id).where(t.inputs.c.input_id == input_id)).scalar_one() == input_id
            assert c.execute(text("SELECT count(*) FROM pg_policies WHERE schemaname='cases' AND policyname='pipeline_access'")).scalar_one() == 8
            assert c.execute(text("SELECT to_regclass('cases.query_plans')")).scalar_one() is None
            assert c.execute(text("SELECT payload FROM legacy.query_plans WHERE query_plan_id=:id"), {"id": query_plan}).scalar_one() == {"old": True}
            assert c.execute(text("SELECT count(*) FROM legacy.chunk_encoding WHERE context_prefix='historical prefix'")).scalar_one() == 4
            assert not c.execute(text("SELECT has_schema_privilege('navigator_app','legacy','USAGE')")).scalar_one()
            assert not c.execute(text("SELECT has_table_privilege('navigator_app','legacy.query_plans','SELECT')")).scalar_one()
    finally:
        engine.dispose()
        with psycopg.connect(admin_dsn, autocommit=True) as admin:
            admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))
