from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import math
import re
from threading import Lock
from time import perf_counter

from backend.contracts.data import ModelConfiguration, validate_vector
from backend.contracts.services import ServiceUnavailable


class LocalEmbedder:
    def __init__(self, configuration: ModelConfiguration, encoder, tokenizer):
        configuration.require_resolved()
        if configuration.role != "embedding" or configuration.normalization != "l2":
            raise ValueError("verified L2 embedding configuration required")
        self.configuration = configuration
        self.config_hash = configuration.config_hash
        self.encoder = encoder
        self.tokenizer = tokenizer
        self.lock = Lock()

    def token_count(self, input_text):
        return len(self.tokenizer.encode(input_text, add_special_tokens=True, truncation=False))

    def document_input(self, text, title="none", headings=""):
        return self.configuration.document_template.format(text=text, title=title or "none", headings=headings)

    def accepts_document(self, text, title="none", headings=""):
        return self.token_count(self.document_input(text, title, headings)) <= self.configuration.input_limit

    def encode_inputs(self, texts):
        if not texts:
            return []
        if any(self.token_count(text) > self.configuration.input_limit for text in texts):
            raise ValueError("embedding tokenizer input limit exceeded; truncation is forbidden")
        with self.lock:
            rows = self.encoder.encode(texts, prompt="", normalize_embeddings=True, show_progress_bar=False,
                convert_to_numpy=True, truncate_dim=self.configuration.dimension)
        if len(rows) != len(texts):
            raise ValueError("embedding batch length mismatch")
        vectors = []
        for row in rows:
            vector = validate_vector([float(value) for value in row], self.configuration.dimension)
            norm = math.sqrt(sum(value * value for value in vector))
            vectors.append([value / norm for value in vector])
        return vectors

    def embed_queries(self, texts):
        return self.encode_inputs([self.configuration.query_template.format(text=text, query=text) for text in texts])

    def embed_query(self, text):
        return self.embed_queries([text])[0]

    def embed_documents(self, texts):
        return self.encode_inputs(texts)

    def benchmark(self, formatted_inputs):
        started = perf_counter()
        vectors = self.encode_inputs(formatted_inputs)
        elapsed = perf_counter() - started
        return {"config_hash": self.config_hash, "count": len(vectors), "seconds": elapsed,
            "documents_per_second": len(vectors) / elapsed if elapsed else None,
            "maximum_tokens": max(map(self.token_count, formatted_inputs), default=0)}


def load_embeddinggemma(configuration: ModelConfiguration, local_path, *, device="cpu"):
    configuration.require_resolved()
    try:
        runtime = f"sentence-transformers/{version('sentence-transformers')};transformers/{version('transformers')};torch/{version('torch')}"
    except PackageNotFoundError as error:
        raise ServiceUnavailable() from error
    if (configuration.artifact != "google/embeddinggemma-2" or not re.fullmatch(r"[a-f0-9]{40}", configuration.revision)
            or configuration.precision != "float32" or configuration.adapter_version != runtime
            or configuration.tokenizer != f"{configuration.artifact}@{configuration.revision}"
            or not Path(local_path).is_dir()):
        raise ValueError("local verified EmbeddingGemma artifact, exact revision/runtime and float32 required")
    try:
        import torch
        from sentence_transformers import SentenceTransformer
        encoder = SentenceTransformer(str(local_path), revision=configuration.revision, local_files_only=True,
            trust_remote_code=False, device=device, config_kwargs={"vision_config": None, "audio_config": None},
            model_kwargs={"torch_dtype": torch.float32})
    except (ImportError, OSError) as error:
        raise ServiceUnavailable() from error
    if encoder.get_sentence_embedding_dimension() != configuration.dimension:
        raise ValueError("local encoder dimension differs from registered configuration")
    if configuration.input_limit > encoder.max_seq_length:
        raise ValueError("registered token budget exceeds local encoder limit")
    return LocalEmbedder(configuration, encoder, encoder.tokenizer)
