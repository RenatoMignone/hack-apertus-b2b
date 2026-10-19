# Backend research completion — 19 October 2026

Branch: `codex/backend-research-completion`, based on `main` at `e406d2b`.
The user authorized merging/pushing to main and a subsequent frontend integration audit.
This backend change performs no shared migration; frontend fixes follow separately.

## Implemented

- Reproduced the exact fictional Helvetic request against the live taxonomy:
  Apertus repeated an invalid activity-label array during its bounded repair.
  Long labels now use a neutral short display label while retaining all returned
  scientific wording in search terms. Public factual/reference validation remains.
- Separate non-blocking `research_questions` from ambiguity in user intent. Public
  unknowns are research tasks; missing user requirements still require clarification.
  Model-proposed operator leads must quote the supplied operator message.
- Bound extraction to twelve passages / 18,000 literal characters per batch, six
  batches and 30 entities / 60 claims per round. Failed batches contribute no
  claims; valid batches retain explicit gaps. All-invalid batches still fail.
  Context/claim budget exclusions are visible. Entity/claim local keys remain
  unique across batches. Only literal source names pass validation.
- Retrieve existing source identity/neighbor spans to give isolated paragraphs
  context. Page-title components are discovery hints; they are never factual
  evidence unless an actual existing source passage contains them.
- Generate bounded novel queries from extraction, support and need-fit gaps,
  including when some claims are supported. Preserve earlier evidence/claims,
  original intent, exclusions, per-run tool/deadline budgets and durable outputs.
  Do not repeat a query when no new proposal is available. Freeze the final pack
  after the bounded research loop; formatting-only edits still reuse the pack.
- Provision/integrate a pinned local multilingual reranker; exact windows, asset
  hashes, runtime checks and optional RRF fallback are documented in
  [reranking](../data/RERANKING.md).
- Persist actual query → evidence paths in the frozen pack and expose them through
  the existing HTTP trace projection. Resolve exact corpus mirrors; omit unknown
  paths. The writer still cannot generate its own trace.
- Need-fit reasoning receives only canonical support for accepted claims, rather
  than the entire retrieval pool. Follow-up planning reserves 120 seconds for
  finalization and compares remaining time with the observed previous-round cost.
- Failed run responses include additive `failure_detail`: failing stage, model
  task and safe schema field/error codes. No prompts, provider body or secrets.

## Verification and remaining acceptance

The refreshed baseline passed 224 tests on disposable local PostgreSQL. The expanded
suite now passes **241 tests**, including all disposable-PostgreSQL tests.
No shared-host tests use a migration/admin identity. Tests include partial gap follow-up/claim preservation,
reviewed PDF, clarification/restart, no duplicate research, literal batches,
query lineage, window coverage and safe HTTP model-failure diagnostics.

Your SSH key-only login and supplied host fingerprint now work from this Mac.
The live application identity/schema check passes, including after the user supplied
Eric’s changed LAN address. The pinned host key stayed the same. The README's new binding/profile
was applied privately while preserving the original DB password/operator digest.
The old fixture credentials are historical, not the current runtime identity.

Eric provisioned separate checkpoint and MinIO credentials with host-side checks.
The user subsequently supplied the three private service settings directly; these
were applied to ignored `.env` while preserving endpoint/bucket, operator token
and other credentials. **All network readiness checks now pass**, including
checkpoint-table access, S3 bucket access, current DB identity and local assets.
API/worker are running locally; authenticated API capabilities and health pass.
Private credentials and downloaded model assets remain ignored.

A real HF + hybrid + local-reranker probe passed against a case-owned live capture.
Probe cases/runs were cancelled; the one interrupted during the address change
was also found and cancelled using only its own request marker. No shared source/artifact/grant/migration was changed.
An initial structured-task probe on public retrieved paragraphs returned an honest
no-match because identity/capability support was insufficient in the bounded
context. This is **not** a successful useful report or real case-to-PDF acceptance.
Source-context and prompt-quality checks remain part of live acceptance.

## Renato's next acceptance run

1. Review/merge this branch through the team's normal integration process. Install
   the optional reranker lock and run the explicit provisioning command on his host;
   preserve all existing private credentials and operator token.
2. Restart his own API/worker only. Run readiness and a new Helvetic case (an old
   failed run may reuse durable outputs from the prior implementation).
3. On failure record `failure_detail`, last completed stage, model-task latency and
   whether extraction produced supported claims. Do not paste provider bodies or
   private prompts into shared docs. A valid no-match is not a quality pass.
4. Inspect direct versus adjacent capability matches, literal identity support,
   combined DB/web deduplication, source flags and recorded query links.
5. Review all cards, keep at least one and download the backend PDF. Then perform
   one controlled worker restart/resume using the actual PostgreSQL saver.
6. Record measured outcomes and update the [checklist](RUNTIME_CHECKLIST.md).
   Gold cases, reranker relevance comparison, supervision/checkpoint isolation and
   a demonstrated deployment target remain separate work.


## Actual provider/runtime checkpoint

All readiness checks, authenticated API health/capabilities and an actual
73,373-byte authorized source-artifact read/hash pass with Elia's separate
credentials. The real LangGraph worker wrote/read its PostgreSQL checkpoints and
completed interpretation, retrieval, extraction and assessment: six claims were
judged supported in its first live case. It then failed at `propose_pack.1` because
the fit task included the full 131,408-character retrieval output alongside
canonical support. This was an input-context failure, before the run deadline.

The fit payload now includes only accepted-claim support; a regression test adds
an unrelated 90,000-character passage and verifies it stays out of the model call
while remaining in coverage. Budget-aware follow-up stops expensive enrichment
before consuming finalization time. A fresh case reached a frozen pack and drafting, but unsupported wording was
correctly blocked. One bounded wording-only rewrite now reuses the unchanged pack
and receives a fresh exact-hash assessment. The assessor also receives only the
canonical passages cited by the pack, rather than UUIDs without source text.
Draft-only retries resolve and validate these passages through the backbone port.
Bulk retrieval/provenance remains outside the model context. The completed acceptance below records the later reviewed PDF result.

## Completed live acceptance — 19 October 2026

The actual Mac API/worker, Eric's authorized live corpus, HF embeddings, local
reranker, Keera 70B, PostgreSQL saver and separate MinIO credentials completed a
cited partial report. Research and report generation used the same frozen pack;
a drafting-only retry exercised the existing report endpoint after the context
and assessor-source fixes. Five cards were published with 26 coverage caveats
and two recorded query/evidence links. This is not a comprehensive expert search
or a relevance benchmark. No web service was configured on this Mac.

All five cards were reviewed. The original German ARTORG passage directly
substantiates the kept interdisciplinary capability statement; the other four
were rejected editorially for this export. Exact-hash approval, worker rendering,
MinIO storage and authenticated download produced a **66,979-byte PDF**. Text
inspection confirmed the kept ARTORG statement/original URL and exclusion of the
rejected biosensing card. The private PDF and case receipts remain ignored.

Remaining: better named-expert/facility coverage and precise direct/adjacent fit,
combined DB/web acceptance, human-reviewed reranker comparisons and controlled
worker interruption/resume. This measured partial acceptance does not establish
production readiness, source trust or a required target deployment.
