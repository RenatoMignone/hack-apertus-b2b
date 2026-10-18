# Runtime lane A handoff

> **Historical lane record — completed and merged, 18 October 2026.**
> Original instructions/results below describe that lane before integration.
> Its pending integration requests and ownership freezes are superseded by the
> [merged baseline](../INTEGRATION.md) and [current status](../../project/STATUS.md). Do not rerun this as a new task.

Lane A only, branch `backend/runtime`. Shared contracts were published separately:
`77bf4f8` (v1 DTOs/ports) and `1216c23` (additive PDF claim support). Merge those
exact commits before B/C production imports. Runtime code, tests and configuration
are implemented here; live B/C services and a frontend HTTP client are separate work.
No schema, ingestion, model/evidence/report implementation or frontend file was edited.

## Team integration instructions

Pushing this branch does not notify running agents or update their checkouts.
Each teammate must fetch and read this handoff explicitly. Their lane prompts
already require reading the published service contracts and exchanging handoffs.
In their own clean lane worktree:

```bash
git fetch origin
git show origin/backend/runtime:docs/team/runtime/HANDOFF.md
git show origin/backend/runtime:docs/team/runtime/HTTP.md
```

B/C should already have merged exact contracts commits `77bf4f8` and `1216c23`.
Do not independently rewrite or cherry-pick duplicate versions of those interfaces.
Full runtime integration uses a reviewed merge of `origin/backend/runtime` into
the team's integration branch (or their clean lane branch when agreed); fetching
or pulling `main` alone will not install this feature branch. Never reset a dirty
checkout or edit another lane to resolve an interface discrepancy.

- B: implement the async reasoning/PDF ports, consume `PdfInput.claims`, and publish
  exact factory imports, template/renderer identities and dependency proposals in
  `docs/team/intelligence/HANDOFF.md`.
- C: implement the backbone/web ports with authorized scope provisioning and stable
  persistence IDs, and publish factory imports/dependencies in
  `docs/team/backbone/HANDOFF.md`. Address the security details below.
- A/integrator: review both handoffs, assemble dependencies/settings centrally,
  configure factories, then run cross-lane fixtures and authorized live smoke tests.
- Frontend owner: use [HTTP.md](HTTP.md) and `/openapi.json` to replace mocks with
  authenticated HTTP calls/polling. No frontend implementation is included here.

Canonical `AGENTS.md`, processing docs and shared contract prose are frozen during
the parallel pass. In the later integration pass, their owner should route runtime
tasks here and replace old statements that HTTP/graph remain future work. This
handoff describes implemented lane A behavior; live B/C integration remains pending.

## Readiness and interfaces

| Boundary | Implementation / contract | Behavior |
| --- | --- | --- |
| HTTP | `backend.api.app:create_app`; `/openapi.json` | FastAPI `/api/v1`, typed intake/report views, bearer auth, safe errors, size limits and explicit CORS |
| Composition | `backend.application.bootstrap.Registry` | Per-user DB binding, configured B/C factories, no automatic migrations or fixture fallback |
| Application | `RuntimeApplication`, `application/persistence/` | Authorized reads, atomic commands/idempotency, existing repository gates, queue and per-node durable outputs |
| Graph | `backend.workflows.graph:build_graph` | LangGraph interpretation/interrupt, DB+web fan-out/join, extraction, ID persistence, assessment, frozen pack and assessed draft |
| Worker | `backend.application.worker.Worker` | Durable jobs, bounded execution, leases/heartbeat, per-run advisory lock and PostgreSQL checkpoints; independent of browser lifetime |
| B services | `ReasoningServices`, `PdfRenderer` in `contracts/services.py` | Typed async calls; no HTTP between modules; server factory supplies injected instances |
| C services | `BackboneServices`, `WebResearchTools` in `contracts/services.py` | Taxonomy/retrieval, source registration, extraction persistence and authorized evidence projection |
| Tracing | Existing local `SafeTracer`/Langfuse adapter | Masked metadata only, nonblocking delivery; automatic external LangSmith tracing is rejected |
| PDF dispatch | `PdfInput` → B renderer → artifact store → existing export gate | Claims/evidence for kept reasons; rechecks exact current approval before and after rendering |

Factories are **synchronous constructors** specified as `backend.module:function`:

```python
def make_services(*, settings, engine, artifacts):
    # Return an instance implementing the assigned async v1 port.
    ...
```

`settings` is `backend.config.runtime.RuntimeSettings`: `llm_name`, `llm_base_url`,
`llm_api_key` (secret), mode/budgets and other runtime settings. The model must
honor explicit configuration; 8B remains the example default, not a measured
winner over 70B. `engine` is the authenticated binding's SQLAlchemy engine;
`artifacts` is the configured artifact store. No provider/model calls in constructors.
Factory settings come from trusted server configuration, never HTTP request fields.
Missing required adapters yield `service_unavailable`, not invented/no-match results.

## Start locally

From repository root, use an isolated Python 3.12–3.14 environment:

```bash
python -m pip install -r src/backend/requirements.lock
python -m pip install --no-deps -e src/backend
navigator-runtime --env-file .env serve --host 127.0.0.1 --port 8000
navigator-runtime --env-file .env worker
```

Run API and worker in separate terminals. The CLI reads private plain `KEY=value`
files without overriding already exported variables. JSON binding values in that
file have no surrounding shell quotes. Never commit a real `.env` or credentials.

Prerequisites are migration 0005, provisioned DB application roles/principals,
a published source snapshot/profile and an artifact store. The data maintainer
owns migration/provisioning; runtime startup only checks schema compatibility.
For each user, generate a random bearer token privately and store its SHA-256
hex digest in the server's `RUNTIME_AUTH_BINDINGS` JSON. Example structure:

```json
[{"token_sha256":"64-lowercase-hex-characters","principal_id":"principal-uuid","namespace":"team","database_url_env":"DATABASE_URL"}]
```

Replace example values privately. The raw bearer token goes to its user; model/DB
keys do not go to the browser. For multiple DB roles, use a separate approved env
DSN name per binding. This preserves existing `session_user` principal checks.
There is no trusted `X-User-ID`, browser-supplied owner or anonymous production user.
The API uses bearer headers, no ambient cookie auth; CORS origins are explicit.
Listen beyond localhost only behind the team's authenticated HTTPS deployment.

Configure `LANGGRAPH_DATABASE_URL` to the separate framework database. Its owner
runs the following **explicitly**, once on an authorized target:

```bash
navigator-runtime --env-file .env checkpoints-setup
```

No graph schema is created by starting HTTP/worker. `worker --once` processes at
most one job per configured identity, useful for controlled smoke runs. Optional
container wiring is described in [deployment](../../../src/backend/deploy/README.runtime.md).
No runtime container image was built/published by this task.

## Configuration ownership and remaining inputs

A owns root/backend env examples, `config/runtime.py`, pyproject and the lock.
B/C send dependency ranges and exact factory imports in their own HANDOFF files;
A integrates them centrally. No B/C implementation branches/factories were available
for live integration when these runtime interfaces were built. Required settings:

- `RUNTIME_REASONING_FACTORY`, `RUNTIME_BACKBONE_FACTORY`: B/C factory imports.
- `RUNTIME_WEB_FACTORY`: optional C tools; connected only. Unconfigured web becomes
  a visible coverage limitation; unavailable required database/reasoning fails the run.
- `RUNTIME_PDF_FACTORY`, `RUNTIME_TEMPLATE_VERSION`, `RUNTIME_RENDERER_VERSION`:
  B's actual renderer plus explicit template/renderer identity before export.
- `LLM_NAME`, `LLM_BASE_URL`, `LLM_API_KEY`: preserve existing Keera interface.
  A queued run pins model alias/base URL/mode; configuration drift refuses execution.
- `RUNTIME_PROFILE_ID`, binding JSON and DSNs; deadline, round/tool/output budgets.
- Optional local `LANGFUSE_BASE_URL`, public/secret keys. Tracing failures do not
  change a case result. Source text, full prompts and credentials are never trace fields.

Offline requires an explicit local model URL and disables discovery/fetch. All
other adapters must also honor `RunContext.mode`; this flag does not prove a
network-isolated deployment or package model assets for you.

## Important B/C integration details

**B / Elias:** `PdfInput.claims` is the additive fix in `1216c23`. Derive citations
using `{claim.claim_id: claim.evidence_ids for claim in report.claims}` and the
supplied `report.evidence` records. A supplies only kept reasons' claims/evidence,
plus full validated draft and `kept_reason_keys`; render only those keys. Never
infer a claim/evidence association from list order, URLs or text similarity.
Provide factory imports, real renderer/template identity and dependencies. Exact
semantic checks remain B's responsibility; runtime membership/JSON validation
is not a substitute for entailment assessment.

**C:** `persist_extraction` must be idempotent by `(run_id, batch hash)` and return
stable canonical IDs when retried after a crash. Persisting a new private claim
requires matching case-scoped subject/evidence. Public evidence copies retain
corpus/curated origin and original lineage; actual new web pages stay unreviewed.
A consumes C's projections rather than trusting scope kind for source status.
Create/grant case scopes through a restricted internal mechanism after verifying
case ownership; application-role `scope_grants` writes are intentionally forbidden.
Do not use a browser-provided owner or disable RLS. This provisioning adapter is
C-owned, not supplied by the runtime. Lock the case before run/child rows when
composing repository transactions to match the runtime lock order. The runtime's
transaction-bound repository adapter is an example; do not keep a transaction
open across fetching, embedding or model calls.

Existing `ops.stage_attempts`/outbox RLS is namespace-based, while runtime node
outputs can contain private case data. HTTP/store access checks case ownership,
but that is not proof of isolation for direct DB clients sharing a namespace.
C must review case/run ownership policies and grants before a multi-user deployment;
A has not changed the frozen schema or its policies to claim stronger guarantees.

`read_evidence` serves both active and historical pack reads: authorize from the
case/snapshot/manifest and return exact stored provenance. Historical reads get
a new short read deadline, not permission to retrieve fresh facts. `retrieve`
returns independently fused lexical/vector hits plus supported source records.
Graph expansion remains C's supported PostgreSQL relationship retrieval.

## Execution/recovery guarantees and limits

HTTP mutation idempotency uses existing outbox records in the same transaction
as its business write; key is scoped by principal/namespace/operation. Reuse with
a different body returns 409. Durable runtime jobs and node outputs use existing
stage_attempts, with no new tables. Graph checkpoints use server-created thread IDs.
A worker restart reuses committed node outputs; losing the lease/cancelling or
changing input prevents late result publication. Session advisory locks are
held without a long SQL transaction; live connections do not cross worker threads.

External calls are at-least-once if a process dies after the provider/adapter
commits but before output recording. Bounded model calls may be repeated in that
window; C side effects must supply their own idempotence. There is no distributed
exactly-once guarantee across provider, artifacts, application DB and saver.
Clarification pauses on durable questions and resumes only after their targeted
answers. Its original deadline stays pinned; expired work requires a new run.
Research is limited to three rounds; one output repair belongs to B's task client.

Chat `kind` is explicit: formatting reuses the pack and revalidates, focus/identity
re-research. Unspecified chat uses conservative focus, never an unverified heuristic
that treats a request for new facts as wording-only. Invalid wording cannot export.
All cards reviewed and one kept plus exact result/selection hashes gate approval
and PDF. Switching current revision only accepts a pack for the current input;
history remains readable without silently restoring an old company intent.

## Verification

Runtime integration tests live only under `src/backend/tests/runtime/`; no shared
bootstrap was modified. Use disposable PostgreSQL with pgvector and the existing
NOLOGIN `navigator_app` role, then:

```bash
PYTHONPATH=src NAVIGATOR_TEST_ADMIN_DSN=postgresql://TEST_ADMIN@127.0.0.1:TEST_PORT/postgres \
  python -m pytest src/backend/tests -q
```

Tests cover actual HTTP/LangGraph/PostgreSQL behavior using explicit synthetic
B/C fixtures: end-to-end draft/review/export registration, source membership,
clarification across PostgreSQL worker restart, checkpoint-loss output reuse,
owner/role isolation, atomic idempotency, concurrent DB/web branches/workers,
request redaction/limits, no-match vs unavailable, offline mode, deadline/cancel,
model config drift, invalid draft budgets, and stale revision/selection downloads.
Synthetic PDF bytes verify registration/gating only; B must verify actual rendering.
Live Keera, embedding/retrieval quality and a multi-user deployment are untested.

Final local regression: **63 tests passed**, including the runtime suite, against
an isolated disposable PostgreSQL/pgvector cluster. Import checks and Ruff's F
checks passed. This verifies the runtime contracts/gates with fixtures; it does
not benchmark Apertus quality or certify B's real PDF layout.
An actual localhost API process served health/OpenAPI (23 paths), then stopped.
Compose configuration validated with a placeholder image solely for parsing;
the digest-pinned deployment image remains an operator prerequisite.
