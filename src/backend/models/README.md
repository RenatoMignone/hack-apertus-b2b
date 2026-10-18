# Model adapters

Start with [module handoffs](../../../docs/plans/MODULE_HANDOFFS.md), then the
assigned adapter's local README. Provider details belong in
[inference configuration](../../../docs/data/INFERENCE_CONFIGURATION.md), encoding
in [embedding deployment](../../../docs/data/EMBEDDING_DEPLOYMENT.md), and pinned
identity in [model/build contracts](../../../docs/data/BUILD_AND_OPERATIONS.md).

- `reasoning/`: connected Keera Apertus 8B, explicit optional 70B; thinking is no-tools.
- `embeddings/`: proposed local text-only `google/embeddinggemma-2`; revision/runtime pending.
- `reranking/`: BGE-reranker-v2-m3 candidate; artifact/runtime still to validate.

Adapters receive permitted text and task contracts, return typed outputs/errors,
and never own case access, graph routing or corpus publication. Each model uses
its compatible tokenizer. Do not use chat output/token IDs as dense embeddings.
No live adapter, weights or inference benchmark exists yet. Source credentials
from backend env only; hosted providers require connected mode. Expose unavailable
when unconfigured, never fake a result or silently select hosted fallback.
