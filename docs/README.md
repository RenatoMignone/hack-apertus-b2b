# Project context and documentation

**Snapshot: 18 October 2026. Status: discovery documented; implementation not started.**
The chosen challenge is the Bern Economic Development Agency's **Research &
Expertise Navigator**. It should help a non-specialist business developer turn
ordinary-language company needs into verifiable matches with Bern's life-science
expertise, then select evidence for a company-facing pitch.

This directory adds working context to the existing submission template. Root
[README.md](../README.md) and [technical_report.md](../technical_report.md) remain
the organizer's submission documents; their placeholders have deliberately not
been filled with unbuilt features or unmeasured results.

## Read according to the task

For implementation planning, start with the paired
[ingestion, taxonomy and memory plan](plans/INGESTION_PLAN.md) and
[case operations plan](plans/OPERATIONS_PLAN.md). They define the user-requested
two-phase boundary and shared contracts. Their implementation choices remain
proposals; the earlier collection-only spec is a subordinate technical reference.
The [selected pilot scope](challenge/PILOT_SCOPE.md) records diabetes technology, verified
discovery seeds, English-first language policy, delegated evaluation rules and
the user's latest answers. The [partner-material inventory](provided_material/README.md)
records the supplied discovery workbook, PowerPoint template and English logo,
including the workbook's count discrepancy and asset handling requirements.
The current ingestion plan details the initial model/search stack and the
payloads passed between stages. The operations plan includes conversational
report revisions, agent follow-up questions and resumable case state.

| Document | Purpose |
| --- | --- |
| [CHALLENGE_BRIEF.md](challenge/CHALLENGE_BRIEF.md) | Faithful capture of the selected track supplied by the user |
| [Notion source snapshot](sources/NOTION_CHALLENGE_2026-10-18.md) | Complete user-supplied page text, supporting filenames and challenge-only branding restriction |
| [RECORDING_INSIGHTS.md](recordings/RECORDING_INSIGHTS.md) | Timestamped evidence from all five supplied transcripts; interpretation and authority caveats |
| [PRODUCT_REQUIREMENTS.md](challenge/PRODUCT_REQUIREMENTS.md) | Needs, scope, required outputs, constraints and acceptance conditions |
| [WORKFLOWS_AND_CASES.md](challenge/WORKFLOWS_AND_CASES.md) | Current workflow, intended assisted workflow, concrete cases and failure behavior |
| [OUTPUT_REPORT_STRUCTURE.md](plans/OUTPUT_REPORT_STRUCTURE.md) | Proposed Bern opportunity brief structure, match cards, priorities and optional extensions; not implemented behavior |
| [DATA_AND_PROVENANCE.md](data/DATA_AND_PROVENANCE.md) | Source inventory status, collection boundaries and proposed evidence/data contracts |
| [TECHNICAL_OPTIONS.md](plans/TECHNICAL_OPTIONS.md) | Initial architecture to validate and implementation alternatives |
| [EVALUATION.md](challenge/EVALUATION.md) | Challenge metrics, proposed pilot protocol and evidence needed for judging |
| [EVENT_AND_SUBMISSION.md](project/EVENT_AND_SUBMISSION.md) | Template rules, delivery checklist, historical event facts and unresolved submission differences |
| [DECISIONS_AND_OPEN_QUESTIONS.md](project/DECISIONS_AND_OPEN_QUESTIONS.md) | Confirmed choices, unresolved dependencies and next useful work |
| [SOURCES.md](project/SOURCES.md) | Evidence hierarchy, local and external sources, verification limits |
| [recordings/README.md](recordings/README.md) | Original transcript inventory, IDs, hashes and handling rules |

For a short onboarding, read [../AGENTS.md](../AGENTS.md), the challenge brief,
requirements, and decisions/questions. Read the recording insights when you need
the reasoning behind a requirement; use the original transcript to verify it.

## Directory map

- `challenge/`: brief, requirements, workflows, pilot scope and evaluation.
- `plans/`: ingestion/memory, operations/dialogue, technical options and report structure.
- `data/`: provenance contract and detailed collection specification/configuration.
- `project/`: decisions, sources, event and submission context.
- `recordings/`: original transcripts, inventory and derived recording insights.
- `sources/`: preserved user-supplied source snapshots.
- `provided_material/`: original partner workbook, presentation template and logo.

## Evidence labels

- **B1 / requirement:** the track brief pasted by the user, captured locally.
- **N1 / requirement:** complete Notion page text subsequently pasted by the
  user; confirms B1 and adds named supporting files and branding-use limits.
- **M1 / M2 / requirement:** this repository's README / technical-report template.
- **T01–T05 / stakeholder clarification:** supplied transcriptions; see the
  evidence entries E01–E30 in recording insights. No original audio was supplied.
- **P1 / historical context:** old preparation notes, summarized read-only;
  dates and authority caveats remain attached.
- **Proposal:** a working interpretation or design suggestion, requiring a team
  decision before it is treated as a selected solution.
- **Unknown:** unavailable or unverified; never fill it with plausible facts.

No crawler, application, benchmark, dataset of verified experts, generated PDF
or deployment has been created in this documentation pass. A partner-supplied
best-effort UniBE discovery workbook is now present: use its actual rows as the
initial map and extend them under robots rules. It is not exhaustive DNS coverage.

The supplied template and logo are restricted by N1 to use for this challenge.

## Important distinctions

- The **search prototype** is the track deliverable. A **company teaser PDF** is
  the stakeholder's downstream workflow. The **technical-report PDF** is a
  separate hackathon submission artifact with its own page limit.
- Medical focus can be narrowed for feasibility, while still demonstrating all
  three required source families and documenting the coverage boundary.
- Search results may be imperfect; their factual claims must remain supported.
  The stakeholder's willingness to review relevance does not relax traceability.
- The latest local template supersedes old assumptions that the challenge and
  template are still pending. Historical delivery additions remain labeled
  until the current submission form is checked.
