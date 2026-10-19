"""Production composition wrappers for the three independently implemented lanes."""
from pathlib import Path
from threading import Lock

from backend.config.endpoints import local_inference_url
from backend.contracts.data import ModelConfiguration
from backend.contracts.services import ServiceUnavailable


class ConfiguredEmbedding:
    """Load the explicitly selected encoder on first search, never at API construction."""
    def __init__(self, settings):
        self.settings, self.loaded, self.lock = settings, None, Lock()
        self.configuration = None
        if settings.embedding_configuration:
            self.configuration = ModelConfiguration.model_validate_json(
                Path(settings.embedding_configuration).read_text(encoding="utf-8"))
            self.configuration.require_resolved()
            if self.configuration.test_only:
                raise ValueError("production factory refuses fixture embedding configurations")

    @property
    def config_hash(self):
        if self.configuration is None:
            raise ServiceUnavailable()
        return self.configuration.config_hash

    def _encoder(self):
        if self.configuration is None:
            raise ServiceUnavailable()
        with self.lock:
            if self.loaded is None:
                from backend.models.embeddings.configured import load_configured
                self.loaded = load_configured(self.configuration, self.settings)
        return self.loaded

    def embed_queries(self, texts):
        return self._encoder().embed_queries(texts)

    def embed_query(self, text):
        return self._encoder().embed_query(text)


class ConfiguredReranker:
    """Only the worker's first retrieval loads weights; API construction stays light."""
    def __init__(self, configuration, path, device):
        configuration.require_resolved()
        if configuration.test_only:
            raise ValueError("production factory refuses fixture reranker configurations")
        self.configuration, self.path, self.device = configuration, path, device
        self.loaded, self.lock = None, Lock()

    def score_with_details(self, query, passages):
        with self.lock:
            if self.loaded is None:
                from backend.models.reranking.local import load_reranker
                self.loaded = load_reranker(self.configuration, self.path, device=self.device)
        return self.loaded.score_with_details(query, passages)

    def score(self, query, passages):
        return [row["score"] for row in self.score_with_details(query, passages)]


def reasoning(*, settings, engine, artifacts):
    from backend.evidence import create_reasoning_services
    from backend.models.reasoning import ModelSettings
    return create_reasoning_services(ModelSettings(base_url=settings.llm_base_url, model_name=settings.llm_name,
        api_key=settings.llm_api_key, local=local_inference_url(settings.llm_base_url),
        max_output_tokens=settings.max_output_tokens))


def backbone(*, settings, engine, artifacts):
    from backend.data.backbone import create_backbone
    reranker = None
    if settings.reranker_configuration or settings.reranker_model_path:
        if not (settings.reranker_configuration and settings.reranker_model_path):
            raise ValueError("reranker configuration and local path must be supplied together")
        configuration = ModelConfiguration.model_validate_json(
            Path(settings.reranker_configuration).read_text(encoding="utf-8"))
        reranker = ConfiguredReranker(configuration, settings.reranker_model_path, settings.model_device)
    return create_backbone(engine, artifacts, ConfiguredEmbedding(settings), reranker=reranker)


def web(*, settings, engine, artifacts):
    from backend.ingestion.web import BraveDiscovery, create_web_tools
    discovery = None
    if settings.web_discovery_provider == "searxng" and settings.web_search_url:
        from backend.ingestion.searxng_discovery import SearXNGDiscovery
        discovery = SearXNGDiscovery(settings.web_search_url, engines=settings.web_search_engines)
    elif settings.web_discovery_provider == "browser" and settings.web_user_agent:
        from backend.ingestion.browser_discovery import BrowserDiscovery
        discovery = BrowserDiscovery(user_agent=settings.web_user_agent,
            executable_path=settings.web_browser_executable, timeout=settings.web_browser_timeout_seconds)
    elif settings.web_discovery_provider == "brave" and settings.brave_api_key:
        discovery = BraveDiscovery(settings.brave_api_key)
    return create_web_tools(discovery=discovery,
        user_agent=settings.web_user_agent or None, allowed_hosts=settings.web_allowed_hosts,
        crawler_python=settings.web_crawl4ai_python)


def pdf(*, settings, engine, artifacts):
    from backend.reports.rendering import create_pdf_renderer
    return create_pdf_renderer(logo_path=Path(settings.pdf_logo_path) if settings.pdf_logo_path else None)


def connect_observations(backbone_service, web_service):
    """Retain fetched originals when C registers its case-local research."""
    from backend.data.backbone import PostgresBackbone
    from backend.ingestion.web import PublicWebTools
    if (isinstance(backbone_service, PostgresBackbone) and isinstance(web_service, PublicWebTools)
            and web_service.fetcher is not None):
        backbone_service.repository.observations = web_service.fetcher.observations
