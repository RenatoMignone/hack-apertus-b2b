# Agent entry point

Active repository: **hack-apertus-submission**, Bern Economic Development Agency
Research & Expertise Navigator. Preserve the hackathon submission template.
Work here; the sibling `hack-apertus-liebefeld` is historical and must not change.

## Integrated baseline

The three backend lanes and `ui-polish` are integrated. Read the
[integration handoff](docs/team/INTEGRATION.md) before starting new work. Create
fresh feature branches from current `main`; completed lane prompts/handoffs below
are historical ownership records, not a ban on separately authorized integration.

## Original three-person backend build

Use [exclusive lane ownership and Git workflow](docs/team/PARALLEL_BACKEND.md)
and [v1 service contracts](docs/team/SERVICE_CONTRACTS.md) for this parallel pass.
[Three copyable prompts](docs/team/prompts/01_RUNTIME.md) assign runtime (A),
intelligence/reports (B), and data backbone (C). Their narrower path allowlists
override the generic feature examples below; each lane edits only its own
READMEs/handoff docs. A alone publishes shared service DTOs/config/dependency locks.
Existing data/pipeline DTOs and the separately owned frontend stay read-only.

## Start a feature task

1. Read [module handoffs](docs/plans/MODULE_HANDOFFS.md) and select the row matching
   the user's feature. It gives the write boundary, focused docs and interfaces.
2. Read the compact [execution graph](docs/plans/EXECUTION_GRAPH.md) and
   [processing contract](docs/plans/REPORT_PROCESSING_BOUNDARIES.md), then the
   row's focused owner documents and nearest source README. Load only relevant context.
3. Inspect actual contracts/code and working-tree changes before editing. Preserve
   other contributors' work. Use injected adapters and explicit fixtures for
   missing dependencies; document needed shared-contract changes.
4. Check the [active open questions](docs/project/OPEN_QUESTIONS.md). Separate a
   real blocker from an unrelated open item; do useful independent work.

**Frontend is owned by another teammate. Backend/docs tasks must not modify
`src/frontend/`, including its types and README.** Read it to understand the
consumer; put proposed interface changes in the HTTP handoff for its owner.
Use separate branches/worktrees for parallel features when practical. Coordinate
shared contracts/migration numbers/configuration through one assigned integrator;
never overwrite another agent's work or independently rename shared fields.

## Current implementation and model configuration

- React/Vite defaults to authenticated HTTP, with explicit mock demo mode. Python
  contracts, FastAPI, durable LangGraph, A/B/C adapters, semantic task stages,
  PDF rendering and PostgreSQL persistence through `0007_frontend_lifecycle` are
  implemented. Final schema fields are authoritative;
  read [data handoff](docs/data/INGESTION_RETRIEVAL_HANDOFF.md) before ingestion or
  retrieval work and use the generated [field reference](docs/data/SCHEMA_REFERENCE.md).
  Synthetic integration checks are not a quality/model benchmark.
- Cross-lane execution is tested with synthetic model responses/embeddings and
  real disposable PostgreSQL. Shared-host migration, real corpus/index population,
  verified local model assets and a combined live provider run remain prerequisites.
- Connected inference: CSCS via Keera, `https://gateway.keera.ch/api/v1`, default
  `apertus-v1-5-8b`. Four supplied aliases and tool/thinking rules are in
  [inference configuration](docs/data/INFERENCE_CONFIGURATION.md). Key and quotas
  remain unverified for deployment; limited synthetic inference probes are in B's
  handoff. Use root [.env.example](.env.example); no real secrets in git.
- Embedding proposal: `google/embeddinggemma-2`, local text-only/shared host first;
  [deployment comparison](docs/data/EMBEDDING_DEPLOYMENT.md). Artifact reference is
  verified; exact revision/runtime/host and performance remain open. BGE reranker
  is a candidate. Each model uses its own compatible tokenizer.
- Pilot: Bern diabetes technology, covering UniBE, ARTORG and DCB as one ecosystem.
  Development host is shared Windows/WSL2/Docker with individual SSH tunnels;
  running end-to-end connected/offline deployments have not been established.

## Focused router

| Task | Owning context |
| --- | --- |
| Assign independent module work | [Module map and example prompt](docs/plans/MODULE_HANDOFFS.md), [source ownership](docs/plans/SOURCE_STRUCTURE.md) |
| HTTP/application/frontend handoff | [API handoff](docs/plans/FRONTEND_BACKEND_API.md), [frontend behavior](docs/plans/FRONTEND_PLAN.md) |
| Graph, interpretation, evidence or drafting | [Processing](docs/plans/REPORT_PROCESSING_BOUNDARIES.md), [operations](docs/plans/OPERATIONS_PLAN.md), [pack authority](docs/plans/ARCHITECTURE.md#evidence-pack-the-report-generation-gate) |
| Apertus calls, tool routing, keys | [Inference configuration](docs/data/INFERENCE_CONFIGURATION.md), [model/build contracts](docs/data/BUILD_AND_OPERATIONS.md) |
| Populate corpus or implement hybrid retrieval | [Data handoff](docs/data/INGESTION_RETRIEVAL_HANDOFF.md), [final schema](docs/data/RELATIONAL_SCHEMA.md), [exact fields](docs/data/SCHEMA_REFERENCE.md) |
| Embeddings, hybrid search, reranking | [Embedding deployment](docs/data/EMBEDDING_DEPLOYMENT.md), [retrieval](docs/data/RETRIEVAL_SPEC.md), [model/build contracts](docs/data/BUILD_AND_OPERATIONS.md) |
| Web research, scraping, citations | [Web research](docs/data/WEB_RESEARCH.md), [provenance](docs/data/DATA_AND_PROVENANCE.md), [ingestion §7](docs/plans/INGESTION_PLAN.md#7-shared-contract-v1--owned-here-consumed-by-phase-2) |
| Persistence, migrations or case history | [Data router](docs/data/DATA_LAYER.md), [schema](docs/data/RELATIONAL_SCHEMA.md), [case additions](docs/data/CASE_PIPELINE_STORAGE.md), [lineage](docs/data/CASE_STATE_AND_LINEAGE.md) |
| Runtime operations, checkpoints, tracing | [Deployment](docs/data/DEPLOYMENT.md), [observability](docs/data/OBSERVABILITY.md) |
| Review/export and branding | [Output content](docs/plans/OUTPUT_REPORT_STRUCTURE.md), [case additions](docs/data/CASE_PIPELINE_STORAGE.md), [supplied assets](docs/provided_material/README.md) |
| Product/pilot/evaluation | [Requirements](docs/challenge/PRODUCT_REQUIREMENTS.md), [pilot](docs/challenge/PILOT_SCOPE.md), [evaluation](docs/challenge/EVALUATION.md) |
| Challenge/workshop/source evidence | [Brief](docs/challenge/CHALLENGE_BRIEF.md), [recording findings](docs/recordings/RECORDING_INSIGHTS.md), [sources](docs/project/SOURCES.md) |
| Unknowns, decisions or submission | [Active questions](docs/project/OPEN_QUESTIONS.md), [decision history](docs/project/DECISIONS_AND_OPEN_QUESTIONS.md), [event/submission](docs/project/EVENT_AND_SUBMISSION.md) |

## Invariants across features

- Preserve root `README.md`, `technical_report.md`, `LICENSE`, `src/` and report
  target-architecture requirements. Working context belongs in `docs/`, code in
  `src/`. Retain `LLM_NAME`, `LLM_BASE_URL`, `LLM_API_KEY`; credentials stay backend-only.
- Operator reads confidential company plans/one-pagers outside the app and types
  permitted context. Confidential uploads to **any** model, including local, are
  forbidden under the current boundary. Public research PDFs are separate.
- Full intent, negation, attributed operator context and uncertainty survive
  interpretation. Taxonomy is versioned, multi-label and allows unknowns. Topic
  labels/keyword hits cannot prefilter away otherwise eligible vector matches.
- Public factual assertions resolve to exact source passages; semantic support
  must be assessed separately from rank or valid JSON. Never invent people,
  roles, projects, contacts, clinical suitability or willingness to collaborate.
- New web evidence stays flagged and case-scoped; prefer pinned corpus versions
  for duplicate URLs. A supported claim does not certify its source. No automatic
  shared-corpus updates from user edits, reports or case-time research.
- Query only final application tables; never build features on `legacy` or the
  frozen migration baseline. Update schema docs/migrations together for changes.
- Freeze supported `ReportEvidencePack` before drafting. Reason keep/reject is
  editorial, not truth approval. All cards reviewed plus one kept gates export;
  result/support/selection hashes bind approval. PDF first; editable PPTX later.
- All agentic execution uses LangGraph/LangChain. Database evidence is authoritative;
  checkpoints resume work and masked local Langfuse traces diagnose it. Neither
  is a fact store. Tracing failure must not block a case.
- External independent infrastructure only; no cantonal internal network access.
  Keera/hosted embedding requires connected mode. Offline needs packaged local
  inference/assets and disabled web tools, not a hidden hosted fallback.
- Preserve source rights, supplied templates/logo and transcripts. Use branding
  only for this challenge; do not automatically publish raw recordings/data.
  English is baseline; DE/FR/IT quality and historical-case scores need evidence.

## Keep context usable

Update the focused owner document and local README when a feature changes. Keep
this file a router. Record decisions with date/provenance in the history and
resolve entries in the active register; distinguish requirement, decision,
recommendation, measured result and unknown. Do not claim tests or services not
actually run. Check links, contract consistency and protected materials.

Commit/push only when the current user request authorizes it; do not migrate the
shared host implicitly. The discussion transcript is tracked following explicit
user publication authorization; preserve its contents.
