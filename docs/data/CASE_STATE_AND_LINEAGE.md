# Case persistence, checkpoints and output lineage

**18 October 2026 · Case persistence and durable workflow integrated; live pilot validation pending.**
Read [data layer](DATA_LAYER.md), [schema](RELATIONAL_SCHEMA.md), and
[Phase 2](../plans/OPERATIONS_PLAN.md) for workflow semantics. PostgreSQL owns
business records; the LangGraph PostgreSQL saver owns resumable graph state.
Langfuse observations are linked diagnostics, not recoverable business state.

## Application records in `navigator.cases`

| Table | Key fields / relationships |
| --- | --- |
| `cases` | Case ID, owner ID, namespace, status/revision, independent on_hold/outcome, current input/result pointers |
| `input_revisions` | Immutable input ID, case ID, parent ID, permitted full message/context, creation time |
| `dialogue_turns` | Turn/case ID, role, message, optional input ID, timestamp; role text is not public evidence |
| `runs` | Run ID, case/input/snapshot IDs, pinned configuration JSON, status, thread/trace IDs, last stage/failure |
| `questions`, `answers` | Question ID, target revision/field, required flag, reason/status, answer turn ID; stale answers cannot overwrite newer intent |
| `interpretations` | Run → structured `CaseInterpretation`; input/taxonomy pins resolve through the run |
| `claim_assessments` | Run/claim → exact assessed statement/support, outcome and validator |
| `case_evidence_manifests`, `case_evidence_items` | Immutable manifest ID/hash and parent/case IDs; items reference scoped evidence IDs; new discoveries create a new manifest |
| `evidence_packs`, `pack_items` | Pack ID, run/manifest/input IDs, accepted facts/matches/derivations/gaps, literal support and hash; frozen before writing |
| `result_revisions`, `draft_reasons`, `reason_claims` | Immutable draft/result, exact reason content/support and claim links |
| `reason_selections`, `reviews` | Per-card editorial selection and immutable approval of exact result/selection hashes |
| `exports` | Export ID, result/review/artifact IDs, template/renderer versions, selection hash, format and status |

Use explicit association tables for pack-to-claims/evidence and reason-to-claim
joins; validated JSON payloads may carry structured need/argument details. The
same evidence contracts apply to public and case-private documents. A pack may
use only the pinned shared snapshot plus the run's eligible case manifest.

The [final schema](RELATIONAL_SCHEMA.md) and [field reference](SCHEMA_REFERENCE.md)
supersede older conceptual field lists. Run pins include `snapshot_id` and
`configuration`; profile/taxonomy/build resolve through that snapshot. There are
no separate run columns for every model/prompt setting. Query plans and round
hits are serialized in `ops.stage_attempts.outputs`; pack payloads own matches.
No application query reads the retired legacy tables.

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

These behaviors have synthetic runtime/repository coverage; see the
[integration test scope](../team/INTEGRATION.md). Real provider quality, target-host
restarts and full retention/deletion propagation still require deployment checks.

## U8 case pipeline extension

[Case pipeline storage](CASE_PIPELINE_STORAGE.md) owns the new tables, manifest
eligibility, supported-claim assessments and reason-level selection/review hashes.
Populated retired match selections remain in the maintainer-only archive. New accepted reviews/exports require
the v2 reason workflow; rejection is editorial and does not retract a claim.
