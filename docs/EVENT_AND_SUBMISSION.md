# Event context and template compliance

**Snapshot: 18 October 2026.** Sources: local template README (**M1**), local
technical-report template (**M2**), user-supplied challenge (**B1**), transcripts
and historical preparation notes (**P1**). See [SOURCES.md](SOURCES.md).

## Current local template is the working baseline

The following files and directory must keep their names and positions:

| Path | Template role |
| --- | --- |
| [../README.md](../README.md) | Challenge description and submission requirements |
| [../technical_report.md](../technical_report.md) | Architecture, Apertus use, data, limitations and reproducibility |
| [../LICENSE](../LICENSE) | Apache-2.0 |
| `src/` | Project code |

Additional working context lives in `docs/`; this pass adds a root `AGENTS.md`
router without moving or renaming the template. M2 itself points to `docs/` for
architecture diagrams. The root placeholders remain unchanged until the team
has actual project details and evidence to report.

M1 requires the repository to originate from the template, become public for
submission, and run end-to-end when judges try it. Local files do not prove the
remote repository's template ancestry or visibility; those checks remain open.
The current remote is `https://github.com/Spaghetti-Overflow/hack-apertus-submission`.
No publishing, remote configuration or commits were performed in this pass.

Use the environment variables **`LLM_NAME`, `LLM_BASE_URL`, `LLM_API_KEY`**.
Provide running instructions in the technical report. The local template does
not prescribe `make run`, a Dockerfile, old online track folders or a stack.

## Deliverables recorded in the local template

- Public template-based **Git repository URL**, required files, working
  end-to-end prototype and T&C compliance.
- Updated **`technical_report.md`**, plus a root **`TeamName_Report.pdf`** once
  the actual team name is confirmed. M1 limit: **6 pages excluding references**.
- **Demo video URL, at most 2 minutes**, also entered in M2's top **Demo** field.
- Apertus **v1.5** model family.

M2's sections are Summary, Architecture, Use of Apertus, Data, Limitations,
Reproducibility and References, with a report license label of CC-BY-4.0.
Under Architecture, the **mandatory target architecture** section asks which of
these targets applies and how:

- on-premise, on the organization's own infrastructure/administration;
- air-gapped, without external network at runtime;
- sovereign Swiss cloud, operated in Switzerland under Swiss jurisdiction and
  with Swiss data residency.

For this track, also apply B1's stricter infrastructure boundary: development
and deployment remain **outside cantonal ICT and internal networks**. A generic
on-premise template option does not authorize use of cantonal infrastructure.
List build-time and runtime dependencies separately and distinguish proposed
deployment from actually tested deployment.

M1 lists six main-jury dimensions, each scored **0–5**: purposeful use of AI;
technical rigour; value/cost/scalability; sovereign deployability; implementation
feasibility; pitch/presentation. No weights are supplied. The selected challenge
lists the first five; both sources should be represented in final materials.

## Historical delivery instructions requiring current confirmation

P1 summarizes participant-supplied Sprintd instructions from 17 October:
a public repository, <=2-minute video and a **ZIP containing exactly two PDFs**,
one **pitch deck of at most 10 slides** and one **technical report of at most
6 pages**. The signed-in
[submission guide](https://app.sprintd.org/events/hack-apertus-liebefeld/submit/guide)
was not accessible in this documentation pass.

| Difference | Current treatment |
| --- | --- |
| ZIP and pitch PDF appear in P1, not the local README | Retain as a historical delivery item to verify in the current form; absence from the template is not proof it was removed |
| M1 excludes references from the report limit; P1 does not specify that exclusion | Follow M1 for template drafting; confirm the form's page-count interpretation before final export |
| Old notes say template/challenge pending | Superseded: user selected this challenge and supplied an actual submission repository/template |
| Old slide notes say no numeric scale visible | That observation remains true of the described slide; the actual M1 now explicitly supplies a 0–5 scale |
| Live pitch duration | Unknown; the two-minute video cap does not define it |

Do not copy old online-phase track layouts or requirements. Treat later verified
organizer instructions as updates, with source/date attached.

## Event timeline useful for delivery

P1 records the Liebefeld event as **18–19 October 2026**, at WORKSPACE & MORE,
Waldeggstrasse 34, 3097 Liebefeld. Its organizer-page snapshot, checked 17 October,
records the following **Monday 19 October, Europe/Zurich (CEST, UTC+02:00)** times:

| Milestone | Recorded time |
| --- | --- |
| Final submission deadline | **14:30** |
| Partner pitches | 15:00–16:45 |
| Public doors | 17:00 |
| Top-six finals | 18:30–19:10 |
| Awards/closing | 19:45–20:00 |

The [event page](https://hackapertus.ch/regions/bern-liebefeld) could not be fetched
successfully on 18 October, so these are **carried-forward dated context**, not
a fresh schedule verification. Confirm live changes with organizers. T01
08:21–08:52 separately describes two finalist teams per track and three awards.

P1 also records an organizer statement that CSCS inference keys would be provided
after team formation. No actual endpoint, credentials, quotas or current access
has been supplied here. No local model-download requirement is inferred.

## Delivery checklist for later implementation work

- [ ] Preserve root template paths and complete project/team fields accurately.
- [ ] Demonstrate all three source families and all core challenge requirements;
  state coverage limits and actual quality evidence.
- [ ] Document exact model/setup, non-secret configuration, reproducible run
  instructions, costs/assumptions and chosen deployment boundary.
- [ ] Check data/recording/logo rights and public artifact contents; exclude
  secrets and private/non-redistributable material.
- [ ] Confirm template ancestry, public repository access and a fresh end-to-end run.
- [ ] Export and verify the root report PDF within the applicable page limit.
- [ ] Record a <=2-minute accessible demo; place the URL in the report.
- [ ] Check the current submission form for the ZIP/pitch PDF and final page rules.
- [ ] Verify actual pitch/Q&A duration and submission cutoff.
- [ ] Submit through the team's official flow and retain confirmation.

These boxes are intentionally open; documentation is not submission completion.
