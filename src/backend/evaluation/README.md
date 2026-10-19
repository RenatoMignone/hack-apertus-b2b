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
real embeddings, permits temporary retrieval tables but no persistent writes, and creates no case,
capture, claim, grant or migration. Optional `--db-host` / `--db-port` selects an
explicit connection address for that same authorized database. The private env
must have exactly one binding and compatible assets; it is never printed.

Raw results default to ignored `.local/proof-concept/raw-results.json`. Every hit
is checked against its exact body slice and SHA-256. Accepted entity projections
are recorded separately; zero profiles must not be described as a successful
canonical-person search. The named demonstration examples were selected after
retrieval and inspected by the assistant, not independently labeled as gold.

`python -m backend.evaluation.render_proof_of_concept` renders the committed,
sanitized `docs/proof-of-concept/retrieval-results.json` into the standalone PDF.
It validates counts and selected rank/source/quote references, uses bundled Unicode
fonts and writes only the PDF. It does not update the JSON/README, require private
raw text or rerun source verification. Optional `--input`, `--output`, `--font` and
`--font-bold` select explicit paths. New collector runs require a separately
inspected public receipt; the historical rankings remain fixed.

See [PoC outcome and reproduction](../../../docs/proof-of-concept/README.md).
The document demonstrates retrieval; application review/export and independent
expert Recall@10 have separate acceptance records.

## Live SQL performance reproduction

Use an existing owned run and private JSON containing its original request and
up to five query variants. This performs no case/corpus writes or migrations:

```sh
python -m backend.evaluation.benchmark_retrieval --env-file PRIVATE_ENV --run-id OWNED_RUN_ID --queries-file PRIVATE_QUERIES.json --repeats 2
```

It compares one versus all supplied inputs under the same identity and capture,
with statements bounded by the existing timeout (at most 30 seconds). Eligibility
is prepared once per measurement, shared by lexical and exact dense ranking.
Keep the output out of git: queries, passage IDs and plans can reveal authorized
information. Use `--vectors-file PRIVATE_CACHE.json` only for explicit cached
`queries`, `vectors` and `config_hash` matching the capture/encoder; otherwise
the real encoder is called. Encoding time is separate from SQL timings.
Optional `--plans` adds separate bounded `EXPLAIN (ANALYZE,BUFFERS)` reruns;
these warm caches and are excluded from measured branch durations. No cold-cache
or unloaded-host guarantee is made. `--db-host`/`--db-port` select an explicit
address without changing the operator's credentials.

See [measured fix and rollout](../../../docs/data/LIVE_RETRIEVAL_PERFORMANCE.md).

Read the [focused specification](../../../docs/challenge/EVALUATION.md) and [module map](../../../docs/plans/MODULE_HANDOFFS.md).
Coordinate shared DTO/schema/configuration changes with their consumers and run
relevant boundary checks against isolated infrastructure.
