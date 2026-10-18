# Project documentation

**18 October 2026 · Design and directory scaffold; application not implemented.**
Bern Economic Development Agency — Research & Expertise Navigator.
Current pilot: Bern diabetes technology; the engine must support other domains
through versioned profiles and rebuildable retrieval indexes.

## Start here

1. **[Visual architecture and pipeline](architecture.html)** — main reference;
   eight stacked diagrams from typed input through evidence preparation to report,
   plus domain changes, deployment and data ownership. Open locally; no external assets.
2. [Architecture contract](plans/ARCHITECTURE.md) — components/locations, text-only
   intake, domain profiles, evidence pack, target architecture and dependencies.
3. [Output structure](plans/OUTPUT_REPORT_STRUCTURE.md) — agreed brief sections.
4. Implementation detail: [ingestion/contracts](plans/INGESTION_PLAN.md), then
   [case operations](plans/OPERATIONS_PLAN.md). These are plans, not working code.
5. **[Data-layer build router](data/DATA_LAYER.md)** — PostgreSQL + pgvector,
   physical schemas, retrieval, cases/checkpoints, Langfuse and build gates.
6. **[Source structure](plans/SOURCE_STRUCTURE.md)** — frontend/backend split,
   component ownership and folder guidance; [HTTP handoff](plans/FRONTEND_BACKEND_API.md)
   for frontend integration. No server/UI or dependencies implemented.
7. **[Report-processing boundaries](plans/REPORT_PROCESSING_BOUNDARIES.md)** —
   retrieved data → `ReportEvidencePack` and pack → output; detailed mapping pending.

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
  stages. No deployment or quality result is yet measured.
- The company brief/PowerPoint is distinct from the hackathon technical report
  and pitch. Preserve root [README](../README.md), [report](../technical_report.md),
  [LICENSE](../LICENSE) and `src/`; code belongs in `src/`.
- Keep public-source claims traceable and source rights separate from code
  licensing. Template/logo are challenge-only. Supplied originals stay unchanged.

## Evidence and document ownership

**B1/N1:** supplied challenge/Notion baseline. **M1/M2:** local submission
README/report template. **T01–T05:** supplied transcripts, not audio-verified;
speakers' names/authority unverified. **U1–U7:** user instructions recorded in
sources. **P1:** dated historical preparation. Label requirements, stakeholder
clarifications, user decisions, proposals, measured results and unknowns.

Keep source snapshots, original transcripts/material and timestamped evidence
intact. Logical payloads remain in ingestion section 7; physical schema/search,
case persistence and tracing belong to the focused data specs. Model/tokenizer
sources and revisions are deferred. Evaluation/source history retain audit detail.
Update the visual and its owning focused document together when architecture changes.
