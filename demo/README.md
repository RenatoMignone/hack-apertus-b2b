# End-to-end demo case: HelioSense

This folder contains a **fictional case brief** for exercising the Navigator
application. It is case input, not source evidence. Do not import these files as
institutional pages, reviewed claims, corpus records, or MeSH assignments.

The report should retrieve and cite only real, currently available evidence from
the configured UniBE, ARTORG and Diabetes Center Berne corpus (and any explicitly
enabled, permitted case-time research). Names, roles, projects, capabilities,
contacts and services in the output must come from those linked sources. If the
corpus does not support a requested field, the correct demo result is a visible
gap—not a made-up value. The fictional company and its plans must remain labeled
as scenario input.

## Files

- `case-brief.md`: copy/paste this as the new case's initial message.
- `query-variants.json`: alternate phrasings for separate runs to compare
  terminology handling; each is synthetic input, not a gold label.
- `business-context.json`: optional hypothetical manual-plan values. Enter them
  only through the application's permitted-context controls, if enabled, and
  keep the fictional/simulation label in the case narrative.
- `run-checklist.md`: walkthrough from intake through reviewed report export and
  a compact acceptance checklist.

## Suggested run

For a frontend-independent demonstration, open the
[recorded retrieval proof of concept](../docs/proof-of-concept/README.md). It
contains a standalone PDF, the exact tested queries, ranked source records and
reproduction instructions. It demonstrates real passage retrieval and inspected
researcher mentions, not a validated expert-recall score or complete profiles.

Use the connected HTTP application, not mock/demo mode, for a real retrieval and
backend report run. Create one case from `case-brief.md`, wait for the run to
finish, inspect its source excerpts, keep or reject each reason, then approve and
export the reviewed PDF. Run each query variant as a separate case when comparing
wording. Do not enable own-case memory for this synthetic case.

The current source snapshot, coverage, model/provider outcomes, and actual
retrieved records determine what the report can demonstrate. This fixture does
not claim that any particular expert, unit, service or project will be found and
does not establish retrieval quality or the 80% success target.
