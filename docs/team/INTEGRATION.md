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
| `ui-polish` / `469c98d` | Polished React screens; integration adds the HTTP transport |

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

1. Maintainer backs up and explicitly migrates the application database to
   `0007_frontend_lifecycle`. Eric's last reported host was still on 0004; confirm
   its current state before scheduling. Never point disposable tests at it.
2. Provision application-role identity/token bindings, checkpoint database and
   artifact access. Publish an authorized corpus snapshot/profile separately.
3. Supply verified local embedding configuration/assets matching that snapshot.
   Optional reranker/web dependencies and provider settings need separate setup.
4. Start API and worker using [backend instructions](../../src/backend/README.md),
   then the [frontend](../../src/frontend/README.md). Run a small authorized live
   smoke before claiming connected/offline deployment or research quality.

## After merging

Each teammate fetches and fast-forwards their local `main`, then creates a new
feature branch from it. The completed lane branches can stay as historical
references; do not reset/rewrite them or merge `main` back merely to reuse their
names. If unfinished work must continue on an existing branch, merge current
`main` into that branch explicitly and resolve any overlap with its owner.
