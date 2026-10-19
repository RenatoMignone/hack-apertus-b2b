"""Runtime-only settings. Secret values never enter run configuration or reprs."""
import json
import os
from dataclasses import dataclass, field
from uuid import UUID

from backend.contracts.data import AccessContext
from backend.config.endpoints import local_inference_url


@dataclass(frozen=True)
class IdentityBinding:
    token_sha256: str = field(repr=False)
    principal_id: UUID
    namespace: str
    database_url_env: str = "DATABASE_URL"

    @property
    def access(self):
        return AccessContext(principal_id=self.principal_id, namespace=self.namespace)


@dataclass(frozen=True)
class RuntimeSettings:
    mode: str = "connected"
    bindings: tuple[IdentityBinding, ...] = field(default=(), repr=False)
    default_profile_id: UUID | None = None
    corpus_mode: str = "published"
    live_taxonomy_version_id: UUID | None = None
    reasoning_factory: str = ""
    backbone_factory: str = ""
    web_factory: str = ""
    pdf_factory: str = ""
    llm_name: str = "apertus-v1-5-8b"
    llm_base_url: str = "https://gateway.keera.ch/api/v1"
    llm_api_key: str = field(default="", repr=False)
    langgraph_database_url: str = field(default="", repr=False)
    cors_origins: tuple[str, ...] = ()
    capture_timeout_seconds: int = 30
    deadline_seconds: int = 600
    max_research_rounds: int = 3
    max_output_tokens: int = 4096
    max_tool_calls: int = 11
    max_request_bytes: int = 128_000
    worker_lease_seconds: int = 60
    template_version: str = "unconfigured"
    renderer_version: str = "unconfigured"
    langfuse_url: str = ""
    langfuse_public_key: str = field(default="", repr=False)
    langfuse_secret_key: str = field(default="", repr=False)
    pdf_logo_path: str = ""
    embedding_configuration: str = ""
    embedding_model_path: str = ""
    embedding_backend: str = "local"
    embedding_endpoint_url: str = ""
    embedding_model_revision: str = ""
    embedding_tokenizer_path: str = ""
    hf_token: str = field(default="", repr=False)
    reranker_configuration: str = ""
    reranker_model_path: str = ""
    model_device: str = "cpu"
    web_user_agent: str = ""
    web_allowed_hosts: tuple[str, ...] = ()
    brave_api_key: str = field(default="", repr=False)
    web_discovery_provider: str = "searxng"
    web_search_url: str = ""
    web_search_engines: tuple[str, ...] = ("duckduckgo", "yahoo")
    web_browser_executable: str = ""
    web_browser_timeout_seconds: int = 25
    web_crawl4ai_python: str = ""
    rich_outputs_enabled: bool = False
    pptx_template_path: str = ""
    case_memory_enabled: bool = False
    case_memory_min_score: float = 50

    def __post_init__(self):
        if not 1 <= self.capture_timeout_seconds <= 120:
            raise ValueError("RUNTIME_CAPTURE_TIMEOUT_SECONDS must be 1–120")
        if self.corpus_mode not in {"live", "published"}:
            raise ValueError("RUNTIME_CORPUS_MODE must be live or published")
        if not 0 <= self.case_memory_min_score <= 100:
            raise ValueError('case memory minimum similarity must be 0–100')
        if self.mode not in {"connected", "offline"} or not 1 <= self.max_research_rounds <= 3:
            raise ValueError("invalid deployment mode or research budget")
        if not 1 <= self.deadline_seconds <= 3600 or not 0 <= self.max_tool_calls <= 30:
            raise ValueError("invalid runtime deadline or tool budget")
        if not 1 <= self.max_output_tokens <= 65536 or not 4096 <= self.max_request_bytes <= 1_000_000:
            raise ValueError("invalid token or input budget")
        if not 15 <= self.worker_lease_seconds <= 3600:
            raise ValueError("worker lease must be 15–3600 seconds")
        if self.mode == "offline" and not local_inference_url(self.llm_base_url):
            raise ValueError("offline inference requires an explicit local model endpoint")
        if self.embedding_backend not in {"local", "hf"}:
            raise ValueError("EMBEDDING_BACKEND must be local or hf")
        if self.web_discovery_provider not in {"searxng", "browser", "brave"}:
            raise ValueError("WEB_DISCOVERY_PROVIDER must be searxng, browser or brave")
        if not 1 <= self.web_browser_timeout_seconds <= 60:
            raise ValueError("WEB_BROWSER_TIMEOUT_SECONDS must be 1–60")
        if self.mode == "offline" and self.embedding_backend == "hf":
            raise ValueError("hosted embeddings are forbidden offline")
        if "*" in self.cors_origins:
            raise ValueError("CORS requires explicit origins")
        import re
        if any(not re.fullmatch(r"[a-f0-9]{64}", b.token_sha256) for b in self.bindings):
            raise ValueError("identity bindings require token SHA-256 digests, not raw tokens")
        if len({b.token_sha256 for b in self.bindings}) != len(self.bindings):
            raise ValueError("duplicate authentication binding")

    @classmethod
    def from_env(cls):
        if any(os.getenv(key, "").lower() in {"1", "true", "yes"}
               for key in ("LANGSMITH_TRACING", "LANGCHAIN_TRACING_V2")):
            raise ValueError("Automatic external tracing must be disabled; use local masked Langfuse")
        bindings = tuple(IdentityBinding(principal_id=UUID(item["principal_id"]), namespace=item["namespace"],
            token_sha256=item["token_sha256"], database_url_env=item.get("database_url_env", "DATABASE_URL"))
            for item in json.loads(os.getenv("RUNTIME_AUTH_BINDINGS", "[]")))
        return cls(mode=os.getenv("DEPLOYMENT_MODE", "connected"), bindings=bindings,
            default_profile_id=UUID(os.environ["RUNTIME_PROFILE_ID"]) if os.getenv("RUNTIME_PROFILE_ID") else None,
            corpus_mode=os.getenv("RUNTIME_CORPUS_MODE", "published"),
            live_taxonomy_version_id=UUID(os.environ["RUNTIME_LIVE_TAXONOMY_ID"]) if os.getenv("RUNTIME_LIVE_TAXONOMY_ID") else None,
            reasoning_factory=os.getenv("RUNTIME_REASONING_FACTORY", ""),
            backbone_factory=os.getenv("RUNTIME_BACKBONE_FACTORY", ""), web_factory=os.getenv("RUNTIME_WEB_FACTORY", ""),
            pdf_factory=os.getenv("RUNTIME_PDF_FACTORY", ""), llm_name=os.getenv("LLM_NAME", "apertus-v1-5-8b"),
            llm_base_url=os.getenv("LLM_BASE_URL", "https://gateway.keera.ch/api/v1"),
            llm_api_key=os.getenv("LLM_API_KEY", ""), langgraph_database_url=os.getenv("LANGGRAPH_DATABASE_URL", ""),
            cors_origins=tuple(x.strip() for x in os.getenv("RUNTIME_CORS_ORIGINS", "").split(",") if x.strip()),
            capture_timeout_seconds=int(os.getenv("RUNTIME_CAPTURE_TIMEOUT_SECONDS", "30")),
            deadline_seconds=int(os.getenv("RUNTIME_DEADLINE_SECONDS", "600")),
            max_research_rounds=int(os.getenv("RUNTIME_RESEARCH_ROUNDS", "3")),
            max_output_tokens=int(os.getenv("RUNTIME_MAX_OUTPUT_TOKENS", "4096")),
            max_tool_calls=int(os.getenv("RUNTIME_MAX_TOOL_CALLS", "11")),
            worker_lease_seconds=int(os.getenv("RUNTIME_WORKER_LEASE_SECONDS", "60")),
            template_version=os.getenv("RUNTIME_TEMPLATE_VERSION", "unconfigured"),
            renderer_version=os.getenv("RUNTIME_RENDERER_VERSION", "unconfigured"),
            langfuse_url=os.getenv("LANGFUSE_BASE_URL", ""), langfuse_public_key=os.getenv("LANGFUSE_PUBLIC_KEY", ""),
            langfuse_secret_key=os.getenv("LANGFUSE_SECRET_KEY", ""),
            pdf_logo_path=os.getenv("RUNTIME_PDF_LOGO_PATH", ""),
            embedding_configuration=os.getenv("EMBEDDING_CONFIGURATION", ""),
            embedding_model_path=os.getenv("EMBEDDING_MODEL_PATH", ""),
            embedding_backend=os.getenv("EMBEDDING_BACKEND", "local"),
            embedding_endpoint_url=os.getenv("EMBEDDING_ENDPOINT_URL", ""),
            embedding_model_revision=os.getenv("EMBEDDING_MODEL_REVISION", ""),
            embedding_tokenizer_path=os.getenv("EMBEDDING_TOKENIZER_PATH", ""),
            hf_token=os.getenv("HF_TOKEN", ""),
            reranker_configuration=os.getenv("RERANKER_CONFIGURATION", ""),
            reranker_model_path=os.getenv("RERANKER_MODEL_PATH", ""),
            model_device=os.getenv("MODEL_DEVICE", "cpu"), web_user_agent=os.getenv("WEB_USER_AGENT", ""),
            web_allowed_hosts=tuple(x.strip() for x in os.getenv("WEB_ALLOWED_HOSTS", "").split(",") if x.strip()),
            brave_api_key=os.getenv("BRAVE_API_KEY", ""),
            web_discovery_provider=os.getenv("WEB_DISCOVERY_PROVIDER", "searxng"),
            web_search_url=os.getenv("WEB_SEARCH_URL", ""),
            web_search_engines=tuple(n.strip() for n in os.getenv("WEB_SEARCH_ENGINES", "duckduckgo,yahoo").split(",") if n.strip()),
            web_browser_executable=os.getenv("WEB_BROWSER_EXECUTABLE", ""),
            web_browser_timeout_seconds=int(os.getenv("WEB_BROWSER_TIMEOUT_SECONDS", "25")),
            web_crawl4ai_python=os.getenv("WEB_CRAWL4AI_PYTHON", ""),
            rich_outputs_enabled=os.getenv("RUNTIME_RICH_OUTPUTS_ENABLED", "false").lower() == "true",
            pptx_template_path=os.getenv("RUNTIME_PPTX_TEMPLATE_PATH", ""),
            case_memory_enabled=os.getenv('CASE_MEMORY_ENABLED', '').lower() in {'1', 'true', 'yes'},
            case_memory_min_score=float(os.getenv('CASE_MEMORY_MIN_SCORE', '50')))
