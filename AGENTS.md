# Agent entry point

This is the active **Hack Apertus Liebefeld submission repository**, for the
**Bern Economic Development Agency — Research & Expertise Navigator** challenge.
Start with [docs/README.md](docs/README.md); load the additional documents relevant
to your task rather than reading the entire knowledge base every time.

## Current state and scope

- Challenge selected by the user on 18 October 2026. The delegated pilot focus
  is diabetes technology: glucose monitoring, automated insulin delivery and
  supporting digital tools; see [pilot scope](docs/challenge/PILOT_SCOPE.md). The
  selected data layer is PostgreSQL + pgvector, artifact storage, LangGraph with
  PostgreSQL checkpoints, and self-hosted Langfuse. Model roles are Apertus
  8B/optional 70B, EmbeddingGemma 2 candidate, and BGE reranking. Exact model
  sources/tokenizer packages/revisions are deferred; see the data-layer router.
  Development deployment is Docker Desktop/WSL2 on the user's shared team host;
  production hardware, roster and project name remain open.
- Authorized work includes documentation, a **runnable frontend in
  `src/frontend/` on mock data** (D12–D14), and the PostgreSQL hybrid RAG data
  layer. The frontend is not yet connected to the backend. `src/backend/` now
  contains Python contracts, repositories, migrations, tests, Docker Compose
  deployment and administration commands. Start runtime work at
  `docs/data/DEPLOYMENT.md`. Live model integration, collection and report
  processing remain separate work. Do not claim test results beyond checks
  actually run; pytest was unavailable during the latest validation.
- Work in this repository. The sibling `hack-apertus-liebefeld` is historical
  preparation context: **do not modify it**. Relevant context has been summarized
  here; routine work should not require reopening it.

## Visual reference and current intake

Start architecture/workflow work at [docs/architecture.html](docs/architecture.html),
backed by [ARCHITECTURE.md](docs/plans/ARCHITECTURE.md). The core is domain-independent;
sources, taxonomy, ranking/validation and evaluation belong to versioned profiles.
RAG indexes can be rebuilt without rewriting orchestration. Current intake is
manually typed permitted keywords/context. Confidential business plan and one-pager
PDFs stay outside the application; a future attachment adapter is disabled pending
explicit permission and revised handling rules. Public research PDFs are separate.
Proposed primary target is an air-gapped independent runtime; not yet tested.

## Task router

| Your task | Read |
| --- | --- |
| Add source components or hand off a backend task | [Source structure](docs/plans/SOURCE_STRUCTURE.md), [source router](src/README.md), then the component README |
| Integrate the frontend with the HTTP backend | [Frontend/backend API handoff](docs/plans/FRONTEND_BACKEND_API.md), [backend router](src/backend/README.md) |
| Design retrieved evidence → pack or pack → report processing | [Processing boundaries and open mapping work](docs/plans/REPORT_PROCESSING_BOUNDARIES.md), then the existing architecture/operations contracts |
| Understand the selected challenge | [Challenge brief](docs/challenge/CHALLENGE_BRIEF.md), [requirements](docs/challenge/PRODUCT_REQUIREMENTS.md) |
| Find the Notion supporting files or check branding restrictions | [Notion text snapshot](docs/sources/NOTION_CHALLENGE_2026-10-18.md), [data and provenance](docs/data/DATA_AND_PROVENANCE.md) |
| Understand stakeholder intent or check a recording claim | [Recording insights](docs/recordings/RECORDING_INSIGHTS.md), then the linked [original transcript](docs/recordings/README.md) |
| Design a user flow, result presentation or demo scenario | [Workflows and cases](docs/challenge/WORKFLOWS_AND_CASES.md), [requirements](docs/challenge/PRODUCT_REQUIREMENTS.md) |
| Work on the UI or connect the backend to it | [Frontend plan and data contract](docs/plans/FRONTEND_PLAN.md), code in `src/frontend/` |
| Plan crawling, extraction, entities or citations | [Data and provenance](docs/data/DATA_AND_PROVENANCE.md) |
| Build the data layer or change persistence | [Data-layer router](docs/data/DATA_LAYER.md), then its owning focused spec |
| Implement database migrations or evidence/taxonomy tables | [Relational schema](docs/data/RELATIONAL_SCHEMA.md) |
| Implement embeddings, hybrid search or reranking | [Retrieval spec](docs/data/RETRIEVAL_SPEC.md), [model/build contracts](docs/data/BUILD_AND_OPERATIONS.md) |
| Implement case history, graph resumption or output lineage | [Case state](docs/data/CASE_STATE_AND_LINEAGE.md), [operations plan](docs/plans/OPERATIONS_PLAN.md) |
| Add Langfuse tracing or deploy the data services | [Observability](docs/data/OBSERVABILITY.md), [build/operations](docs/data/BUILD_AND_OPERATIONS.md) |
| Choose architecture, retrieval or Apertus integration | [Technical options](docs/plans/TECHNICAL_OPTIONS.md), [decisions and questions](docs/project/DECISIONS_AND_OPEN_QUESTIONS.md) |
| Evaluate quality, grounding or sovereign operation | [Evaluation](docs/challenge/EVALUATION.md), [data and provenance](docs/data/DATA_AND_PROVENANCE.md) |
| Prepare report, pitch, video or delivery | Root [README.md](README.md), [technical_report.md](technical_report.md), [event and submission](docs/project/EVENT_AND_SUBMISSION.md) |
| Resolve uncertainty or update context | [Sources](docs/project/SOURCES.md), [decisions and questions](docs/project/DECISIONS_AND_OPEN_QUESTIONS.md) |

## Constraints to carry into every task

1. **Preserve the submission template.** Keep `README.md`, `technical_report.md`,
   `LICENSE` and `src/` at their existing paths. Code belongs in `src/`; working
   context belongs in `docs/`. Retain the report's mandatory target-architecture
   section. Do not import old online-hackathon layouts or invent a `make run`
   requirement. Preserve `LLM_NAME`, `LLM_BASE_URL`, `LLM_API_KEY` as the template's
   model configuration interface; never commit secrets.
2. Use **Apertus v1.5 8B or 70B** purposefully. Endpoint, exact served model ID,
   quotas and deployment have not been verified. Do not invent them.
3. Focus on **life sciences / medicine in the Canton of Bern**. The brief requires
   coverage of **UniBE, ARTORG and Diabetes Center Berne** as one ecosystem.
   The selected diabetes-technology demonstration does not remove three-source
   coverage. English is the baseline output language; DE/FR/IT support is desired.
4. Return structured, concise, source-backed matches. Never invent people,
   roles, projects, contact details, capabilities or willingness to collaborate.
   Distinguish evidence from a suggested adjacent application. Missing evidence
   warrants an explicit limitation or no-match result.
5. Use public source content. **Do not upload confidential company business
   plans to a model**, including a locally hosted model: the stakeholder's stated
   boundary is broader than cloud access. Public availability does not establish
   permission to redistribute website content or recordings.
6. Development and deployment must stay outside cantonal ICT/internal networks.
   Document a self-contained independent deployment and distinguish connected
   collection from offline runtime. A hosted development endpoint alone proves
   no air-gapped capability.
7. Follow the current PostgreSQL design (U6/D09), which supersedes Weaviate,
   SQLite and BGE-M3 as active defaults. Keep original evidence authoritative,
   case data isolated, and runs pinned to validated snapshots/model configs.
   Fuse lexical and vector candidates; inferred topic labels must not exclude
   semantic matches. Reranking never replaces claim-support validation.
8. LangGraph checkpoints and Langfuse traces are not the evidence store.
   Self-host Langfuse and its required services inside the deployment boundary;
   trace eligible, masked data only. Tracing failure must not stop a case.
9. Keep frontend/backend independent through HTTP. Backend code is split by
   responsibility under `src/backend/`; use narrow contracts/ports and focused
   files. The database implementation is authorized; frontend framework, scraper
   selection and complete report-processing algorithms remain separate decisions.
10. Retrieved hits must become a supported, frozen `ReportEvidencePack` before
    report generation. Detailed processing for retrieval → pack and pack → output
    still needs mapping; do not mistake high-level plans for settled algorithms.

## Keeping context reliable

- Treat the user-supplied brief, complete Notion text (N1), and local template
  as the current baseline. The XLSX inventory, PowerPoint template and PNG logo
  are supplied under `docs/provided_material/`; see its inventory for handling
  notes. Use the template/logo only for this challenge and preserve the root
  submission template.
  Record later verified organizer clarifications with dates and provenance.
- Recording evidence is timestamped in `docs/recordings/RECORDING_INSIGHTS.md`. Speaker
  numbers are local to each file; names and formal authority are unverified.
  Participant questions and technical suggestions are not official mandates.
- Label statements **requirement**, **stakeholder clarification**, **proposal**,
  **decision**, **measured**, or **unknown**, as appropriate. Log actual decisions
  and resolved questions in `docs/project/DECISIONS_AND_OPEN_QUESTIONS.md`.
- Keep supplied transcripts unchanged. Cite the file and recording-relative time.
  Do not publish transcripts, source datasets or external messages automatically.
- Update the relevant focused document and its source references when new facts
  arrive. Keep this file a compact router, not a second requirements document.
- Logical payload contracts remain in ingestion plan section 7; physical storage,
  retrieval, case persistence and tracing belong to the focused data specs.
  Update these owners and the visual together; avoid competing schemas.
- Source/component ownership belongs to `docs/plans/SOURCE_STRUCTURE.md`; HTTP
  handoff is a draft, with framework/auth/OpenAPI details still open. Keep local
  source READMEs aligned; create `.gitkeep` only for otherwise empty directories.
- For documentation changes, check relative links, evidence references and
  template/transcript preservation. Do not claim application tests or results
  before an implementation exists.
