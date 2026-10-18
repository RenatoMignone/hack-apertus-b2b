import json
import argparse
import os
import shutil
import socket
import time
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import select

from backend.config.settings import Settings
from backend.contracts.data import AccessContext, ArtifactRef, QueryPlan
from backend.data import schema as tables
from backend.data.artifacts.store import S3ArtifactStore
from backend.data.cli import load_environment
from backend.data.database import check_schema, engine_for
from backend.data.fixtures import FixtureEmbedder
from backend.data.recovery import compose, restore
from backend.data.repositories.snapshots import SnapshotRepository
from backend.data.retrieval.hybrid import HybridSearch


def free_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("backup", nargs="?", default=".local/backup-validation")
    parser.add_argument("--include-traces", action="store_true")
    arguments = parser.parse_args()
    backup = Path(arguments.backup).resolve()
    project = "navigator-restore-" + uuid4().hex[:10]
    environment = Path(".local") / f"{project}.env"
    shutil.copy2(backup / "host.env", environment)
    environment.chmod(0o600)
    load_environment(str(environment))
    os.environ.update({"COMPOSE_PROJECT_NAME": project, "NAVIGATOR_HOST_ENV": str(environment.resolve()),
                       "POSTGRES_PORT": str(free_port()), "S3_PORT": str(free_port()), "S3_CONSOLE_PORT": str(free_port())})
    restore(backup, include_traces=arguments.include_traces)
    settings = Settings.from_env()
    engine = engine_for(settings.database_url.replace(":5432/", f":{os.environ['POSTGRES_PORT']}/"))
    for attempt in range(30):
        try:
            check_schema(engine)
            break
        except Exception:
            if attempt == 29:
                raise
            time.sleep(1)
    fixture = json.loads(Path(".local/fixture.json").read_text(encoding="utf-8-sig"))
    access = AccessContext(principal_id=fixture["principal_id"], namespace=fixture["namespace"])
    snapshot = SnapshotRepository(engine).get(access, profile_id=UUID(fixture["profile_id"]), snapshot_id=UUID(fixture["snapshot_id"]))
    plan = QueryPlan(original_request="glucose", snapshot_id=snapshot["snapshot_id"], build_id=snapshot["build_id"],
        profile_id=snapshot["profile_id"], taxonomy_version_id=snapshot["taxonomy_version_id"],
        embedding_config_hash=fixture["embedding_config_hash"])
    assert len(HybridSearch(engine, FixtureEmbedder()).search(access, plan).hits) == 4
    artifacts = S3ArtifactStore(f"http://127.0.0.1:{os.environ['S3_PORT']}", settings.s3_bucket,
        settings.s3_access_key, settings.s3_secret_key)
    with engine.connect() as connection:
        references = list(connection.execute(select(tables.artifacts)).mappings())
    for row in references:
        artifacts.read(ArtifactRef(key=row["storage_key"], sha256=row["sha256"], mime=row["mime"], byte_count=row["byte_count"]))
    if arguments.include_traces:
        from urllib.request import urlopen
        for attempt in range(60):
            try:
                with urlopen("http://127.0.0.1:3000/api/public/health", timeout=2) as response:
                    assert response.status == 200
                break
            except Exception:
                if attempt == 59:
                    raise
                time.sleep(1)
    engine.dispose()
    compose("down", "--volumes")
    print(f"Restored pinned fixture and verified {len(references)} artifact hashes on an isolated deployment; traces={arguments.include_traces}.")


if __name__ == "__main__":
    main()
