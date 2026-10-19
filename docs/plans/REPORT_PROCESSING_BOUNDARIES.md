# Research, evidence and report processing

| Stage | Input → output | Validation / responsibility |
| --- | --- | --- |
| Intake | Permitted prompt → owned case/input and queued run | Application authorization, idempotency and immutable corpus capture |
| Taxonomy | Pinned profile/version → compact relevant context | Reviewed vocabulary, unknowns retained |
| Interpretation | Full request + taxonomy → structured company/needs/query context | Apertus + typed validation; bounded repair; blocking clarification when necessary |
| Planning | Intent, keywords, concepts and constraints → `QueryPlan` | Preserve original text, negation and uncertainty |
| Research | Independent lexical/vector retrieval + optional web → passages | Authorized snapshot, compatible encoding, RRF/rerank, controlled fetch |
| Registration | Corpus + web → canonical evidence | URL dedup prefers pinned corpus; new web remains flagged/case-local |
| Extraction | Passages + needs → atomic entity/claim candidates | Apertus proposes local keys/support; code validates literal identities |
| Persistence | Candidates → canonical supported-record references | Scope checks, exact spans/hashes and original derivation lineage |
| Assessment | Persisted statements + actual passages → support and fit | Apertus assesses semantics; code validates IDs/coverage |
| Gap handling | Assessed gaps → bounded novel queries or partial result | LangGraph preserves prior work; deadlines, rounds and finalization reserve |
| Pack | Supported claims + context → frozen `ReportEvidencePack` | Deterministic membership/hash checks; unsupported claims excluded |
| Draft | Frozen pack → cited reason cards | Apertus writing; exact claim references; wording assessment |
| Review | Cards → keep/reject decisions and accepted review | All reviewed, at least one kept; exact hashes |
| Export | Authorized review + current revision → PDF / enabled PPTX | Deterministic renderer; access/hash checks before render and download |

Use batched task calls by responsibility (interpret/extract/assess/draft), rather
than one unconstrained call for the entire report or one call per output field.
Valid JSON controls structure; it does not prove semantic support. Reranking
improves relevance and cannot replace assessment. Empty/partial supported output
must retain coverage limitations and missing fields.

## Revisions and chat

Blocking answers resume the same durable run. Formatting requests reuse the
eligible frozen pack, then reassess wording. Focus/identity requests create a new
input and researched revision; earlier reports remain read-only history. A rejected
draft has bounded wording-only recovery and cannot waive support checks. Editing
manual plans also creates a new input/review cycle. Chat cannot execute arbitrary
commands or update shared knowledge.

Exact payloads are in `contracts/pipeline.py` and `contracts/services.py`.
[Operations](OPERATIONS_PLAN.md) owns deadlines/recovery;
[case lineage](../data/CASE_STATE_AND_LINEAGE.md) owns persisted hashes and versions.
