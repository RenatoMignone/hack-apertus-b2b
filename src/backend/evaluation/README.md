# Retrieval evaluation

`python -m backend.evaluation --help` compares lexical, dense, RRF and optional
reranking against an existing authorized capture. The candidate suite has no gold
labels; independent expected typed entities are required for scores. Preserve pins,
source references, timing and failures; outputs stay in ignored private storage.

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

## Frontend-independent retrieval proof of concept

`python -m backend.evaluation.proof_of_concept --env-file PRIVATE_ENV --run-id OWNED_RUN_ID`
runs the complete fictional demo brief and its three wording variants against an
existing authorized capture. It uses the production RRF adapter and configured
real embeddings, enforces read-only database connections, and creates no case,
capture, claim, grant or migration. Optional `--db-host` / `--db-port` selects an
explicit connection address for that same authorized database. The private env
must have exactly one binding and compatible assets; it is never printed.

Raw results default to ignored `.local/proof-concept/raw-results.json`. Every hit
is checked against its exact body slice and SHA-256. Accepted entity projections
are recorded separately; zero profiles must not be described as a successful
canonical-person search. The named demonstration examples were selected after
retrieval and inspected by the assistant, not independently labeled as gold.

`python -m backend.evaluation.render_proof_of_concept` renders the inspected receipt
as a PDF, Markdown summary and public rank/source JSON. It asserts the recorded
query/rank/source selection; changed rankings require fresh inspection. Pass
`--font` / `--font-bold` with Unicode TTF files outside Windows. Full texts remain
in the ignored receipt; only selected exact quotations are republished.

See [PoC outcome and reproduction](../../../docs/proof-of-concept/README.md).
This static fallback is distinct from the application's exact-review-gated report
export and from independent expert Recall@10 evaluation.

Read the [focused specification](../../../docs/challenge/EVALUATION.md) and [module map](../../../docs/plans/MODULE_HANDOFFS.md).
Coordinate shared DTO/schema/configuration changes with their consumers and run
relevant boundary checks against isolated infrastructure.
