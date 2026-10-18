# Project documentation

**18 October 2026 · Design documented; application not implemented.**
Bern Economic Development Agency — Research & Expertise Navigator.
Current pilot: Bern diabetes technology; the engine must support other domains
through versioned profiles and rebuildable retrieval indexes.

## Start here

1. **[Visual architecture and pipeline](architecture.html)** — main reference;
   seven stacked diagrams from typed input through evidence preparation to report,
   plus domain changes and deployment. Open locally in a browser; no external assets.
2. [Architecture contract](plans/ARCHITECTURE.md) — components/locations, text-only
   intake, domain profiles, evidence pack, target architecture and dependencies.
3. [Output structure](plans/OUTPUT_REPORT_STRUCTURE.md) — agreed brief sections.
4. Implementation detail: [ingestion/contracts](plans/INGESTION_PLAN.md), then
   [case operations](plans/OPERATIONS_PLAN.md). These are plans, not working code.

## Focused references

| Topic | Read |
| --- | --- |
| Challenge and requirements | [Brief](challenge/CHALLENGE_BRIEF.md), [requirements](challenge/PRODUCT_REQUIREMENTS.md) |
| Pilot and quality gates | [Pilot scope](challenge/PILOT_SCOPE.md), [evaluation](challenge/EVALUATION.md), [cases](challenge/WORKFLOWS_AND_CASES.md) |
| Technology choices | [Technical handoff](plans/TECHNICAL_OPTIONS.md) |
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
speakers' names/authority unverified. **U1–U5:** user instructions recorded in
sources. **P1:** dated historical preparation. Label requirements, stakeholder
clarifications, user decisions, proposals, measured results and unknowns.

Keep source snapshots, original transcripts/material and timestamped evidence
intact. Planning prose is concise; schema/index details remain in the ingestion
contract, and evaluation/source history retain necessary audit detail. Update
the visual and its owning focused document together when architecture changes.
