# Prompt A — HTTP, LangGraph and runtime integration

> **Historical lane record — completed and merged, 18 October 2026.**
> Original instructions/results below describe that lane before integration.
> Its pending integration requests and ownership freezes are superseded by the
> [merged baseline](../INTEGRATION.md) and [current status](../../project/STATUS.md). Do not rerun this as a new task.

You are backend engineer A for hack-apertus-submission. Implement the runtime
lane completely within its ownership boundary; do not implement your teammates'
modules. The frontend has a separate owner. The other backend engineers own
intelligence/reports (B) and ingestion/database/retrieval/embeddings (C).

Read AGENTS.md, docs/team/PARALLEL_BACKEND.md and SERVICE_CONTRACTS.md first.
Then read docs/plans/REPORT_PROCESSING_BOUNDARIES.md, EXECUTION_GRAPH.md,
FRONTEND_BACKEND_API.md, OPERATIONS_PLAN.md, docs/data/CASE_STATE_AND_LINEAGE.md,
CASE_PIPELINE_STORAGE.md, INFERENCE_CONFIGURATION.md and the READMEs in your folders.
Inspect src/frontend/src/api/index.ts and types/contract.ts read-only to understand
the real consumer. Inspect existing repositories/signatures; do not assume APIs exist.

Work in a separate clean worktree/clone on backend/runtime from the pushed baseline.
Preserve others' changes. Your exclusive write paths are:
- src/backend/api/, src/backend/application/, src/backend/workflows/,
  src/backend/observability/, src/backend/deploy/;
- src/backend/config/ EXCEPT src/backend/config/profiles/;
- src/backend/contracts/services.py and src/backend/contracts/frontend.py ONLY;
- src/backend/pyproject.toml, src/backend/requirements.lock, src/backend/.env.example;
  root .env.example;
- src/backend/tests/runtime/ and docs/team/runtime/.
Everything else is read-only, including frontend, data/, ingestion/, models/,
evidence/, reports/, existing contracts/data.py and pipeline.py, shared test
bootstrap, existing canonical docs and AGENTS.md. Do not edit shared parent
__init__.py files. Record needed changes outside ownership in your own HANDOFF.md.

Deliver in this order:
1. Your FIRST separate commit implements ONLY the v1 ports/DTOs/errors from
   docs/team/SERVICE_CONTRACTS.md in contracts/services.py, plus focused contract
   tests in tests/runtime/. Publish that commit ID through the agreed team Git
   channel (push your feature branch) so B/C can integrate the exact same contract
   before production imports.
   Do not combine this bootstrap with runtime code. Do not independently rename
   existing DTOs. Coordinate changes before altering the new v1 contract.
2. Build the HTTP API/application use cases and backend composition root. Prefer
   FastAPI for this task unless repository evidence requires another framework;
   put the decision in your owned docs. Expose the existing frontend projections
   through /api/v1, OpenAPI and durable 202 + polling; implement safe auth-to-
   AccessContext mapping, revision conflicts, cancellation, clarification, chat,
   reason selections, exact review and authorized PDF request/download. Explicit
   dev identity mapping may be configurable; never accept arbitrary owner/principal
   IDs from browser fields. Do not write frontend code or SQL in route handlers.
3. Implement the real LangGraph graph and worker execution: persist intake/run;
   B interpretation + C taxonomy; blocking clarification; independent C hybrid
   retrieval and optional connected C web tools in parallel; dedup/registration;
   B extraction, C proposal persistence, updated evidence/manifest, B assessment;
   record assessments/freeze pack; B draft + exact draft assessment; persist result.
   Tool selection/execution, budgets, retries, repair bounds, interruptions and
   follow-up research are LangGraph/LangChain features. No hand-built alternate
   agent loop. Checkpoint/resume and stage outputs must survive disconnect/restart.
4. Implement chat routing: wording reuses pack and revalidates; focus/new facts
   re-retrieve; identity/objective changes reinterpret. Preserve editorial choices
   only for unchanged content/support. Export requires every card reviewed and
   at least one kept, exact review/selection hashes, and fresh access checks.
   B's renderer receives a validated kept-only report input; it cannot retrieve.
5. Integrate injected B/C factories after their handoffs. Until available, use
   deterministic port fixtures ONLY in explicit test/demo mode; real production
   dependencies return unavailable. Offline disables hosted models/web. Do not
   invent completion percentages or present fixture answers as real output.
6. Own env/settings, bootstrap and dependency locking. Preserve LLM_NAME,
   LLM_BASE_URL, LLM_API_KEY; never print secrets. Honor an explicit model choice.
   Existing examples are 8B, not 7B; B will compare 70B/8B and report recommended
   routing. Do not silently switch or mix model identities in a pinned run.
   Consume B/C dependency proposals, lock once centrally, and document startup.

Reuse existing repositories/checkpoint/tracing adapters; no transaction stays open
across model/network calls. Do not bypass scopes, weaken provenance, invent a
new schema or use legacy tables to work around a missing adapter. Production
tracing is masked/nonblocking. Do not start/migrate shared infrastructure or stop
other teammates' Docker containers. Name any disposable test resources for this lane
and stop/remove only those you created.

Test your actual API/graph with fixtures: success; clarification/resume; independent
retrieval/web join; unavailable dependency vs no-match; bounded invalid-model output;
restart/idempotency; stale edits/cancellation; owner isolation; review/PDF gates.
After B/C integration, run meaningful cross-lane checks with authorized resources.
No live model-quality/deployment claim without evidence.

Write docs/team/runtime/HANDOFF.md with entry points, exact imports/factories,
commands, actual test results, env/dependencies, missing adapters, frontend-facing
OpenAPI/fixtures and requests to B/C. Update READMEs only in your owned folders.
This prompt authorizes commits and pushes to your own feature branch only. Stage
only owned paths, push the contracts commit first and push the remaining lane after
checks pass. Do not force-push, merge into main or rewrite shared history. Finish your lane;
report genuinely blocked integration and keep independent work moving.
