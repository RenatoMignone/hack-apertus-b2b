# Embeddings: shared ingestion and query protocol

The connected encoder configuration is **`google/embeddinggemma-2`**, revision
`914f7f89142e33e77833254d9c9b90c3cef7303b`, 768-dimensional float vectors,
L2 normalization and an 8192-token input limit including special tokens.
`models/embeddings/configured.py` selects the same adapter for builds and runtime.
An embedding model is required to encode both documents and user queries for
pgvector search; Apertus reasoning does not supply these vectors.

## Configure

Install `src/backend/requirements.hosted.lock` in the backend environment.
Provision only the pinned `tokenizer.json` locally for hosted inference; expected
SHA-256 is `4d777ef5bdc1aa36227abdfb77c3e49e7b9c892d16e1b6bda41c393504828be4`.
Copy the [configuration example](../../src/backend/config/profiles/embeddinggemma-hf.example.json)
into ignored storage and verify the actual endpoint before marking it verified.

```dotenv
EMBEDDING_BACKEND=hf
EMBEDDING_ENDPOINT_URL=https://YOUR_AUTHORIZED_ENDPOINT
HF_TOKEN=<private endpoint token>
EMBEDDING_MODEL_REVISION=914f7f89142e33e77833254d9c9b90c3cef7303b
EMBEDDING_CONFIGURATION=.local/embeddinggemma-hf.json
EMBEDDING_TOKENIZER_PATH=.local/embeddinggemma-2/tokenizer.json
```

The HF adapter calls `POST /v1/embeddings` with exact formatted strings:

```text
query:    task: search result | query: {text}
document: title: {title} | text: {text}
```

No server `prompt_name` is supplied. The tokenizer counts the exact inputs with
truncation/padding disabled; response usage must match the local total. Vectors
must be finite, nonzero, correct-dimensional and cover the batch exactly.
Unexpected prefixes, tokenization drift or invalid responses fail explicitly.
Startup never downloads tokenizer or model weights.

## Compatibility and hosting

Complete configuration determines its hash; the verified development configuration
was `b9846ffee5c2cc11a371a47be00d1cab898d6ca5b88ba6f08ae4e7e9339e131c`.
Changing any relevant field creates a different configuration. Ingestion/query
encoding must match indexed rows; do not relabel synthetic or incompatible vectors.
Changed encoding requires a new build and re-embedding.

HF hosting avoids local model weights but adds network latency, endpoint
availability and usage cost. Local hosting needs provisioned assets/runtime and
hardware. Offline requires the local option; connected development explicitly
uses HF. Each encoder/reranker has its own compatible tokenizer. A `verified`
flag records operator validation, not remote cryptographic weight attestation.

Protocol checks returned finite 768d vectors, query/document token-usage parity
and identical-input parity using synthetic text; this is compatibility evidence,
not a quality benchmark or guarantee the endpoint is currently available.
See [verification](../judges/VERIFICATION.md). Protocol references:
[hf-serve schema](https://github.com/huggingface/hf-serve/blob/b805e0ccb5659d44f3ae384858900273d7965076/src/hf_serve/openai/schemas/embeddings.py),
[pinned model prompts](https://huggingface.co/google/embeddinggemma-2/blob/914f7f89142e33e77833254d9c9b90c3cef7303b/config_sentence_transformers.json).
