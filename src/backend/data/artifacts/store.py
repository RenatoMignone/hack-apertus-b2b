from pathlib import Path
from tempfile import NamedTemporaryFile

import boto3
from botocore.exceptions import ClientError

from backend.contracts.data import ArtifactRef, content_hash


def verify(reference: ArtifactRef, data: bytes) -> bytes:
    if len(data) != reference.byte_count or content_hash(data) != reference.sha256:
        raise ValueError("artifact integrity check failed")
    return data


def object_key(digest: str) -> str:
    return f"sha256/{digest[:2]}/{digest}"


def check_key(reference: ArtifactRef) -> None:
    if reference.key != object_key(reference.sha256):
        raise ValueError("invalid content-addressed artifact key")


class FilesystemArtifactStore:
    def __init__(self, root: Path):
        self.root = root.resolve()

    def put(self, data: bytes, mime: str) -> ArtifactRef:
        digest = content_hash(data)
        reference = ArtifactRef(key=object_key(digest), sha256=digest, byte_count=len(data), mime=mime)
        target = self.root / reference.key
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            verify(reference, target.read_bytes())
            return reference
        with NamedTemporaryFile(dir=target.parent, delete=False) as temporary:
            temporary.write(data)
            temporary.flush()
            import os
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        try:
            temporary_path.replace(target)
        finally:
            temporary_path.unlink(missing_ok=True)
        return reference

    def read(self, reference: ArtifactRef) -> bytes:
        check_key(reference)
        target = (self.root / reference.key).resolve()
        if not target.is_relative_to(self.root):
            raise ValueError("artifact escaped storage root")
        return verify(reference, target.read_bytes())


class S3ArtifactStore:
    def __init__(self, endpoint: str, bucket: str, access_key: str, secret_key: str):
        self.bucket = bucket
        self.client = boto3.client("s3", endpoint_url=endpoint, region_name="us-east-1",
                                   aws_access_key_id=access_key, aws_secret_access_key=secret_key,
                                   config=boto3.session.Config(s3={"addressing_style": "path"},
                                                              retries={"max_attempts": 2},
                                                              connect_timeout=3, read_timeout=10))

    def put(self, data: bytes, mime: str) -> ArtifactRef:
        digest = content_hash(data)
        reference = ArtifactRef(key=object_key(digest), sha256=digest, byte_count=len(data), mime=mime)
        try:
            self.client.put_object(Bucket=self.bucket, Key=reference.key, Body=data,
                                   ContentType=mime, Metadata={"sha256": digest}, IfNoneMatch="*")
        except ClientError as error:
            if error.response["Error"]["Code"] not in {"PreconditionFailed", "412", "ConditionalRequestConflict", "409"}:
                raise
        self.read(reference)
        return reference

    def read(self, reference: ArtifactRef) -> bytes:
        check_key(reference)
        response = self.client.get_object(Bucket=self.bucket, Key=reference.key)
        with response["Body"] as body:
            return verify(reference, body.read())
