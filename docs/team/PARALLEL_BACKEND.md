# Three exclusive backend work lanes

> **Historical lane record — completed and merged, 18 October 2026.**
> Original instructions/results below describe that lane before integration.
> Its pending integration requests and ownership freezes are superseded by the
> [merged baseline](INTEGRATION.md) and [current status](../project/STATUS.md). Do not rerun this as a new task.

18 October 2026. This is the ownership plan for the current three-person backend
build. It overrides the broader example write boundaries in MODULE_HANDOFFS for
these three tasks. It does not assign frontend work. Implementation has not been
performed merely by writing these prompts.

## Start and isolation

Give each person one complete [prompt](prompts/01_RUNTIME.md):
[A: runtime](prompts/01_RUNTIME.md), [B: intelligence/reports](prompts/02_INTELLIGENCE.md),
[C: data backbone](prompts/03_BACKBONE.md). Each uses a separate clone or worktree
and branch from the pushed schema-0005 baseline. Never run agents in the same
checkout/index or have two agents own the same lane. Separate virtualenvs, ignored
local env files and lane-prefixed test services prevent environment collisions.

Suggested branches: `backend/runtime`, `backend/intelligence`, `backend/backbone`.
In a clean checkout, fetch origin and create only your own worktree, for example:

```bash
git fetch origin
git worktree add -b backend/runtime ../navigator-runtime origin/main
```

B/C substitute their branch and destination. If either already exists, inspect
and reuse the correct worktree or choose an unused suffix; do not delete/reset it.
Do not stash another contributor's work, use `git add .`, force-push, rewrite shared
history, merge into main or operate another worktree. Commit only explicitly owned
paths. The three copyable prompts authorize commits/pushes only to the assigned feature
branch when pasted as the task. They never authorize a main merge. A integrates serially
via reviewed merges/PRs; a non-overlapping file plan reduces conflicts but cannot
guarantee conflict-free Git or semantically compatible code without these checks.

## Exclusive ownership

All paths below are relative to the repository. A folder means its descendants,
except the explicit exclusions. Shared parent directories are not ownership.

| Lane | May create/change |
| --- | --- |
| A — runtime/integration | `src/backend/api/`, `src/backend/application/`, `src/backend/workflows/`, `src/backend/observability/`, `src/backend/deploy/`; `src/backend/config/` **except** `src/backend/config/profiles/`; `src/backend/contracts/services.py`, `src/backend/contracts/frontend.py`; `src/backend/pyproject.toml`, `src/backend/requirements.lock`, `src/backend/.env.example`; root `.env.example`; `src/backend/tests/runtime/`; `docs/team/runtime/` |
| B — intelligence/reports | `src/backend/models/reasoning/`, `src/backend/evidence/`, `src/backend/reports/`; `src/backend/tests/intelligence/`; `docs/team/intelligence/` |
| C — ingestion/database/retrieval | `src/backend/data/`, `src/backend/ingestion/`, `src/backend/models/embeddings/`, `src/backend/models/reranking/`, `src/backend/config/profiles/`; `src/backend/tests/backbone/`; existing **files directly inside** `src/backend/tests/` except `__init__.py`, `conftest.py`, `run.py`; `docs/team/backbone/` |

Everything else is read-only during this pass, including `src/frontend/`, root
submission files, original recordings/assets, `AGENTS.md`, existing canonical docs,
this plan/prompt set and `contracts/data.py`, `contracts/pipeline.py`,
`contracts/__init__.py`. Existing shared test bootstrap is frozen. Each lane can
add its own `tests/<lane>/conftest.py`; do not change root test fixtures to suit it.
B/C cannot create/change `models/__init__.py`, backend root files or the other's
subdirectories. A cannot edit data repositories, evidence/report implementations,
embedding adapters or root test fixtures. Updates to canonical docs are collected
in each lane's handoff and applied in a separate integration pass.

A alone assembles the dependency manifest/lock and environment settings. B writes
needed dependency/version ranges under `models/reasoning/requirements.in`; C under
`ingestion/requirements.in`. These are proposals, not substitute runtime manifests.
Install into isolated lane environments; A resolves and locks their union after
handoff. Do not auto-upgrade everybody's environment or share a writable venv.

Schema contract v1 at 0005 is frozen for filling/querying. C is the only owner of
any necessary future migration, but must report/justify it before changing the
contract used by A/B. No shared-host migration, model download, paid provisioning,
public data publication or broad Docker stop is implicit in a feature prompt.

## Communication and integration order

1. **A's first deliverable is a small contracts-only commit**, implementing the
   documented v1 interfaces in [service contracts](SERVICE_CONTRACTS.md). Keep that
   commit separate from API/runtime work. Publish it through the agreed team Git
   channel; the runtime prompt authorizes pushing that feature-branch commit.
2. B/C first read the contract document and can prepare their prompts/adapters/tests
   within owned paths. Before committing production imports of the new contracts,
   they merge A's exact contracts-only commit/branch (not an independently rewritten
   copy). A owns `services.py`; B/C report additive needs, never edit it themselves.
3. A/B/C implement with injected ports and deterministic fixtures. No HTTP between
   these modules: they run in the same Python backend process/worker. HTTP is the
   browser boundary; an optional remote embedding adapter is C's internal concern.
4. Each lane writes `docs/team/<lane>/HANDOFF.md`: entry points/signatures, tested
   commands/results, required env/dependencies, unavailable adapters, and contract
   requests. Include a compact readiness table with v1 API name, implementation
   import/factory, input/output, errors and tests. Teammates read these files from
   the feature branch or reviewed change, not a parallel write to shared notes.
5. A integrates B/C serially after their work is reviewed and authorized to merge,
   resolves dependency/config requests, and runs cross-lane fixtures then live
   smoke checks when configured. A owns the composition root; B/C supply factories.
   No lane changes another's files merely to get an import or test to pass.

If an upstream adapter is missing, return `unavailable` in production; only an
explicit test/demo profile uses fixtures. If a contract needs a breaking change,
record it in the requesting lane's handoff, continue independent tasks and wait
on dependent integration. Do not guess a second shape or silently rename fields.

## Common product gates

Read root AGENTS and the processing/execution docs. Preserve full user intent,
blocking clarification, independent lexical/vector retrieval, flagged case-local
web evidence, exact public support, assessed frozen pack, draft assessment,
per-reason keep/reject, revision hashes and PDF export gates. Rank is not truth;
editorial rejection is not factual rejection. No confidential document uploads.
LangGraph owns agentic execution/tool loops; LangChain owns adapters/structured
calls. Checkpoints/traces are not evidence stores. Offline disables network adapters.

A owns graph and application persistence decisions. B returns typed proposals and
assessments, never publishes corpus data or freezes packs itself. C owns faithful
source records and retrieval, never writes reports or launches another workflow.
Use evidence IDs and exact slices across boundaries, not untrusted model URLs.

## Models and graph retrieval

The committed default is **Apertus 8B**, not 7B; it was a provisional baseline,
not a measured quality winner. For the connected pilot, B should compare 70B first
for extraction/assessment/drafting against 8B using the same public fixtures and
record validity, unsupported claims, latency and quota behavior. Prefer 70B if
it meets the case deadline/quotas with better grounded outputs. This is a
recommendation, not a benchmark result or an automatic change to example settings.
Honor explicit `LLM_NAME`; do not silently switch models. A alone updates shared
configuration after selection. Gateway URL stays `https://gateway.keera.ch/api/v1`.
Non-thinking 8B/70B are the supplied tool-capable aliases; thinking variants get
no tools. [Provider details](../data/INFERENCE_CONFIGURATION.md) distinguish direct
CSCS documentation from Keera-specific behavior still needing verification.

“GraphRAG” in C's lane means supported entity/claim relationship expansion on the
final PostgreSQL schema alongside hybrid search. It does not authorize Neo4j,
a second graph database, generated community summaries treated as evidence, or
replacing the independent full-text/pgvector baseline.
