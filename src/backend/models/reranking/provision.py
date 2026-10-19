"""Explicit build-time provisioning. No downloads in API/worker startup."""
import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter

from backend.contracts.data import ModelConfiguration
from backend.models.reranking.local import load_reranker, runtime_identity

ARTIFACT = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
REVISION = "1427fd652930e4ba29e8149678df786c240d8825"
FILES = ["config.json", "model.safetensors", "tokenizer.json", "tokenizer_config.json",
         "special_tokens_map.json", "sentencepiece.bpe.model", "README.md"]


def provision(path, configuration_path, *, download=False):
    root = Path(path)
    if download:
        from huggingface_hub import snapshot_download
        snapshot_download(ARTIFACT, revision=REVISION, local_dir=str(root),
                          allow_patterns=FILES, token=False)
    import yaml
    card = (root / "README.md").read_text()
    metadata = yaml.safe_load(card.split("---", 2)[1])
    if metadata.get("license") != "apache-2.0":
        raise ValueError("review the publisher license before provisioning")
    configuration = ModelConfiguration(role="reranking", logical_name="multilingual-minilm-reranker",
        artifact=ARTIFACT, revision=REVISION, adapter_version=runtime_identity(),
        tokenizer=f"{ARTIFACT}@{REVISION}", input_limit=512, normalization="none",
        query_template="{text}", document_template="{text}", precision="float32",
        license="apache-2.0", verified=True)
    hashes = {}
    for name in FILES:
        if (root / name).is_file():
            with (root / name).open("rb") as source:
                hashes[name] = hashlib.file_digest(source, "sha256").hexdigest()
    manifest = {"artifact": ARTIFACT, "revision": REVISION, "config_hash": configuration.config_hash, "files": hashes}
    (root / "navigator-model-manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    started = perf_counter()
    reranker = load_reranker(configuration, root)
    query = "Research expertise in glucose sensors and signal processing for diabetes devices"
    scores = reranker.score(query, [
        "Synthetic laboratory develops glucose sensors and signal processing for diabetes research.",
        "Synthetic institute studies medieval poetry and manuscripts."])
    if scores[0] <= scores[1]:
        raise ValueError("reranker failed the synthetic relevance sanity check")
    target = Path(configuration_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(configuration.model_dump_json(indent=2)+"\n")
    return {"artifact": ARTIFACT, "revision": REVISION, "config_hash": configuration.config_hash,
            "runtime": configuration.adapter_version, "sanity_scores": scores,
            "load_and_score_seconds": round(perf_counter()-started, 3),
            "quality_note": "Synthetic compatibility check, not real-corpus relevance evaluation."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--configuration", type=Path, required=True)
    parser.add_argument("--download", action="store_true", help="Explicitly fetch the pinned public model (~490 MB)")
    args = parser.parse_args()
    print(json.dumps(provision(args.model_path, args.configuration, download=args.download), indent=2))


if __name__ == "__main__":
    main()
