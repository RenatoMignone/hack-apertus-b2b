# EmbeddingGemma 2: deployment choices

**18 October 2026 · Hosted connected adapter verified; local offline alternative remains.**
The verified model reference is [google/embeddinggemma-2](https://huggingface.co/google/embeddinggemma-2).
It is distinct from `google/embeddinggemma-300m`. Use the model's own tokenizer,
not Apertus token IDs. This recommendation does not establish measured retrieval
quality or hardware throughput.

## Current connected choice

The user selected Eric's existing HF endpoint and supplied the CPU image/model
revision. [Hosted setup and evidence](HOSTED_EMBEDDINGS.md) is authoritative for
this deployment: ingestion and runtime share the adapter, verified JSON and
pinned local tokenizer. Live synthetic requests passed dimensionality, exact-token
usage and same-input vector parity. No real corpus retrieval quality is claimed.

Hosted clients need no full local model weights. Local/shared-host encoding is
still supported explicitly for disconnected runtime, with independent hardware/
package verification. Switching transport/configuration does not permit mixing
incompatible existing vectors. Hosted runtime is connected-only; Swiss locality,
quotas/billing and broader quality remain to verify with the endpoint owner.

## Budget and hosting

The team's **$10 credit per user** is user-supplied; eligibility for Providers,
Endpoints or Spaces must be checked in each account. Do not treat separate users'
credits as one pooled budget or rotate keys to bypass allocation rules. Pick one
account/organization to own a shared endpoint if hosting is selected.

[HF endpoint pricing](https://huggingface.co/docs/inference-endpoints/support/pricing)
lists $0.067/hour for an AWS 2-vCPU/4-GB instance and $0.80/hour for one L4 GPU.
Illustrative arithmetic: $10 / $0.067 ≈ 149 running hours; $10 / $0.80 = 12.5 hours.
These are compute-only illustrations, not measured capacity, guaranteed model
compatibility, credit eligibility or a quote for this deployment. Exact instance
availability and requirements must be checked before creating a service.
[Credit rules](https://huggingface.co/docs/inference-providers/pricing) distinguish
credit types. [Scale-to-zero](https://huggingface.co/docs/inference-endpoints/guides/autoscaling)
reduces idle use but adds cold starts and may return 503 during initialization.
Keep a demo endpoint warm deliberately or use the local adapter; stop/scale down
hosted experiments when finished.

## Encoding defaults to validate before the first real build

- Proposed baseline: text-only, 768 dimensions, mean pooling/projection as shipped,
  explicit L2 normalization. Use float32 on CPU; bfloat16 only on supported hardware.
  The model card warns against float16. Quantization is a separate evaluated config.
- Queries use `task: search result | query: {query}`. Documents use
  `title: {title} | text: {content}` with `none` for an absent title. The card notes
  that `prompt_name="Document"` assumes no title; do not double-prefix a manually
  formatted document. Preserve literal chunks separately from embedding inputs.
- Load unused vision/audio encoders disabled using the library's documented
  configuration. Pin model commit, tokenizer, package versions, precision and
  exact templates before publishing `ops.model_configurations` as verified.
- Count the prefix plus content against the embedding tokenizer's real limit;
  no silent truncation. Shorter vector dimensions require explicit configuration,
  renormalization and evaluation, not a query-only switch.
- Verify vector shape/non-finite/zero rejection, query/document space parity,
  synonym queries, EN/DE/FR/IT and pilot recall. Cache by full encoding/input hash.

Both local and hosted adapters are implemented. `EMBEDDING_BACKEND` selects them
explicitly through `models/embeddings/configured.py` for build/benchmark/query.
All paths require `EMBEDDING_CONFIGURATION` matching the published snapshot.
HF additionally requires endpoint/token, supplied model revision and pinned local
tokenizer JSON; local mode requires full assets. Model-name/dimension hints alone
cannot configure a valid index. See [HF setup](HOSTED_EMBEDDINGS.md) and
[live setup](LIVE_SETUP.md). Keera chat aliases are not embedding models.
