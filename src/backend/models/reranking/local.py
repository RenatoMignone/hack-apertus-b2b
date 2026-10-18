import math
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import re
from threading import Lock

from backend.contracts.services import ServiceUnavailable


class LocalReranker:
    def __init__(self, model, tokenizer, *, input_limit, config_hash):
        if input_limit < 1:
            raise ValueError("positive pair-token budget required")
        self.model = model
        self.tokenizer = tokenizer
        self.input_limit = input_limit
        self.config_hash = config_hash
        self.lock = Lock()

    def score(self, query, passages):
        pairs = [[query, passage] for passage in passages]
        if any(len(self.tokenizer.encode(query, passage, add_special_tokens=True, truncation=False)) > self.input_limit
               for passage in passages):
            raise ValueError("reranker pair-token budget exceeded; truncation is forbidden")
        if not pairs:
            return []
        with self.lock:
            values = self.model.predict(pairs, show_progress_bar=False)
        scores = [float(value) for value in values]
        if len(scores) != len(passages) or not all(math.isfinite(value) for value in scores):
            raise ValueError("reranker returned invalid scores")
        return scores


def load_reranker(configuration, local_path, *, device="cpu"):
    configuration.require_resolved()
    try:
        runtime = f"sentence-transformers/{version('sentence-transformers')};transformers/{version('transformers')};torch/{version('torch')}"
    except PackageNotFoundError as error:
        raise ServiceUnavailable() from error
    if (configuration.role != "reranking" or not Path(local_path).is_dir()
            or not re.fullmatch(r"[a-f0-9]{40}", configuration.revision) or configuration.adapter_version != runtime
            or configuration.tokenizer != f"{configuration.artifact}@{configuration.revision}"
            or configuration.precision != "float32"):
        raise ValueError("verified local reranker required")
    try:
        from sentence_transformers import CrossEncoder
        model = CrossEncoder(str(local_path), local_files_only=True, trust_remote_code=False, device=device,
            revision=configuration.revision, max_length=configuration.input_limit)
    except (ImportError, OSError) as error:
        raise ServiceUnavailable() from error
    return LocalReranker(model, model.tokenizer, input_limit=configuration.input_limit, config_hash=configuration.config_hash)
