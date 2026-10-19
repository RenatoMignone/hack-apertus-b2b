# Embedding encoder

`configured.py` selects hosted HF or provisioned local encoding for both ingestion
and runtime. Model revision, tokenizer, exact input templates, normalization and
dimension determine compatibility. Validate exact input token usage and finite
nonzero vector dimensions. Changed configuration requires a new build.

Read the [focused specification](../../../../docs/data/HOSTED_EMBEDDINGS.md) and [module map](../../../../docs/plans/MODULE_HANDOFFS.md).
Coordinate shared DTO/schema/configuration changes with their consumers and run
relevant boundary checks against isolated infrastructure.
