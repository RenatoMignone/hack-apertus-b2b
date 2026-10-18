# Case persistence, checkpoints and output lineage

**18 October 2026 · Case persistence implemented; live workflow/model integration pending.**
Read [data layer](DATA_LAYER.md), [schema](RELATIONAL_SCHEMA.md), and
[Phase 2](../plans/OPERATIONS_PLAN.md) for workflow semantics. PostgreSQL owns
business records; the LangGraph PostgreSQL saver owns resumable graph state.
Langfuse observations are linked diagnostics, not recoverable business state.

## Application records in `navigator.cases`

| Table | Key fields / relationships |
| --- | --- |
| `cases` | Case ID, owner/access policy, status, current input/result revision pointers |
| `input_revisions` | Immutable input ID, case ID, parent ID, permitted full message/context, creation time |
| `dialogue_turns` | Turn/case ID, role, text, target input/result/question ID, timestamp; role text is not public evidence |
| `runs` | Run ID, case/input ID, profile/schema/taxonomy/snapshot/build/model/prompt versions, case-manifest ID, state, budgets/usage, thread/trace correlations |
| `questions`, `answers` | Question ID, target revision/field, required flag, reason/status, answer turn ID; stale answers cannot overwrite newer intent |
| `query_plans`, `retrieval_rounds` | Run/round, original/expanded query artifacts, reliable filters, budget/candidate counts, methods/timings/errors |
| `retrieval_hits` | Round/chunk/evidence/entity IDs, component ranks/scores, rejection/support state; persist enough to reconstruct selection |
| `matches` | Run/entity/need IDs, supporting claims, direct/adjacent status, relevance and evidence-strength reasons |
| `case_evidence_manifests`, `case_evidence_items` | Immutable manifest ID/hash, scoped document/claim/evidence IDs; new discoveries create a new manifest revision |
| `evidence_packs`, `pack_items` | Pack ID, run/manifest/input IDs, accepted facts/matches/derivations/gaps, literal support and hash; frozen before writing |
| `result_revisions`, `selections`, `reviews` | Parent result, pack, edit instruction, accepted/rejected findings, reviewer decision and exact reviewed revision/hash |
| `exports` | Export ID, reviewed result/selection set, template/logo/renderer versions, artifact/hash, source manifest and status |

Use explicit association tables for pack-to-claims/evidence and match-to-support
joins; validated JSON payloads may carry structured need/argument details. The
same evidence contracts apply to public and case-private documents. A pack may
use only the pinned shared snapshot plus the run's eligible case manifest.

## Durable execution

```text
draft → intake_validated → interpreting → researching_company
      → retrieving → validating → evidence_pack_ready
      → drafting → ready_for_review → export_ready → exported
```

Active stages can become `needs_clarification`, `partial`, `failed` or `cancelled`.
Keep the last successful stage and explicit failure reason. Partial evidence can
produce a partial pack/result; it is not silently promoted to complete coverage.

Create a server-controlled UUID thread ID for each run, scoped to its authorized
case. Persist the run/thread relationship; subsequent clarification resumes that
thread with the targeted answer. A changed intent after completion creates a new
run/revision, with references to reusable evidence. Do not reuse one global thread
for unrelated companies or trust a client-supplied thread ID as authorization.

Use LangGraph's PostgreSQL saver and its migrations in the separate `langgraph`
database. Checkpoints hold execution state, references, versions and pending
questions; avoid serializing entire corpora or raw files into every checkpoint.
Relevant permitted dialogue may still appear there, so apply case retention and
access controls. Do not hand-edit framework checkpoint tables.

## Writes, retries and concurrency

1. In a `navigator` transaction, validate owner/revision, persist the run's stage
   result and enqueue any durable follow-up work. Use unique idempotency keys
   such as `(run_id, stage, input_hash, config_hash)`.
2. Record artifact references only after bytes are durably stored and verified.
   External fetch/model calls execute outside long-running SQL transactions.
3. Advance the graph/checkpoint after committing business state. On resume,
   reconcile the stage key and reuse already committed outputs.
4. No distributed transaction is assumed across application DB, saver, artifact
   store or Langfuse. A crash between commits must be recoverable without duplicate
   facts/exports. A trace delivery failure never invalidates accepted evidence.

Use optimistic revision checks for edits and current-result pointer updates.
Concurrent exports bind to their explicit reviewed revision, not an unversioned
`latest`. Lease/lock jobs to prevent duplicate active workers; stale leases expire
under a documented recovery policy. Cancellation stops new work, preserves
completed evidence and prevents late responses from replacing a newer revision.

## Revision and publication rules

| Edit/event | Reuse | Recompute or invalidate |
| --- | --- | --- |
| Shorten/reword/change layout | Accepted evidence pack | New draft validation, review and affected exports |
| Change need, priorities or exclusion | Unaffected company/source facts | Query plan, matches, pack and dependent result/export |
| Correct company identity | Compatible public evidence only | Identity-dependent facts, matches and conclusions |
| New corpus snapshot | Existing run stays pinned | New run uses new snapshot; never silently refresh a completed answer |
| Source permission revoked | Only still-authorized material | Block dependent evidence reads; retire/invalidate affected exports and caches |

Reviewed case records can later enter an eligible historical-case dataset through
the same staging/validation/publication interfaces. Do not publish cases, learn
from user corrections, update taxonomy or embed generated reports automatically.
No historical dataset currently exists. Unknown outcomes remain unknown.

## Required integration checks

- Restart after a committed stage but before checkpoint save; reuse the output.
- Resume a question in the right case/revision; reject stale/unauthorized replies.
- Isolate two concurrent cases and scopes in queries, checkpoints and caches.
- Reword a report without repeating retrieval; refocus it with new bounded retrieval.
- Trace the exact reviewed pack/result/template to an export and its citations.
- Revoke supporting evidence and block dependent reads even for an old snapshot.

These are acceptance cases for future implementation, not completed tests.

## U8 case pipeline extension

[Case pipeline storage](CASE_PIPELINE_STORAGE.md) owns the new tables, manifest
eligibility, supported-claim assessments and reason-level selection/review hashes.
Legacy match selections remain historical. New accepted reviews/exports require
the v2 reason workflow; rejection is editorial and does not retract a claim.
