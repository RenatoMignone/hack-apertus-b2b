"""Explicit connected hf-serve embeddings, with exact local token accounting."""
import json
import math
import re
from pathlib import Path
from urllib.parse import urlsplit

import httpx

from backend.contracts.data import content_hash, validate_vector
from backend.contracts.services import ServiceUnavailable
from backend.models.embeddings.local import LocalEmbedder


ADAPTER_VERSION = "hf-serve/b805e0ccb5659d44f3ae384858900273d7965076;raw-openai-v1"
TOKENIZER_SHA256 = "4d777ef5bdc1aa36227abdfb77c3e49e7b9c892d16e1b6bda41c393504828be4"


def endpoint_url(value):
    parsed = urlsplit(value)
    if (parsed.scheme != "https" or not parsed.hostname
            or not parsed.hostname.endswith(".endpoints.huggingface.cloud")
            or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.port not in (None, 443) or parsed.path not in ("", "/", "/v1/embeddings")):
        raise ValueError("hosted embeddings require an explicit HTTPS Hugging Face endpoint")
    return value.rstrip("/") if parsed.path == "/v1/embeddings" else value.rstrip("/") + "/v1/embeddings"


class HFEmbedder(LocalEmbedder):
    """Same formatted inputs for build/query; no server prompts or local fallback.

    The pinned model has default_prompt_name=None. Exact usage-token equality
    additionally detects unexpected prefixes, tokenizer drift and truncation.
    It does not attest the server's model weights/revision.
    """
    def __init__(self, configuration, endpoint, token, tokenizer, *, mode="connected", transport=None):
        if mode != "connected":
            raise ValueError("hosted embeddings are forbidden offline")
        super().__init__(configuration, None, tokenizer)
        if configuration.test_only or configuration.adapter_version != ADAPTER_VERSION:
            raise ValueError("a verified hosted configuration is required; rebuild incompatible indexes")
        if not token or token.isspace():
            raise ServiceUnavailable()
        self.endpoint = endpoint_url(endpoint)
        self._token, self.transport = token, transport

    def encode_inputs(self, texts):
        if not texts:
            return []
        counts = [self.token_count(value) for value in texts]
        if any(count > self.configuration.input_limit for count in counts):
            raise ValueError("embedding tokenizer input limit exceeded; truncation is forbidden")
        vectors = []
        # Bound each request/response and don't implicitly retry paid inference.
        for start in range(0, len(texts), 16):
            batch = texts[start:start + 16]
            payload = {"model": self.configuration.artifact, "input": batch,
                       "dimensions": self.configuration.dimension, "encoding_format": "float"}
            if len(json.dumps(payload).encode()) > 1_000_000:
                raise ValueError("embedding request byte limit exceeded")
            try:
                with httpx.Client(transport=self.transport, follow_redirects=False, trust_env=False,
                                  timeout=httpx.Timeout(60, connect=5)) as client:
                    with client.stream("POST", self.endpoint, json=payload,
                                       headers={"Authorization": "Bearer " + self._token}) as response:
                        if response.status_code != 200:
                            raise ServiceUnavailable()
                        body = bytearray()
                        for chunk in response.iter_bytes():
                            body.extend(chunk)
                            if len(body) > 4_000_000:
                                raise ValueError("embedding response byte limit exceeded")
                result = json.loads(body)
            except (httpx.HTTPError, UnicodeError, json.JSONDecodeError):
                raise ServiceUnavailable() from None
            try:
                rows = result["data"]
                usage = result["usage"]["prompt_tokens"]
                if (result["model"] != self.configuration.artifact or type(usage) is not int
                        or usage != sum(counts[start:start + len(batch)])):
                    raise ValueError("embedding tokenizer usage differs; possible truncation or prompt drift")
                if len(rows) != len(batch) or any(type(row["index"]) is not int for row in rows):
                    raise ValueError("embedding batch length/index mismatch")
                indexed = {row["index"]: row["embedding"] for row in rows}
                if set(indexed) != set(range(len(batch))) or len(indexed) != len(rows):
                    raise ValueError("embedding indexes must cover the batch exactly")
                for index in range(len(batch)):
                    vector = indexed[index]
                    if not isinstance(vector, list) or any(type(v) not in (int, float) for v in vector):
                        raise ValueError("embedding vector must contain numbers")
                    validate_vector(vector, self.configuration.dimension)
                    norm = math.hypot(*vector)
                    if not math.isfinite(norm) or norm == 0:
                        raise ValueError("invalid embedding norm")
                    vectors.append([value / norm for value in vector])
            except (KeyError, TypeError, AttributeError):
                raise ValueError("invalid embedding response structure") from None
        return vectors


def load_hf(configuration, endpoint, token, tokenizer_path, *, revision, mode="connected", transport=None):
    # Reject before filesystem/network work in offline mode.
    if mode != "connected":
        raise ValueError("hosted embeddings are forbidden offline")
    configuration.require_resolved()
    if (configuration.artifact != "google/embeddinggemma-2"
            or not re.fullmatch(r"[a-f0-9]{40}", revision) or configuration.revision != revision
            or revision != "914f7f89142e33e77833254d9c9b90c3cef7303b"
            or configuration.tokenizer != f"{configuration.artifact}@{revision}"
            or configuration.dimension != 768 or configuration.input_limit > 8192
            or configuration.precision != "float32"):
        raise ValueError("hosted model/configuration differs from the approved text-only deployment")
    if not tokenizer_path:
        raise ServiceUnavailable()
    path = Path(tokenizer_path)
    if not path.is_file():
        raise ServiceUnavailable()
    raw = path.read_bytes()
    if content_hash(raw) != TOKENIZER_SHA256:
        raise ValueError("tokenizer bytes differ from the pinned model revision")
    try:
        from tokenizers import Tokenizer
    except ImportError:
        raise ServiceUnavailable() from None
    tokenizer = Tokenizer.from_str(raw.decode("utf-8"))
    tokenizer.no_truncation()
    tokenizer.no_padding()

    class Counter:
        def encode(self, text, **kwargs):
            return tokenizer.encode(text, add_special_tokens=True).ids

    return HFEmbedder(configuration, endpoint, token, Counter(), mode=mode, transport=transport)
