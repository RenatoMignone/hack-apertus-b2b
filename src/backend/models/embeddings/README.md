# Embeddings adapter

Read [deployment recommendation](../../../../docs/data/EMBEDDING_DEPLOYMENT.md),
[retrieval](../../../../docs/data/RETRIEVAL_SPEC.md) and
[model/build configuration](../../../../docs/data/BUILD_AND_OPERATIONS.md).
Connected deployment uses the supplied HF endpoint; [HF setup and live evidence](../../../../docs/data/HOSTED_EMBEDDINGS.md)
owns model/image/tokenizer/config pins. `configured.py` selects local or hosted
for ingestion, benchmarks and runtime queries. `hosted.py` uses the HF
`/v1/embeddings` protocol, exact local token counts and explicit formatted inputs.
It rejects invalid shapes/indexes, usage drift/truncation, redirects and offline
mode; no retries or silent fallback. Install `requirements.hosted.lock`; no model
weights/torch are needed for hosted clients. The checked-in configuration example
is deliberately unverified until deployment review.

`local.py` implements the local-files-only SentenceTransformers adapter; the
[lane handoff](../../../../docs/team/backbone/HANDOFF.md) lists deployment gates.
`load_embeddinggemma(configuration, local_path)` requires a verified configuration,
exact model commit, tokenizer identity `artifact@revision`, float32, and runtime
identity `sentence-transformers/VERSION;transformers/VERSION;torch/VERSION` matching
installed packages. Vision/audio encoders are disabled; there is no download or
hosted fallback. `embed_documents` accepts already formatted actual input text,
not raw chunks to prefix twice. Token limits are counted with the own tokenizer;
`benchmark` measures actual timings only after real artifacts are provisioned.

The adapter implements the existing `Embedder` port in `contracts/data.py`:
`config_hash` and `embed_query(text)`, plus document/batch encoding for index builds.
Local mode loads weights in-process; hosted mode loads only the pinned tokenizer
and uses the explicit external endpoint. Do not invent a second query interface. Pin exact model/tokenizer/runtime and
query/document prefixes. Validate shape, finite nonzero vectors, normalization,
input-token budget and corpus/query configuration parity. No silent truncation
or hosted fallback. Keep model initialization/caching out of every query call.
