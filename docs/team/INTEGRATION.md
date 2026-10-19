# Integrated application baseline

18 October 2026. User-authorized integration of the completed backend lanes and
`ui-polish`, including the live frontend HTTP connection. Original lane handoffs
describe their pre-integration state; this document supersedes their remaining
composition/contract gaps.

| Branch / reviewed tip | Integrated responsibility |
| --- | --- |
| `backend/runtime` / `8b434c6` | FastAPI, authenticated application, durable LangGraph worker and export gates |
| `backend/intelligence` / `f1a7b61` | Apertus transport, extraction/assessment, pack/draft reasoning and actual PDF |
| `backend/backbone` / `ba77ea8` | Corpus ingestion, taxonomy, hybrid/relationship retrieval and scoped evidence persistence |
| `ui-polish` / `a5bd5d5` | Polished React screens and latest Sankey layout; integration adds the HTTP transport |

## Compatibility fixes

- `application.factories` implements the loader's exact `settings/engine/artifacts`
  signature. Retrieval loads only explicitly configured local embedding assets;
  fetched originals share C's observation cache. No hidden fixture fallback.
- Core manifest/lock includes JSON Schema, ReportLab and public-PDF extraction.
  `local-models` and `web` extras declare C's optional heavy dependencies. Resolve
  a target-platform wheel lock before packaging these extras offline; their real
  model/runtime compatibility is still unverified.
- Runtime and model transport share the same offline endpoint policy: loopback,
  `apertus` or `llm`; web remains disabled offline. Host-level isolation and
  packaged weights are still required for an actual air-gapped deployment.
- The container copies the supplied unchanged logo and injects its path.
  `PdfInput.interpretation` supplies attributed company summary, needs and Bern
  objectives. Claim-to-evidence citations and kept-only rendering remain intact.
- Extraction is limited consistently to 30 entities / 60 claims. Web budgets
  count discovery plus each fetched page; optional web exhaustion is a visible gap.
- Migration `0006_runtime_access` adds owner-checked, idempotent case-scope
  provisioning and restrictive RLS for private run stages and command receipts.
  Workers retain ordinary application credentials. Revoked/read-only scopes are
  not restored. Old command receipts lacking owner metadata remain hidden from
  app roles; a maintainer must review any historical backfill.
- Migration `0007_frontend_lifecycle` persists independent `on_hold` and closed
  `outcome` fields plus action answer notes. Existing combined statuses migrate
  forward. Historical migrations are unchanged.
- Historical evidence reads authorize owner, pins, literal support and revocation
  without requiring the old input to remain current. Research writes still require
  the active input. Existing stage keys bind the full input payload, including a
  changed pack after a draft gap; integration tests retain this behavior.
- Frontend defaults to HTTP, with a memory-only operator bearer token. It polls
  real runs, resumes observation after reopening, answers durable questions,
  persists actions/flags, and downloads authenticated PDF bytes after exact-hash
  review. All cards reviewed plus one kept gates export. Demo mode is explicit.
- Source flags are visible, limitations use readable wording, and missing search
  lineage is shown as unavailable instead of a zero-valued fabricated diagram.
  Search-trace population remains future work. Chat defaults conservatively to
  focus/research; the HTTP API also supports explicit formatting-only edits.

## Verification

**153 backend tests passed** on macOS/Python 3.13 with disposable PostgreSQL 18.0
and pgvector 0.8.1. It includes restricted-role API → real A/B/C modules → review
→ actual PDF, changed-input history, owner isolation, and persistent UI metadata.
Model responses and embeddings in these tests are explicitly synthetic.

Frontend `npm test` verifies eight transport/gate/recovery scenarios; `npm run build`
type-checks and builds. Browser smoke checks exercised token connection, intake,
actual run progress, cited results, the review gate and successful PDF download.
The PDF with company context was rendered and visually inspected. Updated routing
and build packages remove npm's reported advisories (`npm audit`: zero at this run).
Frontend transport tests: **8 passed**. Full backend command:
`PYTHONPATH=src NAVIGATOR_TEST_ADMIN_DSN=<disposable-admin-DSN> python -m pytest src/backend/tests -q`.

No shared-host migration, corpus ingestion/index publication, model-weight download
or paid provisioning was performed. No Docker runtime image was built on this PC.

## Run and deployment gates

Use the [first live run runbook](../data/LIVE_SETUP.md) and [current status](../project/STATUS.md).
Repository and shared-host migration head are `0007_frontend_lifecycle`; Eric’s
[completed rollout](MIGRATION_STATUS.md) supersedes the earlier 0004 observation.
Do not rerun that migration for runtime setup.

[Runtime access status](RUNTIME_ACCESS_STATUS.md) summarizes the owner-reported
private bundles and host-local checks. Peer-side SSH and pilot publication remain
pending. [Renato’s acceptance](BACKEND_RUNTIME_ACCEPTANCE.md) establishes partial
sandbox results, not live end-to-end acceptance. Start with the current live
runbook; use isolated infrastructure for destructive integration tests.

## Follow-up integration — 18 October 2026

Renato’s `66dbfd1` removes deployment-credential fallback from the test runner and
adds explicit disposable-DSN guards. Mohamed’s `ui-polish` through `c0c4812`
removes the desk/action screens, makes the board home, and adds structured result
fields, infrastructure cards and demo browser PDF/PPTX exports.

Merge resolution retains authenticated HTTP, memory-only tokens, source limitations
and exact hash/review gates for server PDF. Browser exports run only in explicit
demo mode and require all-reviewed/one-kept selections. Connected PPTX remains
unavailable. Existing action-item HTTP resources are retained without their old
standalone screens. Optional hierarchy/expertise/missing-field UI metadata is
backward-compatible; backend population is a separate enhancement.

## After merging

Each teammate fetches and fast-forwards their local `main`, then creates a new
feature branch from it. The completed lane branches can stay as historical
references; do not reset/rewrite them or merge `main` back merely to reuse their
names. If unfinished work must continue on an existing branch, merge current
`main` into that branch explicitly and resolve any overlap with its owner.

## Latest merged verification — 18 October 2026

On this Mac, the merged code passed **177 backend tests**, including all 58
PostgreSQL integration tests, on isolated local PostgreSQL 18.0 / pgvector 0.8.1.
No asyncio polling workaround was used. The first attempts were blocked by socket
sandboxing and an incorrect local admin role; the final run used the isolated
cluster’s configured administrator with approved local network access.
Frontend clean locked install, **11 tests** (8 transport + 3 export-policy),
TypeScript/build passed; npm reported zero vulnerabilities. Browser export bundles
produce size warnings; demo PPTX visual/PowerPoint compatibility is not certified.
These are synthetic engineering checks, not real corpus/provider acceptance.

Merged browser smoke also passed against the isolated synthetic API/worker:
board home, authenticated case creation, cited result, unavailable-trace wording,
blocked export before review, kept selection, exact-hash review, queued export and
HTTP 200 PDF download. Connected export offered PDF only. Source providers and
company input in this smoke were synthetic; no shared host was contacted.

## 19 October integration audit

Backend research completion `66b86cb` and the subsequent authorized frontend audit
supersede the earlier missing lineage/clarification/formatting status above. Current
shared schema head is `0008_live_corpus`. See [current status](../project/STATUS.md),
[backend acceptance](BACKEND_RESEARCH_COMPLETION.md) and
[frontend interaction checks](FRONTEND_RUNTIME_AUDIT.md). The combined suite passes
243 backend tests and 15 frontend tests/build. A real-provider partial report and
reviewed PDF passed; combined DB/web quality and target deployment remain open.
