import json
import secrets
import subprocess
from pathlib import Path


DEPLOY = Path(__file__).parents[1] / "deploy"
IMAGES = {
    "POSTGRES_IMAGE": "pgvector/pgvector:0.8.2-pg17-bookworm",
    "MINIO_IMAGE": "cgr.dev/chainguard/minio:latest",
    "MINIO_MC_IMAGE": "cgr.dev/chainguard/minio:latest",
    "REDIS_IMAGE": "redis:7.4.2-alpine",
    "CLICKHOUSE_IMAGE": "clickhouse/clickhouse-server:25.12",
    "LANGFUSE_WEB_IMAGE": "docker.langfuse.com/langfuse/langfuse:4",
    "LANGFUSE_WORKER_IMAGE": "docker.langfuse.com/langfuse/langfuse-worker:4",
}


def resolve_image(image):
    result = subprocess.run(["docker", "buildx", "imagetools", "inspect", image,
                             "--format", "{{json .Manifest}}"], check=True, capture_output=True, text=True, timeout=120)
    manifest = json.loads(result.stdout)
    digest = manifest["digest"]
    return image + "@" + digest


def initialize_host(env_path: Path, image_lock: Path):
    if env_path.exists():
        raise ValueError("host environment already exists; secrets are never overwritten")
    images = json.loads(image_lock.read_text()) if image_lock.exists() else {key: resolve_image(image) for key, image in IMAGES.items()}
    if set(images) != set(IMAGES) or any("@sha256:" not in image for image in images.values()):
        raise ValueError("image lock must contain every service pinned by digest")
    values = {**images, **{key: secrets.token_hex(24) for key in (
        "POSTGRES_PASSWORD", "NAVIGATOR_MIGRATOR_PASSWORD", "LANGGRAPH_PASSWORD", "LANGFUSE_DB_PASSWORD",
        "MINIO_ROOT_PASSWORD", "S3_SECRET_ACCESS_KEY", "TRACE_S3_SECRET_KEY", "REDIS_PASSWORD",
        "CLICKHOUSE_PASSWORD", "NEXTAUTH_SECRET", "LANGFUSE_SALT")},
        "LANGFUSE_ENCRYPTION_KEY": secrets.token_hex(32), "MINIO_ROOT_USER": "navigator-root",
        "S3_ACCESS_KEY_ID": "navigator-app", "TRACE_S3_ACCESS_KEY": "langfuse-traces"}
    values.update({"DATABASE_URL": f"postgresql+psycopg://navigator_migrator:{values['NAVIGATOR_MIGRATOR_PASSWORD']}@localhost:5432/navigator",
                   "LANGGRAPH_DATABASE_URL": f"postgresql://langgraph:{values['LANGGRAPH_PASSWORD']}@localhost:5432/langgraph",
                   "ARTIFACT_BACKEND": "s3", "S3_ENDPOINT_URL": "http://localhost:9000", "S3_BUCKET": "navigator",
                   "LLM_NAME": "", "LLM_BASE_URL": "", "LLM_API_KEY": ""})
    env_path.parent.mkdir(parents=True, exist_ok=True)
    with env_path.open("x", encoding="utf-8", newline="\n") as output:
        output.write("".join(f"{key}={value}\n" for key, value in values.items()))
    env_path.chmod(0o600)
    return images
