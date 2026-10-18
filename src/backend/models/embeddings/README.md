# Embeddings adapter

Read [deployment recommendation](../../../../docs/data/EMBEDDING_DEPLOYMENT.md),
[retrieval](../../../../docs/data/RETRIEVAL_SPEC.md) and
[model/build configuration](../../../../docs/data/BUILD_AND_OPERATIONS.md).
Proposed local text-only model: `google/embeddinggemma-2`, 768d; benchmark the
shared host before deciding hosted fallback. No model is installed/served yet.

`local.py` implements the local-files-only SentenceTransformers adapter; the
[lane handoff](../../../../docs/team/backbone/HANDOFF.md) lists deployment gates.
`load_embeddinggemma(configuration, local_path)` requires a verified configuration,
exact model commit, tokenizer identity `artifact@revision`, float32, and runtime
identity `sentence-transformers/VERSION;transformers/VERSION;torch/VERSION` matching
installed packages. Vision/audio encoders are disabled; there is no download or
hosted fallback. `embed_documents` accepts already formatted actual input text,
not raw chunks to prefix twice. Token limits are counted with the own tokenizer;
`benchmark` measures actual timings only after real artifacts are provisioned.

Implement the existing `Embedder` port in `contracts/data.py`: `config_hash` and
`embed_query(text)`. Add an agreed document/batch-encoding port for index builds;
do not invent a second query interface. Pin exact model/tokenizer/runtime and
query/document prefixes. Validate shape, finite nonzero vectors, normalization,
input-token budget and corpus/query configuration parity. No silent truncation
or hosted fallback. Keep model initialization/caching out of every query call.
