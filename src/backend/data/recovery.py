import json
import hashlib
import os
import shutil
import subprocess
from pathlib import Path

from backend.contracts.data import content_hash
from backend.data.host import DEPLOY


def file_hash(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def docker(arguments, *, capture=False):
    return subprocess.run(["docker", *arguments], check=True, capture_output=capture,
                          text=True, timeout=600)


def compose(*arguments, capture=False):
    command = ["compose", "-f", str(DEPLOY / "compose.yaml")]
    if os.getenv("NAVIGATOR_HOST_ENV"):
        command.extend(["--env-file", os.environ["NAVIGATOR_HOST_ENV"]])
    return docker([*command, "--profile", "observability", *arguments], capture=capture)


def backup(path: Path, *, include_traces=False):
    path = path.resolve()
    path.mkdir(parents=True, exist_ok=False)
    path.chmod(0o700)
    configuration = json.loads(compose("config", "--format", "json", capture=True).stdout)
    running = compose("ps", "--services", "--status", "running", capture=True).stdout.split()
    if not include_traces and set(running) & {"langfuse-web", "langfuse-worker", "clickhouse", "redis"}:
        raise ValueError("running tracing services require --include-traces for a recoverable backup")
    names = ["postgres-data", "artifacts"] + (["clickhouse-data", "clickhouse-logs", "redis-data"] if include_traces else [])
    image = configuration["services"]["postgres"]["image"]
    compose("stop")
    try:
        files = {}
        for name in names:
            volume = configuration["volumes"][name]["name"]
            docker(["run", "--rm", "--user", "0", "--entrypoint", "tar", "-v", f"{volume}:/data:ro",
                    "-v", f"{path}:/backup", image, "-czf", f"/backup/{name}.tar.gz", "-C", "/data", "."])
            files[f"{name}.tar.gz"] = file_hash(path / f"{name}.tar.gz")
        shutil.copy2(Path(os.environ.get("NAVIGATOR_HOST_ENV", str(DEPLOY / ".env"))), path / "host.env")
        (path / "host.env").chmod(0o600)
        files["host.env"] = file_hash(path / "host.env")
        manifest = {"format": 1, "volumes": names, "files": files,
                    "images": {name: service["image"] for name, service in configuration["services"].items()},
                    "compose_hash": content_hash((DEPLOY / "compose.yaml").read_bytes()), "includes_traces": include_traces}
        (path / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    finally:
        if running:
            compose("up", "-d", *running)


def restore(path: Path, *, include_traces=False):
    path = path.resolve()
    manifest = json.loads((path / "manifest.json").read_text())
    if manifest["format"] != 1 or manifest["includes_traces"] != include_traces:
        raise ValueError("backup format or trace inclusion does not match requested restore")
    if manifest["compose_hash"] != content_hash((DEPLOY / "compose.yaml").read_bytes()):
        raise ValueError("restore with the same deployment revision used for the backup")
    for name, digest in manifest["files"].items():
        if Path(name).name != name or file_hash(path / name) != digest:
            raise ValueError("backup integrity check failed")
    configuration = json.loads(compose("config", "--format", "json", capture=True).stdout)
    expected_images = {name: service["image"] for name, service in configuration["services"].items()}
    if expected_images != manifest["images"]:
        raise ValueError("container image digests must match the backup")
    for name in manifest["volumes"]:
        volume = configuration["volumes"][name]["name"]
        if subprocess.run(["docker", "volume", "inspect", volume], capture_output=True).returncode == 0:
            raise ValueError("restore requires a clean deployment with no existing target volumes")
    if compose("ps", "-q", capture=True).stdout.strip():
        raise ValueError("restore requires a deployment with no running containers")
    image = configuration["services"]["postgres"]["image"]
    host_environment = Path(os.environ.get("NAVIGATOR_HOST_ENV", str(DEPLOY / ".env")))
    if host_environment.exists() and host_environment.read_bytes() != (path / "host.env").read_bytes():
        raise ValueError("target host environment differs; preserve it and select a fresh NAVIGATOR_HOST_ENV path")
    for name in manifest["volumes"]:
        volume = configuration["volumes"][name]["name"]
        docker(["volume", "create", "--label", f"com.docker.compose.project={configuration['name']}",
                "--label", f"com.docker.compose.volume={name}", volume], capture=True)
        docker(["run", "--rm", "--user", "0", "--entrypoint", "tar", "-v", f"{volume}:/data",
                "-v", f"{path}:/backup:ro", image, "-xzf", f"/backup/{name}.tar.gz", "-C", "/data"])
    host_environment.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path / "host.env", host_environment)
    host_environment.chmod(0o600)
    for line in host_environment.read_text().splitlines():
        key, value = line.split("=", 1)
        os.environ[key] = value
    services = ["postgres", "minio", "storage-init"] + (["langfuse-web", "langfuse-worker", "clickhouse", "redis"] if include_traces else [])
    compose("up", "-d", *services)
