from contextlib import contextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import make_url

from backend.contracts.data import AccessContext


MIGRATION_LOCK = 781146250


def engine_for(url: str, *, runtime=False):
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    parsed = make_url(url)
    if parsed.host == "localhost":
        parsed = parsed.set(host="127.0.0.1")
    engine = create_engine(parsed, pool_pre_ping=True, hide_parameters=True, connect_args={"connect_timeout": 5})
    if runtime:
        # Only API/worker connections. Ingestion/migration engines retain their
        # own policies. Suspended terminals must not retain case locks forever.
        @event.listens_for(engine, "connect")
        def bounded_waits(connection, _record):
            previous = connection.autocommit
            connection.autocommit = True
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""SELECT set_config(name,
                        least(coalesce(nullif(setting::int,0),bound),bound)::text,false)
                        FROM pg_settings JOIN (VALUES
                          ('lock_timeout',5000),
                          ('idle_in_transaction_session_timeout',60000)
                        ) AS limits(name,bound) USING(name)""")
            finally:
                connection.autocommit = previous
    return engine


def migration_config() -> Config:
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).parent / "migrations"))
    return config


def migrate(engine) -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT pg_advisory_lock(:key)"), {"key": MIGRATION_LOCK})
        connection.commit()
        try:
            config = migration_config()
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
        finally:
            connection.rollback()
            connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": MIGRATION_LOCK})
            connection.commit()


def check_schema(engine, *, require_latest=False) -> None:
    expected = ScriptDirectory.from_config(migration_config()).get_current_head()
    with engine.connect() as connection:
        actual = MigrationContext.configure(connection).get_current_revision()
    # Only explicitly additive optional releases may coexist with the proven
    # core baseline. Feature services separately require their own tables.
    compatible = {'0008_live_corpus', '0009_case_memory', '0010_rich_outputs', '0011_capture_performance', '0012_membership_lookup'}
    if actual != expected and (require_latest or actual not in compatible or expected not in compatible):
        raise RuntimeError(f"schema revision {actual!r} is incompatible; maintainer must migrate to {expected}")


@contextmanager
def transaction(engine, access: AccessContext):
    with engine.begin() as connection:
        allowed = connection.execute(text("""
            SELECT 1 FROM ops.principals
            WHERE principal_id=:principal AND namespace=:namespace
              AND database_role=session_user AND active
        """), {"principal": access.principal_id, "namespace": access.namespace}).scalar()
        if not allowed:
            raise PermissionError("principal is not authenticated for this database role and namespace")
        connection.execute(text("SELECT set_config('navigator.principal', :principal, true)"),
                           {"principal": str(access.principal_id)})
        connection.execute(text("SELECT set_config('navigator.namespace', :namespace, true)"),
                           {"namespace": access.namespace})
        yield connection


def require_scope(connection, scope_id, write=False):
    allowed = connection.execute(text("SELECT ops.can_access(:scope, :write)"),
                                 {"scope": scope_id, "write": write}).scalar()
    if not allowed:
        raise PermissionError("scope is unavailable or access has been revoked")
