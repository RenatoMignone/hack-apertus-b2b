from uuid import uuid4

import boto3
from moto import mock_aws
import pytest

from backend.contracts.data import ArtifactRef, Span, validate_vector
from backend.data.artifacts.store import FilesystemArtifactStore, S3ArtifactStore
from backend.data.fixtures import FIXTURE_MODEL
from backend.data.retrieval.hybrid import fuse
from backend.observability.tracing import SafeTracer, sanitized


def test_unicode_offsets_and_false_quotes():
    body = "É😀 Glukose"
    Span(char_start=1, char_end=2, text="😀").validate_body(body)
    with pytest.raises(ValueError):
        Span(char_start=1, char_end=3, text="😀").validate_body(body)


@pytest.mark.parametrize("vector", [[0, 0, 0], [1, 2], [float("nan"), 1, 1], [float("inf"), 1, 1]])
def test_invalid_vectors(vector):
    with pytest.raises(ValueError):
        validate_vector(vector, 3)


def test_model_handoff_must_be_verified():
    with pytest.raises(ValueError):
        FIXTURE_MODEL.model_copy(update={"verified": False}).require_resolved()
    assert FIXTURE_MODEL.config_hash != FIXTURE_MODEL.model_copy(update={"revision": "2"}).config_hash


def test_filesystem_is_content_addressed_and_detects_corruption(tmp_path):
    store = FilesystemArtifactStore(tmp_path)
    reference = store.put(b"original", "text/plain")
    assert store.put(b"original", "text/plain") == reference
    assert store.read(reference) == b"original"
    (tmp_path / reference.key).write_bytes(b"modified")
    with pytest.raises(ValueError):
        store.read(reference)
    with pytest.raises(ValueError):
        store.read(ArtifactRef(key="../../outside", sha256=reference.sha256, byte_count=8, mime="text/plain"))


@mock_aws
def test_s3_round_trip_immutable_key_and_bucket_boundary():
    boto3.client("s3", region_name="us-east-1").create_bucket(Bucket="navigator")
    store = S3ArtifactStore("https://s3.amazonaws.com", "navigator", "test", "test")
    reference = store.put("glycémie".encode(), "text/plain")
    assert store.put("glycémie".encode(), "text/plain") == reference
    assert store.read(reference).decode() == "glycémie"


def test_fusion_includes_semantic_only_candidates_and_stable_ties():
    first, second, third = uuid4(), uuid4(), uuid4()
    result = fuse({first: {"rank": 1}, second: {"rank": 2}}, {third: {"rank": 1}, second: {"rank": 2}})
    assert result[0][0] == second
    assert {item[0] for item in result} == {first, second, third}
    assert fuse({first: {"rank": 1}}, {third: {"rank": 1}}) == sorted(
        [(first, 1/61), (third, 1/61)], key=lambda item: str(item[0]))


def test_tracing_masks_before_delivery_and_survives_outage():
    run_id = str(uuid4())
    assert sanitized({"run_id": run_id, "stage": "retrieval", "prompt": "private", "error_code": "private"}) == {
        "run_id": run_id, "stage": "retrieval"}
    def fail(metadata):
        raise RuntimeError("secret exception text")
    tracer = SafeTracer(fail)
    tracer.emit({"prompt": "private", "run_id": run_id})
    tracer.close()
    assert tracer.degraded
