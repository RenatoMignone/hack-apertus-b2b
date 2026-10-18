# Project documentation

**18 October 2026 · Backend lanes and HTTP frontend integrated; live deployment pending.**
Bern Economic Development Agency — Research & Expertise Navigator.
Current pilot: Bern diabetes technology; the engine must support other domains
through versioned profiles and rebuildable retrieval indexes.

Start with the [integration baseline and deployment gates](team/INTEGRATION.md).
Read [current status and next tasks](project/STATUS.md), then the
[live setup runbook](data/LIVE_SETUP.md) for rollout. [Team documents](team/README.md)
separate current interfaces/integration evidence from the completed lane history.

## Start here

1. **[Agent/module handoffs](plans/MODULE_HANDOFFS.md)** — choose a feature row,
   read its focused docs and code, and respect the write boundary. Frontend is
   separately owned; backend agents leave `src/frontend/` unchanged.
2. **[Execution graph](plans/EXECUTION_GRAPH.md)** and
   [processing contract](plans/REPORT_PROCESSING_BOUNDARIES.md) — agreed end-to-end
   stages, inputs/outputs, evidence gates, chat revisions, reason review and PDF.
3. [Architecture](plans/ARCHITECTURE.md) and [interactive visual](architecture.html)
   — shared components/deployment; [source structure](plans/SOURCE_STRUCTURE.md)
   for module dependencies and [API handoff](plans/FRONTEND_BACKEND_API.md) for HTTP.
4. [Data router](data/DATA_LAYER.md) and [deployment](data/DEPLOYMENT.md) — existing
   PostgreSQL/pgvector persistence, retrieval, cases, checkpoints and tracing.
   Corpus/retrieval teammate starts at [data handoff](data/INGESTION_RETRIEVAL_HANDOFF.md);
   [exact schema fields](data/SCHEMA_REFERENCE.md) are generated from runtime metadata.
5. **[Inference settings](data/INFERENCE_CONFIGURATION.md)** — supplied Keera
   endpoint/model IDs; [embedding recommendation](data/EMBEDDING_DEPLOYMENT.md).
   Root [.env.example](../.env.example) contains placeholders, not a working key.
   [Hosted embeddings](data/HOSTED_EMBEDDINGS.md) documents the configured HF
   endpoint; [Windows LF fix](data/WINDOWS_SHELL_FIX.md) replaces the temporary workaround.
6. **[Active open questions](project/OPEN_QUESTIONS.md)** — integration decisions,
   prerequisites and recommended defaults; [history](project/DECISIONS_AND_OPEN_QUESTIONS.md)
   records provenance rather than another competing current backlog.

## Focused references

| Topic | Read |
| --- | --- |
| Challenge and requirements | [Brief](challenge/CHALLENGE_BRIEF.md), [requirements](challenge/PRODUCT_REQUIREMENTS.md) |
| Pilot and quality gates | [Pilot scope](challenge/PILOT_SCOPE.md), [evaluation](challenge/EVALUATION.md), [cases](challenge/WORKFLOWS_AND_CASES.md) |
| Technology choices | [Technical handoff](plans/TECHNICAL_OPTIONS.md) |
| Data-layer ownership and implementation route | [Data layer](data/DATA_LAYER.md), [relational schema](data/RELATIONAL_SCHEMA.md) |
| Embeddings and hybrid retrieval | [Retrieval spec](data/RETRIEVAL_SPEC.md), [model/build contracts](data/BUILD_AND_OPERATIONS.md) |
| Case persistence and tracing | [Case state](data/CASE_STATE_AND_LINEAGE.md), [Langfuse observability](data/OBSERVABILITY.md) |
| Collection and provenance | [Evidence rules](data/DATA_AND_PROVENANCE.md), [collection spec](data/ingestion/INGESTION_SPEC.md), [draft source registry](data/ingestion/sources.yaml) |
| Partner workbook, slide template, logo | [Original-material inventory](provided_material/README.md) |
| Workshop evidence | [Timestamped findings E01–E30](recordings/RECORDING_INSIGHTS.md), [original transcript inventory](recordings/README.md) |
| Decisions and unresolved inputs | [Decision log](project/DECISIONS_AND_OPEN_QUESTIONS.md) |
| Delivery and source history | [Submission](project/EVENT_AND_SUBMISSION.md), [sources/conflicts](project/SOURCES.md), [supplied Notion snapshot](sources/NOTION_CHALLENGE_2026-10-18.md) |

## Boundaries

- The operator reads confidential plans/one-pagers outside the app and types
  permitted keywords/context. Future PDF intake is disabled pending explicit
  permission and revised handling rules. Public research PDFs are separate.
- Current pilot requires UniBE, ARTORG and DCB; domain independence does not
  silently broaden scope. English output is baseline; DE/FR/IT are extensions.
- Proposed primary deployment target: air-gapped case runtime on independent
  infrastructure outside cantonal ICT. Collection/build are connected, separate
  stages. Synthetic local integration and earlier storage/restore checks are recorded;
  shared live deployment, model quality and air-gap operation remain unverified.
- The company brief/PowerPoint is distinct from the hackathon technical report
  and pitch. Preserve root [README](../README.md), [report](../technical_report.md),
  [LICENSE](../LICENSE) and `src/`; code belongs in `src/`.
- Keep public-source claims traceable and source rights separate from code
  licensing. Template/logo are challenge-only. Supplied originals stay unchanged.

## Evidence and document ownership

**B1/N1:** supplied challenge/Notion baseline. **M1/M2:** local submission
README/report template. **T01–T05:** supplied transcripts, not audio-verified;
speakers' names/authority unverified. **U1–U10:** user instructions recorded in
sources. **P1:** dated historical preparation. Label requirements, stakeholder
clarifications, user decisions, proposals, measured results and unknowns.

Keep source snapshots, original transcripts/material and timestamped evidence
intact. Logical payloads remain in ingestion section 7; physical schema/search,
case persistence and tracing belong to the focused data specs. Keera endpoint/model aliases and the EmbeddingGemma 2 reference are supplied;
authenticated behavior, immutable revisions and hardware still need validation. Evaluation/source history retain audit detail.
Update the visual and its owning focused document together when architecture changes.

## Current implementation boundary

FastAPI/authentication, durable LangGraph, reasoning/retrieval/web adapters,
evidence assessment, reviewed PDF export and the HTTP frontend are implemented.
Migration head is `0007_frontend_lifecycle`. The [status page](project/STATUS.md)
separates these capabilities from real corpus publication, model asset verification,
shared-host rollout and quality evaluation. Historical handoffs are dated records.
