import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database_url: str
    langgraph_database_url: str | None
    artifact_root: Path
    artifact_backend: str
    s3_endpoint: str | None
    s3_bucket: str
    s3_access_key: str | None
    s3_secret_key: str | None

    @classmethod
    def from_env(cls):
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL is required; credentials stay in your environment")
        return cls(database_url, os.getenv("LANGGRAPH_DATABASE_URL"),
                   Path(os.getenv("ARTIFACT_ROOT", ".local/artifacts")),
                   os.getenv("ARTIFACT_BACKEND", "filesystem"), os.getenv("S3_ENDPOINT_URL"),
                   os.getenv("S3_BUCKET", "navigator"), os.getenv("S3_ACCESS_KEY_ID"),
                   os.getenv("S3_SECRET_ACCESS_KEY"))

    def artifact_store(self):
        from backend.data.artifacts.store import FilesystemArtifactStore, S3ArtifactStore

        if self.artifact_backend == "filesystem":
            return FilesystemArtifactStore(self.artifact_root)
        if self.artifact_backend == "s3" and self.s3_endpoint and self.s3_access_key and self.s3_secret_key:
            return S3ArtifactStore(self.s3_endpoint, self.s3_bucket, self.s3_access_key, self.s3_secret_key)
        raise ValueError("ARTIFACT_BACKEND must be filesystem or a fully configured s3 adapter")
