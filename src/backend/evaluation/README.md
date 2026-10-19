# Retrieval evaluation

Run `python -m backend.evaluation --help`. The CLI reads an existing operator-owned
run/capture and compares lexical, dense, RRF and optionally reranked retrieval.
It creates no case, snapshot, source, grant or migration. Hosted encoding is an
explicit runtime dependency. Results include immutable pins, original source
links/IDs and elapsed search + entity-projection time; outputs default to ignored
`.local/` with private permissions. No prompts/provider bodies/secrets are logged.

The candidate suite in `docs/evaluation/PILOT_QUERIES.json` contains **no gold
labels**. A reviewer must independently validate expected typed entity IDs against
source passages, then set `reviewed`, `reviewer` and `expected_entity_ids` in a
versioned suite. Unreviewed results never receive a quality score. The primary
metric reuses intent-balanced unique-entity Recall@10; repetitions measure timing
without overweighting wording variants. Missing accepted shared entities is an
observable corpus limitation, not evidence that raw source passages are irrelevant.

Use the same snapshot/config/suite for all strategies. Single-run timing is a
smoke check; repeat and report hardware/cache/provider conditions for benchmarks.
See `docs/challenge/EVALUATION.md` for negative/ambiguity and field-support audits.
