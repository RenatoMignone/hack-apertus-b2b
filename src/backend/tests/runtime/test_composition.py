from dataclasses import replace

import pytest

from backend.application.adapters import Services
from backend.application.factories import ConfiguredEmbedding
from backend.config.runtime import RuntimeSettings
from backend.contracts.services import ServiceUnavailable
from backend.models.reasoning import KeeraChatModel, ModelSettings


def test_production_factories_match_runtime_signature_and_share_fetch_observations(tmp_path):
    from backend.data.artifacts.store import FilesystemArtifactStore
    settings = RuntimeSettings(reasoning_factory="backend.application.factories:reasoning",
        backbone_factory="backend.application.factories:backbone", web_factory="backend.application.factories:web",
        pdf_factory="backend.application.factories:pdf", web_user_agent="Navigator integration test",
        llm_name="apertus-v1-5-70b", llm_api_key="fixture-key", pdf_logo_path=str(tmp_path / "logo.png"))
    services = Services.configured(settings, object(), FilesystemArtifactStore(tmp_path))
    assert services.reasoning.tasks.model.settings.model_name == "apertus-v1-5-70b"
    assert services.backbone.repository.observations is services.web.fetcher.observations
    assert services.pdf.logo_path == tmp_path / "logo.png"
    with pytest.raises(ServiceUnavailable):
        ConfiguredEmbedding(settings).embed_query("No hidden embedding fallback")
    offline = Services.configured(replace(settings, mode="offline", llm_base_url="http://llm:8080/v1"),
        object(), FilesystemArtifactStore(tmp_path))
    assert offline.web is None and offline.reasoning.tasks.model.settings.local


@pytest.mark.parametrize("host", ["localhost", "127.0.0.1", "[::1]", "llm", "apertus"])
def test_model_and_runtime_offline_endpoint_policies_agree(host):
    from types import SimpleNamespace
    settings = RuntimeSettings(mode="offline", llm_base_url=f"http://{host}:8080/v1")
    KeeraChatModel(settings=ModelSettings(base_url=settings.llm_base_url, local=True))._validate_endpoint(
        SimpleNamespace(mode="offline"))


@pytest.mark.parametrize("url", ["https://gateway.keera.ch/api/v1", "http://llm.attacker.invalid/v1",
    "http://token@llm/v1", "file://llm/v1", "http://llm/v1?redirect=remote"])
def test_offline_endpoint_rejects_external_or_credential_urls(url):
    with pytest.raises(ValueError):
        RuntimeSettings(mode="offline", llm_base_url=url)
