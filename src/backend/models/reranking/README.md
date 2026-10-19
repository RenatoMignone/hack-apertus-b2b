# Reranking adapter

[Setup, pinned model, measured checks and limitations](../../../../docs/data/RERANKING.md).

`local.py` implements the existing `Reranker.score(query, passages)` port. The
optional `score_with_details` returns exact windows and pair-token counts for
retrieval observations. Longer passages use complete literal windows; the original
query is never truncated. Invalid scores fail; budget/unavailability retains RRF
with an explicit limitation. Scores are not factual support or probabilities.

`provision.py` explicitly downloads/verifies the pinned compact multilingual model
at build time and runs a synthetic sanity check. Runtime is local-files-only and
checks configuration/revision/runtime/tokenizer plus an asset-hash manifest.
The factory loads weights lazily on first retrieval, not API construction.

Install `requirements.reranker.lock`; provision the model/configuration and set
`RERANKER_CONFIGURATION` / `RERANKER_MODEL_PATH`. The lock is measured on macOS
arm64/Python 3.13; verify wheels on other hosts. BGE remains an evaluation candidate.
