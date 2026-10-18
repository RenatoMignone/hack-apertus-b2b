# Embeddings adapter

Read [deployment recommendation](../../../../docs/data/EMBEDDING_DEPLOYMENT.md),
[retrieval](../../../../docs/data/RETRIEVAL_SPEC.md) and
[model/build configuration](../../../../docs/data/BUILD_AND_OPERATIONS.md).
Proposed local text-only model: `google/embeddinggemma-2`, 768d; benchmark the
shared host before deciding hosted fallback. No model is installed/served yet.

Implement the existing `Embedder` port in `contracts/data.py`: `config_hash` and
`embed_query(text)`. Add an agreed document/batch-encoding port for index builds;
do not invent a second query interface. Pin exact model/tokenizer/runtime and
query/document prefixes. Validate shape, finite nonzero vectors, normalization,
input-token budget and corpus/query configuration parity. No silent truncation
or hosted fallback. Keep model initialization/caching out of every query call.
