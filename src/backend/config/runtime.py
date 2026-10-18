"""Runtime-only settings. Secret values never enter run configuration or reprs."""
import json
import os
from dataclasses import dataclass, field
from urllib.parse import urlsplit
from uuid import UUID

from backend.contracts.data import AccessContext


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
    reasoning_factory: str = ""
    backbone_factory: str = ""
    web_factory: str = ""
    pdf_factory: str = ""
    llm_name: str = "apertus-v1-5-8b"
    llm_base_url: str = "https://gateway.keera.ch/api/v1"
    llm_api_key: str = field(default="", repr=False)
    langgraph_database_url: str = field(default="", repr=False)
    cors_origins: tuple[str, ...] = ()
    deadline_seconds: int = 600
    max_research_rounds: int = 3
    max_output_tokens: int = 4096
    max_tool_calls: int = 6
    max_request_bytes: int = 128_000
    worker_lease_seconds: int = 60
    template_version: str = "unconfigured"
    renderer_version: str = "unconfigured"
    langfuse_url: str = ""
    langfuse_public_key: str = field(default="", repr=False)
    langfuse_secret_key: str = field(default="", repr=False)

    def __post_init__(self):
        if self.mode not in {"connected", "offline"} or not 1 <= self.max_research_rounds <= 3:
            raise ValueError("invalid deployment mode or research budget")
        if not 1 <= self.deadline_seconds <= 3600 or not 0 <= self.max_tool_calls <= 30:
            raise ValueError("invalid runtime deadline or tool budget")
        if not 1 <= self.max_output_tokens <= 65536 or not 4096 <= self.max_request_bytes <= 1_000_000:
            raise ValueError("invalid token or input budget")
        if not 15 <= self.worker_lease_seconds <= 3600:
            raise ValueError("worker lease must be 15–3600 seconds")
        if self.mode == "offline" and urlsplit(self.llm_base_url).hostname not in {
            "localhost", "127.0.0.1", "::1", "apertus", "llm"
        }:
            raise ValueError("offline inference requires an explicit local model endpoint")
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
            reasoning_factory=os.getenv("RUNTIME_REASONING_FACTORY", ""),
            backbone_factory=os.getenv("RUNTIME_BACKBONE_FACTORY", ""), web_factory=os.getenv("RUNTIME_WEB_FACTORY", ""),
            pdf_factory=os.getenv("RUNTIME_PDF_FACTORY", ""), llm_name=os.getenv("LLM_NAME", "apertus-v1-5-8b"),
            llm_base_url=os.getenv("LLM_BASE_URL", "https://gateway.keera.ch/api/v1"),
            llm_api_key=os.getenv("LLM_API_KEY", ""), langgraph_database_url=os.getenv("LANGGRAPH_DATABASE_URL", ""),
            cors_origins=tuple(x.strip() for x in os.getenv("RUNTIME_CORS_ORIGINS", "").split(",") if x.strip()),
            deadline_seconds=int(os.getenv("RUNTIME_DEADLINE_SECONDS", "600")),
            max_research_rounds=int(os.getenv("RUNTIME_RESEARCH_ROUNDS", "3")),
            max_output_tokens=int(os.getenv("RUNTIME_MAX_OUTPUT_TOKENS", "4096")),
            max_tool_calls=int(os.getenv("RUNTIME_MAX_TOOL_CALLS", "6")),
            worker_lease_seconds=int(os.getenv("RUNTIME_WORKER_LEASE_SECONDS", "60")),
            template_version=os.getenv("RUNTIME_TEMPLATE_VERSION", "unconfigured"),
            renderer_version=os.getenv("RUNTIME_RENDERER_VERSION", "unconfigured"),
            langfuse_url=os.getenv("LANGFUSE_BASE_URL", ""), langfuse_public_key=os.getenv("LANGFUSE_PUBLIC_KEY", ""),
            langfuse_secret_key=os.getenv("LANGFUSE_SECRET_KEY", ""))
