"""Read-only readiness checks; never start workers, migrate, or call model APIs."""
import argparse
import os
from pathlib import Path

from backend.config.runtime import RuntimeSettings
from backend.config.settings import Settings
from backend.data.cli import load_environment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--network", action="store_true", help="Also perform read-only DB/S3 checks")
    args = parser.parse_args()
    load_environment(args.env_file)
    failures = []

    def check(label, operation):
        try:
            operation()
        except Exception as error:
            failures.append(label)
            # Provider/SQL exception messages can contain credentials or private data.
            print(f"MISSING/FAILED {label} ({type(error).__name__})")
        else:
            print(f"OK {label}")

    def required(value):
        if not value:
            raise ValueError()

    try:
        runtime = RuntimeSettings.from_env()
    except Exception as error:
        print(f"MISSING/FAILED runtime settings ({type(error).__name__})")
        return 1
    check("operator bindings", lambda: required(runtime.bindings))
    for binding in runtime.bindings:
        check("application DSN", lambda: required(os.getenv(binding.database_url_env)))
        if binding.namespace.startswith(("fixture", "test")):
            print("NOTE fixture/test identity: pilot namespace and grants need owner confirmation")
    check("published profile configured", lambda: required(runtime.default_profile_id))
    check("checkpoint DSN configured", lambda: required(runtime.langgraph_database_url))
    check("reasoning endpoint/key configured (not contacted)",
          lambda: required(runtime.llm_base_url and runtime.llm_api_key))

    def embedding():
        from backend.application.factories import ConfiguredEmbedding
        configured = ConfiguredEmbedding(runtime)
        required(configured.configuration)
        if runtime.embedding_backend == "hf":
            from backend.models.embeddings.configured import load_configured
            load_configured(configured.configuration, runtime)  # Local tokenizer/hash only.
        else:
            required(runtime.embedding_model_path and Path(runtime.embedding_model_path).exists())
    check("embedding configuration and local assets (not contacted)", embedding)
    check("PDF logo exists", lambda: required(Path(runtime.pdf_logo_path).is_file()))

    def artifacts():
        settings = Settings.from_env()
        required(settings.artifact_backend == "s3")
        settings.artifact_store()  # Constructs the client; no network calls.
    check("shared S3 configuration", artifacts)
    if not args.network:
        print("NOTE network checks skipped; use --network with the SSH tunnel open")
    else:
        from sqlalchemy import text
        from backend.data.database import engine_for

        for binding in runtime.bindings:
            def database():
                from alembic.script import ScriptDirectory
                from backend.data.database import migration_config
                engine = engine_for(os.environ[binding.database_url_env])
                try:
                    with engine.connect() as connection:
                        connection.execute(text("SET TRANSACTION READ ONLY"))
                        connection.execute(text("SET LOCAL statement_timeout = '5s'"))
                        revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                        required(revision == ScriptDirectory.from_config(migration_config()).get_current_head())
                        required(connection.execute(text("SELECT 1 FROM ops.principals WHERE "
                            "principal_id=:id AND namespace=:ns AND database_role=session_user AND active"),
                            {"id": binding.principal_id, "ns": binding.namespace}).scalar())
                finally:
                    engine.dispose()
            check("database schema and authenticated identity", database)

        def checkpoints():
            import psycopg
            with psycopg.connect(runtime.langgraph_database_url, connect_timeout=5,
                                 options="-c default_transaction_read_only=on -c statement_timeout=5000") as connection:
                for table in ("checkpoint_migrations", "checkpoints", "checkpoint_blobs", "checkpoint_writes"):
                    connection.execute(f"SELECT 1 FROM {table} LIMIT 0")
        if runtime.langgraph_database_url:
            check("checkpoint tables readable (write access not tested)", checkpoints)

        def storage():
            store = Settings.from_env().artifact_store()
            required(hasattr(store, "client"))
            store.client.head_bucket(Bucket=store.bucket)
        check("S3 bucket reachable with configured credentials", storage)
        print("NOTE bucket HEAD does not verify source-object reads or report writes")
    print("NOTE profile publication/scope visibility, model calls and full-case acceptance remain separate checks")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
