import math
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import re
from threading import Lock
import json
import hashlib

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

    def windows(self, query, passage):
        count = lambda value: len(self.tokenizer.encode(query, value, add_special_tokens=True, truncation=False))
        if count(passage) <= self.input_limit:
            return [{"char_start": 0, "char_end": len(passage), "pair_tokens": count(passage)}]
        if not callable(self.tokenizer):
            raise ValueError("reranker pair-token budget exceeded; truncation is forbidden")
        if count("") >= self.input_limit:
            raise ServiceUnavailable()  # Never truncate the original request.
        offsets = self.tokenizer(passage, add_special_tokens=False, return_offsets_mapping=True)["offset_mapping"]
        output, cursor = [], 0
        while cursor < len(offsets):
            if len(output) >= 16:
                raise ServiceUnavailable()  # Bounded inference; caller retains RRF + visible limitation.
            # Exact token counts include special tokens and the paired query.
            lo, hi = cursor+1, min(len(offsets), cursor+self.input_limit)
            best = None
            start = 0 if cursor == 0 else offsets[cursor][0]
            while lo <= hi:
                end_token = (lo+hi)//2
                end = offsets[end_token][0] if end_token < len(offsets) else len(passage)
                tokens = count(passage[start:end])
                if tokens <= self.input_limit:
                    best = (end_token, end, tokens)
                    lo = end_token+1
                else:
                    hi = end_token-1
            if best is None:
                raise ServiceUnavailable()
            end_token, end, tokens = best
            output.append({"char_start": start, "char_end": end, "pair_tokens": tokens})
            cursor = end_token
        return output

    def score_with_details(self, query, passages):
        windows = [self.windows(query, passage) for passage in passages]
        pairs = [[query, passage[w["char_start"]:w["char_end"]]]
                 for passage, group in zip(passages, windows) for w in group]
        if not pairs:
            return []
        with self.lock:
            values = self.model.predict(pairs, show_progress_bar=False, batch_size=8)
        scores = [float(value) for value in values]
        if len(scores) != len(pairs) or not all(math.isfinite(value) for value in scores):
            raise ValueError("reranker returned invalid scores")
        result, cursor = [], 0
        for group in windows:
            values = scores[cursor:cursor+len(group)]
            result.append({"score": max(values), "windows": [dict(w, score=v) for w, v in zip(group, values)]})
            cursor += len(group)
        return result

    def score(self, query, passages):
        return [result["score"] for result in self.score_with_details(query, passages)]


def runtime_identity():
    return f"sentence-transformers/{version('sentence-transformers')};transformers/{version('transformers')};torch/{version('torch')}"


def verify_assets(local_path, configuration):
    """The build-time helper pins bytes; startup never downloads or trusts a directory name."""
    root = Path(local_path)
    manifest = json.loads((root / "navigator-model-manifest.json").read_text())
    if (manifest["artifact"] != configuration.artifact or manifest["revision"] != configuration.revision
            or manifest["config_hash"] != configuration.config_hash):
        raise ValueError("reranker manifest does not match configuration")
    if not {"config.json", "model.safetensors", "tokenizer.json"} <= manifest["files"].keys():
        raise ValueError("reranker manifest is incomplete")
    for name, digest in manifest["files"].items():
        if Path(name).name != name or not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise ValueError("invalid reranker manifest entry")
        file = root / name
        if file.is_symlink():
            raise ValueError("reranker assets must be local regular files")
        with file.open("rb") as source:
            actual = hashlib.file_digest(source, "sha256").hexdigest()
        if actual != digest:
            raise ValueError("reranker asset integrity check failed")


def load_reranker(configuration, local_path, *, device="cpu"):
    configuration.require_resolved()
    try:
        runtime = runtime_identity()
    except PackageNotFoundError as error:
        raise ServiceUnavailable() from error
    if (configuration.role != "reranking" or not Path(local_path).is_dir()
            or not re.fullmatch(r"[a-f0-9]{40}", configuration.revision) or configuration.adapter_version != runtime
            or configuration.tokenizer != f"{configuration.artifact}@{configuration.revision}"
            or configuration.precision != "float32" or configuration.normalization != "none"
            or configuration.query_template != "{text}" or configuration.document_template != "{text}"):
        raise ValueError("verified local reranker required")
    verify_assets(local_path, configuration)
    try:
        import torch
        from sentence_transformers import CrossEncoder
        model = CrossEncoder(str(local_path), local_files_only=True, trust_remote_code=False, device=device,
            revision=configuration.revision, max_length=configuration.input_limit,
            model_kwargs={"dtype": torch.float32})
    except (ImportError, OSError) as error:
        raise ServiceUnavailable() from error
    if configuration.input_limit > model.tokenizer.model_max_length:
        raise ValueError("reranker token budget exceeds the tokenizer limit")
    return LocalReranker(model, model.tokenizer, input_limit=configuration.input_limit, config_hash=configuration.config_hash)
