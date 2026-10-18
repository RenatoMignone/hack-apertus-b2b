import json
from dataclasses import replace

import httpx
import pytest

from backend.config.runtime import RuntimeSettings
from backend.contracts.data import ModelConfiguration
from backend.contracts.services import ServiceUnavailable
from backend.models.embeddings.hosted import ADAPTER_VERSION, HFEmbedder, endpoint_url, load_hf


ENDPOINT = "https://fixture.endpoints.huggingface.cloud"
REVISION = "914f7f89142e33e77833254d9c9b90c3cef7303b"


class Counter:
    def encode(self, text, **kwargs):
        return list(range(len(text)))


def configuration(**changes):
    return ModelConfiguration(role="embedding", logical_name="hosted-test", artifact="google/embeddinggemma-2",
        revision=REVISION, adapter_version=ADAPTER_VERSION, tokenizer=f"google/embeddinggemma-2@{REVISION}",
        input_limit=100, dimension=2, normalization="l2", query_template="query: {text}",
        document_template="title: {title} | text: {text}", precision="float32", license="fixture",
        verified=True).model_copy(update=changes)


def response(payload):
    return {"model": payload["model"], "usage": {"prompt_tokens": sum(map(len, payload["input"]))},
            "data": [{"index": i, "embedding": [3, 4]} for i in reversed(range(len(payload["input"])))]}


def test_query_and_documents_send_exact_formatted_inputs_without_server_prefixes():
    observed = []
    def handler(request):
        assert request.headers["authorization"] == "Bearer private-test-token"
        payload = json.loads(request.content)
        assert "prompt_name" not in payload and payload["encoding_format"] == "float"
        observed.extend(payload["input"])
        return httpx.Response(200, json=response(payload))
    encoder = HFEmbedder(configuration(), ENDPOINT, "private-test-token", Counter(),
                         transport=httpx.MockTransport(handler))
    assert encoder.embed_query("glucose") == [0.6, 0.8]
    documents = [encoder.document_input("monitoring", "Study"), encoder.document_input("sensors")]
    assert encoder.embed_documents(documents) == [[0.6, 0.8], [0.6, 0.8]]
    assert observed == ["query: glucose", *documents]
    assert encoder.config_hash == configuration().config_hash
    assert encoder.embed_documents([]) == []


def test_inputs_are_rejected_before_remote_truncation_and_requests_are_batched():
    batches = []
    def handler(request):
        payload = json.loads(request.content); batches.append(len(payload["input"]))
        return httpx.Response(200, json=response(payload))
    encoder = HFEmbedder(configuration(), ENDPOINT, "token", Counter(), transport=httpx.MockTransport(handler))
    with pytest.raises(ValueError, match="truncation"):
        encoder.embed_query("x" * 100)
    assert batches == []
    assert len(encoder.embed_documents(["document"] * 17)) == 17
    assert batches == [16, 1]


@pytest.mark.parametrize("status", [301, 401, 403, 429, 503])
def test_provider_failures_are_safe_and_never_follow_redirects_or_retry(status):
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(status, headers={"Location": "https://attacker.invalid"}, text="sensitive provider details")
    encoder = HFEmbedder(configuration(), ENDPOINT, "private-test-token", Counter(), transport=httpx.MockTransport(handler))
    with pytest.raises(ServiceUnavailable) as error:
        encoder.embed_query("query")
    assert len(calls) == 1 and "sensitive" not in str(error.value) and "private-test-token" not in str(error.value)


@pytest.mark.parametrize("change", [
    lambda d: d["usage"].update(prompt_tokens=0),
    lambda d: d.update(data=[]),
    lambda d: d["data"][0].update(index=1),
    lambda d: d["data"][0].update(embedding=[0, 0]),
    lambda d: d["data"][0].update(embedding=[True, 1]),
    lambda d: d["data"][0].update(embedding=[1, 2, 3]),
    lambda d: d.update(model="other-model"),
])
def test_invalid_vectors_usage_and_identity_cannot_enter_an_index(change):
    def handler(request):
        data = response(json.loads(request.content)); change(data)
        return httpx.Response(200, json=data)
    encoder = HFEmbedder(configuration(), ENDPOINT, "token", Counter(), transport=httpx.MockTransport(handler))
    with pytest.raises(ValueError):
        encoder.embed_query("query")


@pytest.mark.parametrize("url", ["http://fixture.endpoints.huggingface.cloud", "https://attacker.invalid",
    ENDPOINT + "?token=secret", "https://user:secret@fixture.endpoints.huggingface.cloud", ENDPOINT + "/other"])
def test_credentials_go_only_to_explicit_hf_https_endpoint(url):
    with pytest.raises(ValueError):
        endpoint_url(url)


def test_offline_and_missing_credentials_fail_before_network_or_tokenizer_work():
    with pytest.raises(ValueError, match="offline"):
        load_hf(configuration(), ENDPOINT, "token", "/not/read", revision=REVISION, mode="offline")
    with pytest.raises(ServiceUnavailable):
        HFEmbedder(configuration(), ENDPOINT, "", Counter())
    with pytest.raises(ValueError, match="rebuild"):
        HFEmbedder(configuration(adapter_version="local-runtime"), ENDPOINT, "token", Counter())
    with pytest.raises(ValueError, match="offline"):
        RuntimeSettings(mode="offline", llm_base_url="http://llm/v1", embedding_backend="hf")


def test_cli_and_runtime_share_encoder_selection_and_settings_hide_token(monkeypatch, tmp_path):
    from backend.application.factories import ConfiguredEmbedding
    from backend.models.embeddings.configured import load_configured
    observed = []
    def loader(config, endpoint, token, path, **kwargs):
        observed.append((config.config_hash, endpoint, path, kwargs["revision"]))
        return type("Encoder", (), {"embed_query": lambda self, text: [0.6, 0.8]})()
    monkeypatch.setattr("backend.models.embeddings.hosted.load_hf", loader)
    monkeypatch.setenv("EMBEDDING_BACKEND", "hf")
    monkeypatch.setenv("EMBEDDING_ENDPOINT_URL", ENDPOINT)
    monkeypatch.setenv("EMBEDDING_MODEL_REVISION", REVISION)
    monkeypatch.setenv("HF_TOKEN", "private-test-token")
    settings = RuntimeSettings.from_env()
    assert "private-test-token" not in repr(settings)
    path = tmp_path / "configuration.json"; path.write_text(configuration().model_dump_json())
    settings = replace(settings, embedding_configuration=str(path))
    load_configured(configuration(), settings)
    assert ConfiguredEmbedding(settings).embed_query("glucose") == [0.6, 0.8]
    assert observed[0] == observed[1]


def test_hosted_loader_rejects_revision_and_tokenizer_drift(tmp_path):
    with pytest.raises(ValueError, match="approved"):
        load_hf(configuration(), ENDPOINT, "token", "", revision="0" * 40)
    bad = tmp_path / "tokenizer.json"; bad.write_text("{}")
    with pytest.raises(ValueError, match="tokenizer bytes"):
        load_hf(configuration(dimension=768), ENDPOINT, "token", str(bad), revision=REVISION)
