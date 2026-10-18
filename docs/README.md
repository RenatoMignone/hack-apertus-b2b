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

| Document | Purpose |
| --- | --- |
| [CHALLENGE_BRIEF.md](CHALLENGE_BRIEF.md) | Faithful capture of the selected track supplied by the user |
| [RECORDING_INSIGHTS.md](RECORDING_INSIGHTS.md) | Timestamped evidence from all four supplied transcripts; interpretation and authority caveats |
| [PRODUCT_REQUIREMENTS.md](PRODUCT_REQUIREMENTS.md) | Needs, scope, required outputs, constraints and acceptance conditions |
| [WORKFLOWS_AND_CASES.md](WORKFLOWS_AND_CASES.md) | Current workflow, intended assisted workflow, concrete cases and failure behavior |
| [DATA_AND_PROVENANCE.md](DATA_AND_PROVENANCE.md) | Source inventory status, collection boundaries and proposed evidence/data contracts |
| [TECHNICAL_OPTIONS.md](TECHNICAL_OPTIONS.md) | Architecture alternatives and implementation handoff; no stack selected |
| [EVALUATION.md](EVALUATION.md) | Challenge metrics, proposed pilot protocol and evidence needed for judging |
| [EVENT_AND_SUBMISSION.md](EVENT_AND_SUBMISSION.md) | Template rules, delivery checklist, historical event facts and unresolved submission differences |
| [DECISIONS_AND_OPEN_QUESTIONS.md](DECISIONS_AND_OPEN_QUESTIONS.md) | Confirmed choices, unresolved dependencies and next useful work |
| [SOURCES.md](SOURCES.md) | Evidence hierarchy, local and external sources, verification limits |
| [recordings/README.md](recordings/README.md) | Original transcript inventory, IDs, hashes and handling rules |

For a short onboarding, read [../AGENTS.md](../AGENTS.md), the challenge brief,
requirements, and decisions/questions. Read the recording insights when you need
the reasoning behind a requirement; use the original transcript to verify it.

## Evidence labels

- **B1 / requirement:** the track brief pasted by the user, captured locally.
- **M1 / M2 / requirement:** this repository's README / technical-report template.
- **T01–T04 / stakeholder clarification:** supplied transcriptions; see the
  evidence entries E01–E26 in recording insights. No original audio was supplied.
- **P1 / historical context:** old preparation notes, summarized read-only;
  dates and authority caveats remain attached.
- **Proposal:** a working interpretation or design suggestion, requiring a team
  decision before it is treated as a selected solution.
- **Unknown:** unavailable or unverified; never fill it with plausible facts.

No crawler, application, benchmark, dataset of verified experts, generated PDF
or deployment has been created in this documentation pass. The UniBE subdomain
inventory mentioned in the brief is **not present** among the supplied files.

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
