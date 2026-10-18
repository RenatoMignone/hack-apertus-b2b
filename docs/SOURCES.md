# Sources, provenance and known conflicts

**Documentation snapshot: 18 October 2026.** Local artifacts and the user's
instructions are the basis of this knowledge pack. Linked external resources
are references, not proof that their current contents were retrieved.

## Evidence hierarchy

1. The user's current instructions define workspace, task and authorized scope.
2. Current local submission template and user-supplied selected challenge brief
   establish the working delivery/product requirements. Later verified organizer
   instructions can update them; retain date/source when resolving conflicts.
3. Timestamped stakeholder statements clarify needs and workflow. Speaker
   identity/authority is inferred from context, not authenticated.
4. Other workshop remarks inform technical options; participant questions are
   not confirmed requirements.
5. Historical preparation notes preserve dated context and caveats.
6. Proposed interpretations/architecture/checks stay labeled as proposals until
   chosen or tested.

Do not merge conflicting instructions silently. For example, conversational
“mostly” source references does not override B1's 100% traceability requirement.

## Local source registry

| ID | Source | Supports | Limitations |
| --- | --- | --- | --- |
| U1 | User's task in this session, 18 Oct 2026 | Chosen track; active submission repository; read-only old repository; docs-only scope and root AGENTS router | Not an implementation/hosting/publication request |
| B1 | [Challenge text captured locally](CHALLENGE_BRIEF.md), supplied by user | Objective, sources, models, expected fields, metrics, ethics and infrastructure boundaries | Linked Notion page not independently retrieved; capture is based on pasted text |
| M1 | Root [README.md](../README.md), local template at baseline commit `e1a8246` | Required layout, environment names, deliverables, report/video limits, six 0–5 jury dimensions | Contains unfilled project/team/challenge placeholders; remote template ancestry/visibility not checked |
| M2 | Root [technical_report.md](../technical_report.md), same baseline | Mandatory target architecture, Apertus/data/limitations/reproducibility sections, report license label | Contains no actual architecture, results or evidence yet |
| M3 | Root [LICENSE](../LICENSE) and [.gitignore](../.gitignore) | Apache-2.0 code template; existing secret/model-weight exclusion patterns | Not a license grant for institutional page content or recordings; ignore patterns do not guarantee clean publication |
| T01 | [Opening/pitches transcript](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.56.37.mp4.txt) | Primary user/problem; initial medical scope; later general event remarks | Also contains two other challenges; starts mid-pitch; audio not available |
| T02 | [Early navigator Q&A transcript](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.04.mp4.txt) | Workflow, expertise types, semantic needs, privacy, no-match behavior and technical options | Includes participant suggestions, static/noise and team-allocation chatter |
| T03 | [Navigator workshop transcript](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.21.mp4.txt) | Teaser workflow, business volume, relevance review, sources, boundaries and evaluation discussion | No assets, sample documents or labeled data attached; speaker identities unverified |
| T04 | [Follow-up transcript](recordings/WhatsApp%20Audio%202026-10-18%20at%2011.04.13.mp4.txt) | Generic investor-oriented material and the terminology/location gap | Short, ends mid-sentence; sharing-channel remarks are ambiguous |
| P1 | Historical sibling `hack-apertus-liebefeld/docs/`: `EVENT_BRIEF.md`, `SUBMISSION.md`, `EVALUATION.md`, `SOURCES.md`, `CONTEXT.md`, `OPERATIONS.md`, `CHALLENGES.md`, `TEAM_WORKFLOW.md`, `PEOPLE.md`, `DECISIONS.md`, `OPEN_QUESTIONS.md` | Dated event timeline; participant-supplied Sprintd delivery instructions; older Finals-slide summary and inference-key announcement | Read only; not copied wholesale. Most claims checked 17 Oct; several pending/pre-event assumptions are now superseded. Original messages/slide images are not in this submission repository |

All four transcripts were read completely. Their immutable IDs, last timestamps
and original hashes are in [recordings/README.md](recordings/README.md). Derived
findings E01–E26 in [RECORDING_INSIGHTS.md](RECORDING_INSIGHTS.md) link to original
files and give recording-relative time ranges. No original audio was accessed.

## External references and verification status

| Resource | Purpose | Status in this pass, 18 Oct 2026 |
| --- | --- | --- |
| [Selected challenge on Notion](https://app.notion.com/p/hackapertus/Bern-Economic-Development-Agency-fe5b4fec112a833daf9401a4771a7c12?source=copy_link) | Canonical challenge guide reference supplied by user | Retrieval inaccessible through web tool; use B1, not a claim of live verification |
| [Official local event page](https://hackapertus.ch/regions/bern-liebefeld) | Event timeline and location | Two retrieval attempts timed out; recorded schedule is inherited from P1's 17 Oct snapshot |
| [Sprintd submission guide](https://app.sprintd.org/events/hack-apertus-liebefeld/submit/guide) | Current submission form/packaging | Inaccessible through web tool; P1's participant-supplied instructions remain dated context |
| [HackApertus/liebefeld](https://github.com/HackApertus/liebefeld) | Historical dedicated template reference | Retrieval failed; actual local M1/M2 used instead; old 17 Oct 404 is not asserted to be current |
| [Terms & Conditions](https://hackapertus.ch/terms-and-conditions) | Event compliance/Open Commons wording | Request returned no extractable text; current §6 and legal interpretation not verified |
| [Resources & Tools](https://hackapertus.notion.site/liebefeld-resources-tools) | Organizer resource reference in M1 | Not independently checked; missing inventory is not assumed to be hosted here |
| [Apertus v1.5 8B](https://huggingface.co/swiss-ai/Apertus-v1.5-8B), [70B](https://huggingface.co/swiss-ai/Apertus-v1.5-70B) | Model references from B1/M1 | Links supplied locally; weights, model cards, endpoint availability and behavior not independently inspected |

## Conflicts and ambiguity resolved for this context pack

- **Track/template pending:** P1's older state is superseded by U1 and this
  repository's actual template. Future agents must not restart track selection.
- **Numeric scoring:** P1's photographed slide summary says no scale was shown;
  M1 explicitly says each of six main-jury dimensions is scored 0–5. Use M1's
  statement without inventing weights or a partner-stage formula.
- **Submission packaging:** M1 specifies repo, root report PDF and video. P1
  additionally describes a two-PDF ZIP and <=10-slide pitch. Keep the addition
  pending current form verification; do not assume omission means cancellation.
- **Page limits:** company teaser (typically 5–10 pages in T03), submission
  technical report (<=6 pages excluding references in M1), and historical pitch
  deck (<=10 slides in P1) are different artifacts.
- **No ready evaluation dataset:** workshop comments describe missing labels,
  not cancellation of B1's 80%-in-top-10 success target.
- **Public sources versus open licensing:** workshop “open source” wording does
  not clear redistribution of public-page text, personal details or recordings.
- **Scale and geography:** one medical field is allowed as a starting point;
  all three named source families and Bern relevance remain requirements.
- **No API:** no ready access API was provided in the discussion; this is not
  evidence that no institution has any public API.
- **Model combinations:** T01's OCR discussion belongs to another track. It does
  not add OCR/vision requirements or waive Apertus/deployment constraints here.

## Updating evidence

When new information arrives, record the source, date, exact relevant wording
or timestamp, verification method, affected requirement/question and whether it
supersedes an older statement. Update the focused doc and the decision/question
log together. Store only material appropriate for the repository; link restricted
sources without copying private messages, credentials or confidential plans.
