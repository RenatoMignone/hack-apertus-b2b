# Local reranking

19 October 2026. Implemented on `codex/backend-research-completion`.

The first provisioned CPU option is
[cross-encoder/mmarco-mMiniLMv2-L12-H384-v1](https://huggingface.co/cross-encoder/mmarco-mMiniLMv2-L12-H384-v1),
revision `1427fd652930e4ba29e8149678df786c240d8825`, Apache-2.0.
Its publisher describes multilingual retrieval training. This is a compact
alternative to the earlier BGE candidate, selected for this development machine's
available disk/memory budget. It is not a measured quality winner; BGE remains an
option for a separately provisioned comparison. Changing the reranker does not
change the embedding space or require re-encoding the corpus.

## Provision explicitly

From repository root, using the project's virtual environment:

```bash
python -m pip install -r src/backend/requirements.reranker.lock
python -m backend.models.reranking.provision \
  --model-path .local/reranker-minilm \
  --configuration .local/reranker-minilm.json --download
```

The lock was tested on macOS arm64 / Python 3.13. Verify wheels on Linux/Windows;
GPU deployments need their own resolved runtime. The model download is about
490 MB. Omitting `--download` uses existing local files. The helper pins the
revision, checks the publisher license, hashes required model/tokenizer files and
runs a synthetic relevance sanity check before writing the configuration.

Set privately, then restart API and worker:

```dotenv
RERANKER_CONFIGURATION=.local/reranker-minilm.json
RERANKER_MODEL_PATH=.local/reranker-minilm
MODEL_DEVICE=cpu
```

Startup never downloads weights. API construction is lazy; the worker loads the
model on its first reranking request. The readiness checker verifies the configured
runtime and asset manifest without model/network calls. Transfer both the model
folder (including its manifest) and matching JSON for offline packaging.

## Scoring and provenance

Independent lexical/vector retrieval and RRF still select authorized candidates.
The reranker scores the full original request against original passage plus
separate title/heading context. Its own tokenizer counts the pair, including
special tokens. Inputs use float32, a 512-token pair limit and batches of eight.

Long passages use consecutive exact character windows that cover the full passage;
the original request is never truncated. At most sixteen windows per passage are
allowed. The passage score is the maximum window score; every window's character
bounds, pair-token count and score are recorded in `EvidenceHit.reranker_windows`.
Bounds refer to the composed `Title / Headings / Passage` input, not document-body
offsets. Source evidence text and its original offsets remain unchanged.

If the original query cannot fit or complete window coverage exceeds the budget,
reranking is unavailable and the caller retains RRF with `reranker_unavailable`.
Invalid/non-finite score output is an error. Scores are relevance values, never
truth judgments or probabilities. Stable chunk IDs break ties.

`query_matches` records which actual lexical/vector queries retrieved each hit.
The workflow resolves recorded paths to the exact canonical claim evidence before
putting search lineage into the frozen pack. It does not invent ontology mappings.

## Measured limits

On Elia's Mac, the pinned runtime loaded and passed a two-passage synthetic sanity
check in about eight seconds. One real authorized live-corpus probe with the
fictional Helvetic request returned 30 hits / 50 evidence passages and reranked all
30 hits in 29.37 seconds including HF queries and database/context expansion.
Later context-expansion probes changed passage counts and timing; these are
engineering checks, not a controlled relevance/latency benchmark.

The probe created and cancelled only its own case/run; it did not alter ingestion,
grants, migrations or source artifacts. Human-reviewed expected entities and
fused-versus-reranked Recall@10/latency comparisons remain open. Keep the
[quality evaluation protocol](../challenge/EVALUATION.md).
