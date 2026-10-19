# Model adapters

Reasoning, embedding and reranking are distinct injected roles with compatible
configuration/tokenizers. Apertus structured tasks have bounded validation/repair.
The embedding protocol is shared by ingestion and query runtime. Cross-encoder
rank scores indicate relevance, not truth. Assets are provisioned explicitly;
startup downloads nothing and offline mode rejects hosted dependencies.

Read the [focused specification](../../../docs/data/INFERENCE_CONFIGURATION.md) and [module map](../../../docs/plans/MODULE_HANDOFFS.md).
Coordinate shared DTO/schema/configuration changes with their consumers and run
relevant boundary checks against isolated infrastructure.
