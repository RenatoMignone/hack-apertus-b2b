# Ordered completion checkpoints — 19 October 2026

User-authorized order: implement, focused smoke/regression checks, commit/push,
then continue. Shared migrations and ingestion acceptance remain Eric's operations;
prepare/test locally, never migrate the shared host implicitly. Own-case search
comes first; agency-wide sharing is deferred. Confidential documents remain out.

| # | Delivery | State |
| --- | --- | --- |
| 1 | Retrieval-quality evaluation and performance measurements | Complete; focused tests + live read-only smoke passed |
| 2 | Source validation/tagging tooling on isolated data | In progress |
| 3 | Own-case similarity | Queued |
| 4 | Domain-independent configuration | Queued |
| 5 | Local DB/web and actual checkpoint restart tests | Queued |
| 6 | Reviewed PPTX and richer attributed case/output fields | Queued |

## Checkpoint 1

`python -m backend.evaluation --env-file .env --run-id OWN_RUN_UUID
--suite docs/evaluation/PILOT_QUERIES.json --output .local/retrieval-evaluation.json`
(on one line). Add `--strategies lexical dense rrf reranked` only when provisioned.
All strategies use the same existing authorized capture. The candidate suite has
no invented expected experts; independently reviewed labels unlock Recall@10.
The CLI writes local observations only. It never creates a case or mutates corpus.

Verification: 16 focused evaluation/backbone/cross-lane tests passed on disposable
PostgreSQL. One real existing-capture query measured lexical 9.77 s, dense 12.31 s
and RRF 19.29 s. An earlier hosted-encoder request failed transiently; the completed
repeat passed all three. These single-query timings are not statistical benchmarks.
No independently reviewed gold entities exist in the candidate suite, so no recall
score is claimed. Measurements/URLs/IDs stay in ignored local output.
