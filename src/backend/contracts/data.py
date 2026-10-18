from __future__ import annotations

import hashlib
import json
import math
from typing import Literal, Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


def content_hash(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def configuration_hash(value: dict) -> str:
    return content_hash(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode())


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class AccessContext(Contract):
    principal_id: UUID
    namespace: str = Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$")


class ArtifactRef(Contract):
    key: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    byte_count: int = Field(ge=0)
    mime: str


class ArtifactStore(Protocol):
    def put(self, data: bytes, mime: str) -> ArtifactRef: ...
    def read(self, reference: ArtifactRef) -> bytes: ...


class Span(Contract):
    char_start: int = Field(ge=0)
    char_end: int = Field(gt=0)
    text: str = Field(min_length=1)
    heading_path: list[str] = Field(default_factory=list)
    page: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def ordered(self):
        if self.char_end <= self.char_start:
            raise ValueError("span must have positive length")
        return self

    def validate_body(self, body: str) -> None:
        if body[self.char_start:self.char_end] != self.text:
            raise ValueError("evidence must equal its exact Unicode body slice")


class ModelConfiguration(Contract):
    role: Literal["embedding", "reranking", "reasoning_primary", "reasoning_fallback"]
    logical_name: str
    artifact: str
    revision: str
    adapter_version: str
    tokenizer: str
    input_limit: int = Field(gt=0)
    dimension: int | None = Field(default=None, gt=0)
    normalization: str
    query_template: str
    document_template: str
    precision: str
    license: str
    verified: bool = False
    test_only: bool = False

    def require_resolved(self) -> None:
        if not self.verified or any(not value.strip() or value.lower() in {"unknown", "pending"}
                                    for value in (self.artifact, self.revision, self.tokenizer, self.license)):
            raise ValueError("model artifact, revision, tokenizer and license must be verified")
        if self.role == "embedding" and self.dimension is None:
            raise ValueError("embedding dimension is unresolved")

    @property
    def config_hash(self) -> str:
        return configuration_hash(self.model_dump())


def validate_vector(vector: list[float], dimension: int) -> list[float]:
    if len(vector) != dimension or not all(math.isfinite(value) for value in vector):
        raise ValueError("non-finite vector or incompatible dimension")
    if not any(vector):
        raise ValueError("zero vector is invalid for cosine search")
    return vector


class Embedder(Protocol):
    config_hash: str
    def embed_query(self, text: str) -> list[float]: ...


class Reranker(Protocol):
    def score(self, query: str, passages: list[str]) -> list[float]: ...


class QueryPlan(Contract):
    original_request: str = Field(min_length=1)
    run_id: UUID | None = None
    case_id: UUID | None = None
    input_revision_id: UUID | None = None
    variants: list[str] = Field(default_factory=list, max_length=5)
    snapshot_id: UUID
    profile_id: UUID
    taxonomy_version_id: UUID
    build_id: UUID
    embedding_config_hash: str
    languages: list[Literal["en", "de", "fr", "it", "und"]] = Field(default_factory=list)
    source_family_ids: list[UUID] = Field(default_factory=list)
    excluded_document_ids: list[UUID] = Field(default_factory=list)
    round_number: int = Field(default=1, ge=1, le=3)


class EvidenceHit(Contract):
    chunk_id: UUID
    document_id: UUID
    document_version_id: UUID
    text: str
    title: str
    heading_path: list[str]
    char_start: int
    char_end: int
    language: str
    source_url: str
    evidence_ids: list[UUID]
    snapshot_id: UUID
    build_id: UUID
    lexical_rank: int | None = None
    vector_rank: int | None = None
    lexical_score: float | None = None
    cosine_distance: float | None = None
    fusion_score: float
    reranker_score: float | None = None
    ranking_version: str = "rrf60-v1"


class SearchResult(Contract):
    hits: list[EvidenceHit]
    limitations: list[str] = Field(default_factory=list)
