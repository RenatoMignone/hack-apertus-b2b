# Connected HF embeddings and first ingestion handoff

18 October 2026 · User-supplied deployment; adapter verified with synthetic text.
No shared DB writes, ingestion or snapshot publication were performed here.

| Item | Value |
| --- | --- |
| Endpoint | `https://6ad51265d2d0ab8296e5a3cd.endpoints.huggingface.cloud` |
| Container | `ghcr.io/huggingface/hf-serve:b805e0c-cpu` (operator-supplied tag; not an image digest) |
| Internal port / client URL | Container 8080; external client uses HTTPS 443 |
| Model / revision | `google/embeddinggemma-2` / `914f7f89142e33e77833254d9c9b90c3cef7303b` |
| Protocol | `POST /v1/embeddings`, float vectors; exact formatted strings, no server prompt name |
| Encoding | 768d, L2, text-only, maximum 8192 tokens including special tokens |
| Tokenizer JSON SHA-256 | `4d777ef5bdc1aa36227abdfb77c3e49e7b9c892d16e1b6bda41c393504828be4` |

`models/embeddings/configured.py` selects the encoder for **both** ingestion/build/
benchmark and runtime queries. `EMBEDDING_BACKEND=hf` explicitly selects the
hosted adapter; `local` retains local assets. Hosted use is rejected offline,
with no fallback, redirects or implicit retries. HF token stays backend-only.

## Configuration

1. Install `src/backend/requirements.hosted.lock` and the editable backend.
   The supplemental lock adds the lightweight tokenizer runtime; no torch or
   model weights are required on clients. It was tested on macOS/Python 3.13;
   target-host wheel/image packaging still needs validation.
2. Download **only** `tokenizer.json` from the immutable model revision through
   your approved provisioning process. The adapter verifies its hash, disables
   tokenizer truncation/padding and counts exact formatted inputs before sending.
   Runtime never downloads this file automatically.
3. Copy [the non-secret configuration example](../../src/backend/config/profiles/embeddinggemma-hf.example.json)
   to an ignored local JSON. Review the declared serving configuration and verify
   the endpoint before marking it `verified=true`. Use this **same complete JSON**
   for the ingestion builder and runtime. A JSON `verified` flag is a recorded
   operator assertion, not remote cryptographic attestation of model weights.
4. Set these fields in the private backend environment:

   ```text
   DEPLOYMENT_MODE=connected
   EMBEDDING_BACKEND=hf
   EMBEDDING_ENDPOINT_URL=https://6ad51265d2d0ab8296e5a3cd.endpoints.huggingface.cloud
   HF_TOKEN=<private authorized endpoint token>
   EMBEDDING_MODEL_REVISION=914f7f89142e33e77833254d9c9b90c3cef7303b
   EMBEDDING_CONFIGURATION=.local/embeddinggemma-hf.json
   EMBEDDING_TOKENIZER_PATH=.local/embeddinggemma-2/914f7f89142e33e77833254d9c9b90c3cef7303b/tokenizer.json
   ```

Hosted input formatting is explicit: `task: search result | query: {text}` and
`title: {title} | text: {text}`. The pinned model metadata has no default server
prompt; the client sends no `prompt_name`, avoiding double prefixes. Document
embeddings receive already formatted inputs. Every response must match the local
sum of input tokens: unexpected prefixes/truncation/tokenizer drift are rejected.
Indexed rows must cover the batch exactly; invalid/zero/non-finite/wrong-size
vectors fail. Response model echoes are checked but do not attest server weights.

Existing local or synthetic config hashes are incompatible. Build/publish a new
reviewed snapshot explicitly; do not relabel existing vectors. HF and Keera are
connected runtime dependencies, so this configuration does not prove an air-gap
or Swiss-residency claim. Only permitted text may leave the backend; source and
operator content must not include confidential plans/one-pagers.

## Eric: one-source test, then publication

After pulling this change, use `--env-file` with the HF fields above. `benchmark`
and `build` no longer require `--model-path` when backend is `hf`; local mode
still requires assets. Start with one source **without `--publish`**. Verify stored
`retrieval.embeddings.input_text`/config hash, exact evidence and query encoding.
Full pilot publication still requires reviewed claims and all required source
families (UniBE/ARTORG/DCB). A one-source collection/build is not that publication.

The tested local JSON (example plus `verified=true`) has config hash:
`b9846ffee5c2cc11a371a47be00d1cab898d6ca5b88ba6f08ae4e7e9339e131c`.
Keep `logical_name`, templates, limits and all fields identical if reusing this
hash. Any intended change creates a different configuration/build.

## Verification and provenance

A first token lacked endpoint permission (403); the replacement token returned
200. Final adapter requests used synthetic query/document text: finite 768d unit
vectors, exact tokenizer/remote usage equality, and identical-input vector parity
passed. Pinned tokenizer bytes and model license (`apache-2.0`) were checked at
the supplied model commit. Tokens/configured secrets are only in ignored `.env`;
model weights were not downloaded. Focused non-database regression: **117 passed, 58 integration tests deselected**;
no DB suite was run by this change. Schema-reference, lock-consistency and compile
checks passed. This is protocol/encoding evidence, not a
retrieval-quality benchmark or proof of a populated corpus/full case.

Protocol inspected from the actual [hf-serve schema](https://github.com/huggingface/hf-serve/blob/b805e0ccb5659d44f3ae384858900273d7965076/src/hf_serve/openai/schemas/embeddings.py)
and [implementation](https://github.com/huggingface/hf-serve/blob/b805e0ccb5659d44f3ae384858900273d7965076/src/hf_serve/openai/tasks/embeddings.py).
Model metadata: [pinned prompt configuration](https://huggingface.co/google/embeddinggemma-2/blob/914f7f89142e33e77833254d9c9b90c3cef7303b/config_sentence_transformers.json).
