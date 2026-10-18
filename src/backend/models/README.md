# Model adapters

- `reasoning/`: Apertus v1.5 8B, optional bounded 70B fallback.
- `embeddings/`: EmbeddingGemma 2 candidate, sources/settings deferred.
- `reranking/`: BGE reranking candidate, exact adapter/revision deferred.

Inputs/outputs follow narrow task-specific ports. Use validated immutable model
configuration; each model uses its compatible tokenizer/processor. Never pass
Apertus token IDs as embeddings. No weights, clients or executable stubs exist.

[Model/build contracts](../../../docs/data/BUILD_AND_OPERATIONS.md) own model
roles and deferred settings. [Retrieval](../../../docs/data/RETRIEVAL_SPEC.md)
owns query/document encoding compatibility. Adapters cannot decide case access,
publish facts, silently choose hosted fallbacks or conceal unresolved configuration.
