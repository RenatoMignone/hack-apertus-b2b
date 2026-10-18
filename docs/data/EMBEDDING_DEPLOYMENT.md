# EmbeddingGemma 2: deployment recommendation

**18 October 2026 · U9 proposal; no weights downloaded or endpoint provisioned.**
The verified model reference is [google/embeddinggemma-2](https://huggingface.co/google/embeddinggemma-2).
It is distinct from `google/embeddinggemma-300m`. Use the model's own tokenizer,
not Apertus token IDs. This recommendation does not establish measured retrieval
quality or hardware throughput.

## Recommendation

**Run the text-only embedder locally on the shared team host first**, behind the
existing embedding port. Batch corpus embeddings once, persist them, and encode
only new/changed documents and user queries afterward. This avoids per-developer
endpoints and is compatible with an eventual offline runtime. Benchmark CPU
latency/memory before deciding on a GPU or hosted fallback.

The [Google developer guide](https://developers.googleblog.com/embeddinggemma-2-the-developer-guide/)
describes an on-device embedding model. The [model card](https://huggingface.co/google/embeddinggemma-2)
provides text-only encoder loading (270M active parameters), 768-dimensional
output, an 8,192-token context and separate query/document task formatting.
Those properties make local text-only serving a reasonable starting point;
they do not guarantee performance on the team's host.

| Option | When it fits | Remaining checks |
| --- | --- | --- |
| Local/shared host (recommended) | One corpus/query embedding space, no hosted runtime dependency, no credit burn | Actual CPU/RAM/GPU, supported package versions, warm latency, batch throughput |
| HF Inference Providers | Quick connected experiments if this exact model/task is available to the account | Feature-extraction API semantics, revision/prefix/normalization control, quota and eligible credits |
| HF dedicated Inference Endpoint | Shared remote service when local performance fails the target | Compatible container/engine, region, billing, cold starts, exact encoder config and team authorization |
| HF Space | Explicitly managed experiment/service, not an assumed managed endpoint | Hardware/credit eligibility, sleep/auth/concurrency and operations |

A Hugging Face repository stores weights; it does not itself provide a dedicated
server. The model page currently exposes an HF feature-extraction inference
option, but account access and exact request/encoding parity are untested. Keep
local and hosted adapters interchangeable only after matching model revision,
processor, input templates, normalization, dimension and measured vector parity.

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

No live adapter consumes the proposed `EMBEDDING_*` environment keys yet. Examples
are a handoff, not implemented model serving. Keera's four supplied chat models
are not embedding models; do not send embedding requests to them.
