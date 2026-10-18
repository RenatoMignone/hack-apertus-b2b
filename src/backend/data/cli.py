import argparse
import json
import os
from pathlib import Path
from uuid import UUID

from backend.config.settings import Settings
from backend.contracts.data import AccessContext, QueryPlan
from backend.data.database import check_schema, engine_for, migrate


def load_environment(path):
    if path:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                os.environ.setdefault(key, value)


def main():
    parser = argparse.ArgumentParser(prog="navigator")
    parser.add_argument("--env-file")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("db-migrate")
    commands.add_parser("validate-config")
    commands.add_parser("checkpoint-setup")
    commands.add_parser("fixture-load")
    host = commands.add_parser("host-init")
    host.add_argument("--output", default="src/backend/deploy/.env")
    host.add_argument("--image-lock", default="src/backend/deploy/images.lock.json")
    search = commands.add_parser("fixture-search")
    search.add_argument("manifest")
    search.add_argument("query")
    publish = commands.add_parser("snapshot-publish")
    publish.add_argument("snapshot", type=UUID)
    publish.add_argument("--principal", required=True, type=UUID)
    publish.add_argument("--namespace", required=True)
    publish.add_argument("--expected-active", type=UUID)
    principal = commands.add_parser("principal-create")
    principal.add_argument("role")
    principal.add_argument("namespace")
    principal.add_argument("--credentials-file", required=True)
    grant = commands.add_parser("scope-grant")
    grant.add_argument("principal", type=UUID)
    grant.add_argument("scope", type=UUID)
    grant.add_argument("--write", action="store_true")
    revoke = commands.add_parser("scope-revoke")
    revoke.add_argument("scope", type=UUID)
    for name in ("backup", "restore"):
        command = commands.add_parser(name)
        command.add_argument("path", type=Path)
        command.add_argument("--include-traces", action="store_true")
    arguments = parser.parse_args()
    load_environment(arguments.env_file)
    if arguments.command == "host-init":
        from backend.data.host import initialize_host
        initialize_host(Path(arguments.output), Path(arguments.image_lock))
        print("Generated private host environment; credentials were not printed.")
        return
    if arguments.command in {"backup", "restore"}:
        from backend.data.recovery import backup, restore
        (backup if arguments.command == "backup" else restore)(arguments.path, include_traces=arguments.include_traces)
        print("Recovery operation completed; verify a pinned case before declaring recovery.")
        return
    settings = Settings.from_env()
    if arguments.command == "principal-create":
        admin_url = os.getenv("ADMIN_DATABASE_URL")
        if not admin_url and os.getenv("POSTGRES_PASSWORD"):
            admin_url = f"postgresql://postgres:{os.environ['POSTGRES_PASSWORD']}@127.0.0.1:5432/navigator"
        if not admin_url:
            raise ValueError("principal-create requires ADMIN_DATABASE_URL or the private host environment")
        engine = engine_for(admin_url)
    else:
        engine = engine_for(settings.database_url)
    if arguments.command == "db-migrate":
        migrate(engine)
    else:
        check_schema(engine)
        if arguments.command == "validate-config":
            settings.artifact_store()
            print("Schema and storage configuration valid. Model inference remains unresolved until handoff.")
        elif arguments.command == "checkpoint-setup":
            if not settings.langgraph_database_url:
                raise ValueError("LANGGRAPH_DATABASE_URL is required")
            from backend.workflows.checkpoints import CheckpointPort
            CheckpointPort(engine, settings.langgraph_database_url).setup()
        elif arguments.command == "fixture-load":
            from backend.data.fixtures import load_fixture
            print(json.dumps(load_fixture(engine, settings.artifact_store()), indent=2))
        elif arguments.command == "fixture-search":
            from backend.data.fixtures import FixtureEmbedder
            from backend.data.repositories.snapshots import SnapshotRepository
            from backend.data.retrieval.hybrid import HybridSearch
            fixture = json.loads(Path(arguments.manifest).read_text(encoding="utf-8-sig"))
            access = AccessContext(principal_id=fixture["principal_id"], namespace=fixture["namespace"])
            snapshot = SnapshotRepository(engine).get(access, profile_id=UUID(fixture["profile_id"]), snapshot_id=UUID(fixture["snapshot_id"]))
            plan = QueryPlan(original_request=arguments.query, profile_id=fixture["profile_id"], snapshot_id=fixture["snapshot_id"],
                taxonomy_version_id=fixture["taxonomy_version_id"], build_id=snapshot["build_id"],
                embedding_config_hash=fixture["embedding_config_hash"])
            print(HybridSearch(engine, FixtureEmbedder()).search(access, plan).model_dump_json(indent=2))
        elif arguments.command == "snapshot-publish":
            from backend.data.repositories.snapshots import SnapshotRepository
            SnapshotRepository(engine).publish(AccessContext(principal_id=arguments.principal, namespace=arguments.namespace),
                arguments.snapshot, expected_active=arguments.expected_active)
        elif arguments.command == "principal-create":
            from backend.data.admin import provision_principal
            path = Path(arguments.credentials_file)
            if path.exists():
                raise ValueError("credentials file already exists")
            principal_id, password = provision_principal(engine, arguments.role, arguments.namespace)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8") as output:
                json.dump({"principal_id": str(principal_id), "role": arguments.role,
                           "namespace": arguments.namespace, "password": password}, output)
            path.chmod(0o600)
            print("Principal created; credentials saved privately to the specified file.")
        elif arguments.command == "scope-grant":
            from backend.data.admin import grant_scope
            grant_scope(engine, arguments.principal, arguments.scope, write=arguments.write)
        elif arguments.command == "scope-revoke":
            from backend.data.admin import revoke_scope
            revoke_scope(engine, arguments.scope)
    engine.dispose()


if __name__ == "__main__":
    main()
