# Agent entry point

This is the active **Hack Apertus Liebefeld submission repository**, for the
**Bern Economic Development Agency — Research & Expertise Navigator** challenge.
Start with [docs/README.md](docs/README.md); load the additional documents relevant
to your task rather than reading the entire knowledge base every time.

## Current state and scope

- Challenge selected by the user on 18 October 2026. No implementation stack,
  architecture, medical subdomain, team roster or project name has been selected
  in the supplied material.
- Current authorized work is **documentation and agent context only**. Implement
  features when a subsequent user task authorizes them. Do not treat proposed
  designs or acceptance checks in these docs as implemented behavior.
- Work in this repository. The sibling `hack-apertus-liebefeld` is historical
  preparation context: **do not modify it**. Relevant context has been summarized
  here; routine work should not require reopening it.

## Task router

| Your task | Read |
| --- | --- |
| Understand the selected challenge | [Challenge brief](docs/CHALLENGE_BRIEF.md), [requirements](docs/PRODUCT_REQUIREMENTS.md) |
| Find the Notion supporting files or check branding restrictions | [Notion text snapshot](docs/sources/NOTION_CHALLENGE_2026-10-18.md), [data and provenance](docs/DATA_AND_PROVENANCE.md) |
| Understand stakeholder intent or check a recording claim | [Recording insights](docs/RECORDING_INSIGHTS.md), then the linked [original transcript](docs/recordings/README.md) |
| Design a user flow, result presentation or demo scenario | [Workflows and cases](docs/WORKFLOWS_AND_CASES.md), [requirements](docs/PRODUCT_REQUIREMENTS.md) |
| Plan crawling, extraction, entities or citations | [Data and provenance](docs/DATA_AND_PROVENANCE.md) |
| Choose architecture, retrieval or Apertus integration | [Technical options](docs/TECHNICAL_OPTIONS.md), [decisions and questions](docs/DECISIONS_AND_OPEN_QUESTIONS.md) |
| Evaluate quality, grounding or sovereign operation | [Evaluation](docs/EVALUATION.md), [data and provenance](docs/DATA_AND_PROVENANCE.md) |
| Prepare report, pitch, video or delivery | Root [README.md](README.md), [technical_report.md](technical_report.md), [event and submission](docs/EVENT_AND_SUBMISSION.md) |
| Resolve uncertainty or update context | [Sources](docs/SOURCES.md), [decisions and questions](docs/DECISIONS_AND_OPEN_QUESTIONS.md) |

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
   A narrower medical demonstration is permitted by the stakeholder, but has
   not been chosen and does not remove three-source coverage.
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

## Keeping context reliable

- Treat the user-supplied brief, complete Notion text (N1), and local template
  as the current baseline. N1 lists an XLSX inventory, a PowerPoint template
  and a PNG logo; actual files are not supplied. Use the template/logo only for
  this challenge and preserve the root submission template.
  Record later verified organizer clarifications with dates and provenance.
- Recording evidence is timestamped in `docs/RECORDING_INSIGHTS.md`. Speaker
  numbers are local to each file; names and formal authority are unverified.
  Participant questions and technical suggestions are not official mandates.
- Label statements **requirement**, **stakeholder clarification**, **proposal**,
  **decision**, **measured**, or **unknown**, as appropriate. Log actual decisions
  and resolved questions in `docs/DECISIONS_AND_OPEN_QUESTIONS.md`.
- Keep supplied transcripts unchanged. Cite the file and recording-relative time.
  Do not publish transcripts, source datasets or external messages automatically.
- Update the relevant focused document and its source references when new facts
  arrive. Keep this file a compact router, not a second requirements document.
- For documentation changes, check relative links, evidence references and
  template/transcript preservation. Do not claim application tests or results
  before an implementation exists.
