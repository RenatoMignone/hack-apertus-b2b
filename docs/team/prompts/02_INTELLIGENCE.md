# Prompt B — Apertus, evidence reasoning and reports

You are backend engineer B for hack-apertus-submission. Implement the intelligence
and report lane. A owns HTTP/application/LangGraph/config/shared contracts; C owns
ingestion/database/hybrid+graph retrieval/embedding/reranking. Frontend is separately
owned. Do not implement an alternate server, workflow or database in this lane.

Read AGENTS.md, docs/team/PARALLEL_BACKEND.md and SERVICE_CONTRACTS.md first.
Then read docs/plans/REPORT_PROCESSING_BOUNDARIES.md, ARCHITECTURE.md (pack gate),
OUTPUT_REPORT_STRUCTURE.md, docs/data/INFERENCE_CONFIGURATION.md,
DATA_AND_PROVENANCE.md, CASE_PIPELINE_STORAGE.md, relevant contracts and your READMEs.
Inspect frontend reason/evidence types read-only to understand citation presentation.

Use your own clean worktree/clone on backend/intelligence from the pushed baseline.
Your exclusive write paths are src/backend/models/reasoning/, src/backend/evidence/,
src/backend/reports/, src/backend/tests/intelligence/, docs/team/intelligence/.
Everything else is read-only, including frontend, workflow/API/application/data/
ingestion/embedding/reranking folders, shared config/manifests/locks/env files,
existing contracts, canonical docs and AGENTS.md. Do not create shared parent
__init__.py files or rewrite a teammate's adapter to make your tests pass.

A first publishes a contracts-only commit implementing docs/team/SERVICE_CONTRACTS.md.
Integrate that exact commit before committing production imports. Until then prepare
owned prompts/adapters/tests against the written specification; do not create a
second production DTO/port definition. Report needed contract changes in your own
HANDOFF.md, where A can review them. Keep independent work moving.

Implement:
1. A LangChain Apertus client for CSCS via Keera:
   https://gateway.keera.ch/api/v1, bearer team key, exact configured model alias,
   bounded requests/timeouts/retries and validated structured outputs with at most
   one repair/task. The API key is injected, never logged/committed. Confirm actual
   gateway behavior with a key before assuming native JSON Schema/tool support.
   Non-thinking 8B/70B support tools per the supplied list; thinking aliases receive
   no tools. Return allowed tool proposals; A's LangGraph executes them.
2. The ReasoningServices v1 methods as small single-purpose tasks: full-intent
   interpretation against supplied reviewed taxonomy; bounded atomic claim/entity
   extraction from supplied evidence; semantic support/contradiction and need-fit
   assessment; supported pack proposal; concise cited Why Bern draft; separate
   assessment of the exact draft hash. Code owns IDs/provenance/slices, not the model.
   Missing need/intent/material ambiguity produces targeted blocking questions;
   unknown company name alone is not blocking. Preserve exclusions and uncertainty.
3. Produce local-key ExtractionBatch proposals, not invented canonical UUIDs.
   C persists/remaps them and A then supplies exact canonical claim/evidence IDs
   for assessment. Do not bypass same-scope claim constraints, publish a new public
   fact, directly query SQL or claim rank/JSON validity establishes truth. Unsupported
   or contradicted claims cannot become supported pack content. Honest partial or
   no-match output remains valid; never manufacture required fields.
4. Draft only from the frozen ReportEvidencePack, with claim-backed reasons and
   entries matching the existing frontend projections. No browsing/retrieval inside
   the writer. Missing support returns a typed gap to A. Editorial keep/reject is
   not factual validation. Rephrasing still needs exact-wording assessment.
5. A deterministic PdfRenderer v1 in reports/rendering/: kept reasons, source
   citations, direct/adjacent labels and material caveats, using challenge-only
   branding. A supplies authorized exact review/hash inputs; reject invalid kept
   keys and do not add model-generated facts. Verify actual rendered PDF pages.
   PPTX is later. Keep PDF libraries optional at import boundaries where possible.
6. Make models injectable/configurable. Existing default is Apertus 8B, not 7B;
   there is no benchmark proving it sufficient. Compare apertus-v1-5-70b first for
   extraction/assessment/drafting with apertus-v1-5-8b on identical permitted cases:
   valid schema, grounded support, ambiguity handling, latency, quota/usage. Recommend
   70B if it improves quality within budgets; do not claim results without a run,
   hard-code an override, silently fall back or change shared env examples yourself.
   EmbeddingGemma and reranker implementation belong exclusively to C.

All autonomous research/tool loops remain in A's LangGraph; your service methods
are bounded typed tasks. Inject evidence, model config and budgets through v1
ports, never cross-module HTTP. Do not hold database transactions during model calls.
Provide deterministic fixture clients to test malformed JSON, unsupported claims,
contradictions, tool/thinking restrictions, timeouts, partial/no-match, exact draft
hash and PDF citation/selection behavior. Real mode must report unavailable if
unconfigured, never silently use fixtures. No confidential plans/uploads to any model.

Write dependency proposals in models/reasoning/requirements.in; A owns pyproject/lock
and configuration. Document your importable factories, arguments/env requests,
fixtures, measured model comparison or untested status, PDF checks, test commands,
known gaps and interface requests in docs/team/intelligence/HANDOFF.md. Update only
owned READMEs. Use lane-owned local test resources and stop only your own services.
This prompt authorizes commits and pushes to your own feature branch only after
checks pass. Stage only owned paths; no force-push, main merge or shared-history rewrite. Complete the lane and leave a concrete integration handoff.
