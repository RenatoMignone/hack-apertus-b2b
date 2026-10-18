# Decisions, unknowns and next work

**Updated: 18 October 2026.** This records actual user choices and known gaps.
Proposed designs in other docs are not team decisions or completed work.

## Confirmed decisions

| ID | Decision | Source and implication |
| --- | --- | --- |
| D01 | Select Bern Economic Development Agency — Research & Expertise Navigator | User's current task; supersedes the historical preparation state of “challenge not selected” |
| D02 | Use `hack-apertus-submission` as the active submission repository and strictly retain its template | User's current task; existing root template files remain in place |
| D03 | Use `hack-apertus-liebefeld` only as historical read-only context | User explicitly says not to touch the old repository; useful context has been summarized locally |
| D04 | Current work is documentation/context extraction and a root agent router | User's current task; no application or infrastructure implementation in this pass |
| D05 | Preserve supplied recordings and organize derived context under `docs/` | User supplied `docs/recordings`; originals stay unchanged and evidence is timestamped in derived documents |
| D06 | Incorporate the complete Notion page text supplied by the user | N1 agrees with B1; adds Research & Innovation domain, three supporting filenames and challenge-only template/logo use. Preserve the dated text snapshot; files themselves remain unavailable |

**Confirmed requirements, not team architecture choices:** medical/life-science
focus in Bern; UniBE/ARTORG/Diabetes Center Berne coverage; Apertus v1.5;
source-backed structured results; no confidential-plan ingestion; external,
self-contained deployment. See [PRODUCT_REQUIREMENTS.md](PRODUCT_REQUIREMENTS.md).

**Not selected:** product/team name or roster, medical subdomain, implementation
stack, retrieval strategy, ontology/graph technology, model size/endpoint,
deployment target, extra data sources, export implementation and UI design.
The Git remote organization is not evidence of a finalized team name.

## Open questions

These are a working backlog, **not a request for approval or a blocker to the
completed documentation pass**. Resolve them at the relevant next task; do not
ask again for facts already supplied.

| ID | Question | Who/source can resolve it | Why it matters / current handling |
| --- | --- | --- | --- |
| Q01 | Obtain and inspect `unibe_sous_domaines_publics_etendus.xlsx`; what are the exact official ARTORG/DCB seeds? | N1's Notion challenge supporting materials or team | Inventory filename/page reference resolved by N1; actual workbook/download URL, schema and entries remain unavailable; no seeds invented |
| Q02 | Which medical slice is feasible while demonstrating all three sources? | Team, with partner input if useful | Diabetes and oncology are examples, not selected directions |
| Q03 | Can the partner supply public/anonymized example needs and expected relevant experts/units? | Partner | No authentic sample brief or labeled answers supplied; synthetic prompts need checked real evidence |
| Q04 | How should the 80%-in-top-10 target aggregate across queries, and how should experts versus units count? | Partner/evaluation discussion | Report per-query and macro/micro results; keep entity types explicit until clarified |
| Q05 | What are the actual model endpoint, protocol, served model IDs, authentication, quotas and availability? | Official inference documentation / team-held access | No adapter assumptions or credentials recorded; use template environment names |
| Q06 | Which independent deployment mode will be demonstrated, and what hardware/resources are available? | Team and verified infrastructure docs | No claim of offline or Swiss-cloud operation yet; keep cantonal ICT excluded |
| Q07 | Which source languages and user/output languages should the prototype support? | Team/partner and actual source inventory | Multilingual scope is not explicitly specified; record languages rather than assume coverage |
| Q08 | Is automatic teaser export worth including? Obtain and inspect the listed presentation/branding files if needed | Team; N1's `powerpoint_template.pptx` and `Logo_SF_BE_EN.png` | Asset names and challenge-only use now confirmed in supplied page text; contents, colors/layout and export feature remain unverified/undecided |
| Q09 | Which additional Bern company/supplier sources, if any, should be included? | Team/partner; verified public source sites | Extension only; cannot replace core institutional coverage |
| Q10 | What may be retained/redistributed from public pages, transcripts, logos and contact information under current terms? | Current organizer terms, N1 and source rights holders where needed | N1 limits template/logo use to this challenge; no broader asset license or blanket redistribution/transcript-publication consent established |
| Q11 | Does the current submission form still require the exact two-PDF ZIP and <=10-slide pitch, and how does it count report references? | Signed-in Sprintd guide/current organizer instructions | Historical addition remains flagged; local template's report naming/limits recorded separately |
| Q12 | What are the live pitch/Q&A duration and latest delivery cutoff? | Current on-site organizer announcements | Historical cutoff is 19 Oct 14:30 CEST; two-minute limit is the video cap, not live pitch time |
| Q13 | Are remote template ancestry and public visibility correct, and what is the final team name? | Team's GitHub/submission account | Initial context was committed/pushed to `origin/main` as `ab3d534` at user request; ancestry, visibility and team name are not established by that push |
| Q14 | How extensive must collection/freshness be and what page/file types are feasible? | Actual inventory, team time budget and partner priorities | Coverage of an entire university is not claimed; a bounded pilot must expose omissions |

## Suggested next work after a new implementation task

First resolve source access/inventory and a feasible scope, then verify a small
set of expected matches. Use that evidence to choose the architecture and
Apertus role. Build the required end-to-end search flow before optional case
management, extra company sources or teaser export. The detailed handoff is in
[TECHNICAL_OPTIONS.md](TECHNICAL_OPTIONS.md).

For future documentation-only tasks, append new sources and timestamped findings,
resolve the relevant questions, and update this file without reopening completed
choices or filling unknowns with guesses.

## Future decision record

```text
ID / date:
Decision and scope:
Source or user instruction:
Alternatives/trade-off, only if material:
Evidence verified / checks run:
Remaining unknowns:
Documents and question IDs updated:
```

Use the actual event/local time zone for deadlines. Do not add an invented owner,
personal roster, completed benchmark or deployment to a decision record.
