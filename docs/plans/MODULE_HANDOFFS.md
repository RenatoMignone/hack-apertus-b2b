# Agent work routing and module handoffs

**18 October 2026 · Post-integration feature routing.** Start at root `AGENTS.md`, then
read this table and only the focused owners for the assigned feature. The
[execution graph](EXECUTION_GRAPH.md) and [processing contract](REPORT_PROCESSING_BOUNDARIES.md)
are the common system design. These are logical modules in one backend, not a
requirement to deploy a service for every row.

The [integration handoff](../team/INTEGRATION.md) describes the merged baseline.
The [team index](../team/README.md) marks completed lane assignments as historical.
Use the implemented [service contracts](../team/SERVICE_CONTRACTS.md) and current
code; allocate shared changes to one integrator for each new task.

## Current baseline and boundaries

Implemented: authenticated FastAPI/application, durable LangGraph worker, A/B/C
reasoning/retrieval/evidence adapters, deterministic PDF, HTTP React frontend,
PostgreSQL/pgvector through `0008_live_corpus`, artifacts, checkpoints and
masked tracing. Cross-lane tests use synthetic inference/embeddings. Team-host
migration, verified model assets, published corpus and live deployment remain gates.

**The frontend belongs to another teammate. Do not modify anything under
`src/frontend/` in backend/documentation tasks.** Read its existing `NavigatorApi`
and types to understand the consumer. Describe needed changes in the HTTP handoff
and coordinate them with that teammate. Source flags, HTTP polling and strict
review/export gates are now implemented; mock mode is an explicit demo choice.
The historical sibling repository, supplied assets/transcripts and submission
root template remain protected. Do not commit/push or migrate shared services
unless the current task explicitly authorizes it.

## Feature → focused context and work boundary

Paths in the next table are relative to `src/backend/`. Focused docs are in `docs/`.
Use the actual contracts/repositories as implementation truth; docs describe intent.

| Work package | Read after the common design | Write boundary | Required handoff / acceptance |
| --- | --- | --- | --- |
| HTTP and application integration | [HTTP contract](FRONTEND_BACKEND_API.md), [frontend view](FRONTEND_PLAN.md), `api/README.md`, `application/README.md`; read frontend API/types | `api/`, `application/`; shared DTO changes coordinated | Authorized commands, durable 202/status URLs, existing frontend projections, revision/idempotency errors; no SQL/model calls in handlers |
| LangGraph orchestration | [operations](OPERATIONS_PLAN.md), [case lineage](../data/CASE_STATE_AND_LINEAGE.md), `workflows/README.md` | `workflows/` | Typed stages, parallel DB/web join, budgets, clarification interrupt/resume, cancel/recovery and pinned references; no HTTP dependencies |
| Taxonomy and interpretation | [processing](REPORT_PROCESSING_BOUNDARIES.md), [schema](../data/RELATIONAL_SCHEMA.md), [pilot](../challenge/PILOT_SCOPE.md), `contracts/pipeline.py` | Profile data under `config/profiles/`; interpretation service in `evidence/` | Reviewed versioned concepts/aliases; `CaseInterpretation`, full intent preserved, targeted blocking questions; unknowns/multiple fields allowed |
| Apertus adapter | [inference integration](../data/INFERENCE_CONFIGURATION.md), [model contracts](../data/BUILD_AND_OPERATIONS.md), `models/README.md` | `models/reasoning/` | Bounded typed calls, tool-capable versus thinking routing, schema repair, usage/timeout errors; no workflow or access policy |
| Embeddings | [embedding deployment](../data/EMBEDDING_DEPLOYMENT.md), [retrieval](../data/RETRIEVAL_SPEC.md), `contracts/data.py` | `models/embeddings/` | Existing `Embedder` port; document encoding adapter for index builds; compatible config hashes/token budgets, finite nonzero vectors; benchmark CPU first |
| Reranking | [retrieval](../data/RETRIEVAL_SPEC.md), [model roles](../data/BUILD_AND_OPERATIONS.md), `contracts/data.py` | `models/reranking/` | Existing `Reranker` port returns one finite relevance score per input passage; separate from factual assessment |
| Corpus population and hybrid retrieval | [Data handoff](../data/INGESTION_RETRIEVAL_HANDOFF.md), [final schema](../data/RELATIONAL_SCHEMA.md), [exact field inventory](../data/SCHEMA_REFERENCE.md), [retrieval](../data/RETRIEVAL_SPEC.md) | `ingestion/`, `data/retrieval/`, scoped model adapters | Populate supported entities/claims and exact text; publish compatible snapshots; no alternate schema, retired tables or report/frontend edits |
| Web discovery and fetch | [web research](../data/WEB_RESEARCH.md), `ingestion/README.md`, research/corpus repositories | `ingestion/` | Separate search provider and Crawl4AI tools; `FetchedSource`, actual page text/locators and failures; deduplicate against whole pinned corpus; case-local flags |
| Evidence preparation | [processing](REPORT_PROCESSING_BOUNDARIES.md), [pack authority](ARCHITECTURE.md#evidence-pack-the-report-generation-gate), [case storage](../data/CASE_PIPELINE_STORAGE.md), evidence repository | `evidence/` | Bounded extraction/semantic assessment; exact statement/support in `ClaimAssessment`; code freezes `ReportEvidencePack`; no report drafting |
| Draft generation and checking | [processing](REPORT_PROCESSING_BOUNDARIES.md), [output](OUTPUT_REPORT_STRUCTURE.md), draft repository and `contracts/pipeline.py` | `reports/generation/`, `reports/validation/` | `DraftRevision` + separate `DraftAssessment` of its exact hash; claim-backed reasons; unsupported text cannot pass just because JSON validates |
| Review and PDF export | [output](OUTPUT_REPORT_STRUCTURE.md), [case storage](../data/CASE_PIPELINE_STORAGE.md), HTTP handoff | `reports/rendering/`; application owner handles commands | All cards reviewed, one kept, exact result/selection hashes; deterministic PDF contains kept reasons/citations/caveats; editable PPTX later |
| Persistence/retrieval/artifacts | [data router](../data/DATA_LAYER.md), focused schema/retrieval/lineage specs | `data/`, migration stream | Preserve RLS, immutable manifests/packs, namespaces, source support and revocation; fresh/upgrade tests; only this owner allocates migrations |
| Operations and observability | [deployment](../data/DEPLOYMENT.md), [observability](../data/OBSERVABILITY.md) | `deploy/`, `observability/` and scoped config | Existing local tracing/checkpoints remain separate from evidence; no secrets/full case prompts in traces; no shared deployment side effects by default |
| Quality/evaluation | [evaluation](../challenge/EVALUATION.md), pilot, processing/storage specs | Focused tests/evaluation fixtures in the assigned module | Intent-balanced Recall@10, literal and semantic support, honest partial/no-match, language coverage and isolation; no invented gold labels or scores |

## Shared interface ownership

- `contracts/data.py`: implemented search/storage DTOs, `Embedder`, `Reranker`,
  artifact port and immutable model configuration. Reuse their actual signatures.
- `contracts/pipeline.py`: implemented interpretation, fetched source, claim/draft
  assessments, supported claims, pack, reasons/revision and export request.
- `contracts/frontend.py`: pure projection helpers; full authorized
  `CaseDetail` responses are assembled in `application/projections.py`. Frontend
  types and the implemented HTTP handoff describe the consumer interface.
- Ingestion §7 owns shared source/read semantics; physical tables and policy live
  in the focused data specs. Do not implement a second evidence or case database.
- A needed port not yet in code is an explicit new contract, not an assumed
  callable API. Agree its small input/output/error surface in the owning doc,
  implement a fixture at that boundary, and name the consuming modules.
- Shared contract, migration, config and orchestration changes have one assigned
  integrator per task. Do not have parallel agents independently rename fields,
  allocate the same migration number, or rewire bootstrap/configuration.

## Working independently and integrating

Use one branch/worktree per teammate where practical. Before editing, inspect
working-tree changes; preserve others' work. Assign one row and a concrete outcome,
not “build the entire backend.” Implement only that row plus necessary agreed
contracts/tests; update its local README and focused doc. Shared changes should
state their consumer impact. Runtime calls use injected adapters; deterministic
fixtures permit work while an upstream module is absent. Production adapters
must report unavailable/unconfigured, never silently serve fixtures.

A feature is ready for integration when it has typed inputs/outputs and safe
failures; focused tests; a wired fixture/demo boundary; configuration documented;
remaining dependencies named in the [open questions](../project/OPEN_QUESTIONS.md).
Integrate contracts/persistence first, then adapters and evidence/report services,
then graph/application/API, then the separately owned frontend and renderer.
Independent branches can develop concurrently using those contracts.

## Example prompt

> Implement the **[module row]** for **[specific behavior]**. Read `AGENTS.md`,
> follow `docs/plans/MODULE_HANDOFFS.md`, and load its focused references. Inspect
> existing contracts and working-tree changes. Work only in **[assigned paths]**;
> leave `src/frontend/` untouched. Use deterministic boundary fixtures for missing
> dependencies and report unresolved integration inputs. Update the owning docs
> and run the module's meaningful checks. Do not commit/push or migrate shared data.
