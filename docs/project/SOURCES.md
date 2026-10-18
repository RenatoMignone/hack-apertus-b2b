# Sources, provenance and known conflicts

**Documentation snapshot: 18 October 2026.** Local artifacts and the user's
instructions are the basis of this knowledge pack. The complete Notion page
text was supplied by the user as N1 after retrieval difficulties. Linked external
resources are references, not proof of independent live verification.

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
| U1 | User's tasks in this session, 18 Oct 2026 | Chosen track; active submission repository; read-only old repository; docs-only scope, root AGENTS router, direct one-commit push, and later Notion-context update | Authorizes documentation commits/pushes; not application implementation or final hackathon submission |
| U2 | User's open-question answers in this session, 18 Oct 2026 | No official UniBE inventory; robots-allowed public collection; agent-delegated medical focus and evaluation design; English-first with DE/FR/IT desirable; Bern healthcare expansion; confirmed export; partner examples available | Examples, endpoint/deployment details and branding assets not delivered; no historical-case corpus confirmed; no redistribution grant |
| U3 | User's later material delivery, 18 Oct 2026; [inspection inventory](../provided_material/README.md) | Best-effort UniBE workbook with 42 actual entries, supplied PowerPoint template and English agency logo | Supersedes missing inventory/branding delivery status in U2; Notes count 71 conflicts with data rows; no sample cases/gold labels or endpoint details supplied |
| U4 | User's architecture and information-handoff request, plus revision/follow-up instructions, 18 Oct 2026 | Initial Apertus 8B/70B + BGE-M3 + Weaviate + BGE reranker + LangGraph design; editable conversational results and agent questions | Starting architecture to validate, not measured superiority, access credentials or implementation authorization |
| U5 | User's visual architecture, manual input and domain-independence request, 18 Oct 2026 | Typed permitted keywords/context/operator knowledge; private PDFs outside app; future attachment extension; unchanged report sections; stacked HTML reference; concise docs and explicit deployment/dependency accounting | Documentation authorization; future confidential ingestion requires revised permission/handling; deployment target remains untested |
| U6 | User's data-layer discussion/refinement and request for build specs plus AGENTS update, 18 Oct 2026 | PostgreSQL + pgvector instead of Weaviate/SQLite; LangGraph persistence; self-hosted Langfuse; named model roles/candidates, taxonomy-assisted hybrid retrieval, versioned cases/evidence; exact model/tokenizer sources deliberately deferred | Authorizes focused technical documentation, not application implementation, provisioning or measured performance claims; D09/D10 supersede older storage choices |
| U7 | User's pasted team discussion 00:01–02:19 and accompanying source-structure instructions, 18 Oct 2026 | Separate frontend/backend communicating through HTTP; modular single-purpose backend components with local docs; directory-only scaffold and `.gitkeep` for empty folders; retrieval → ReportEvidencePack before report output | Explicitly no source code files or frontend implementation now; framework/scraper and detailed processing on both sides of the pack remain undecided. Draft API route/projection details are proposals, not user-selected exact schemas |
| U9 | User's frontend ownership, parallel-feature docs and provider/embedding handoff, 18 Oct 2026 | Frontend changes restored; Keera base URL/four aliases/tool restrictions; env placeholder; report all remaining questions; compare local/HF EmbeddingGemma 2 | Team key not supplied; $10/user credits are user-reported, eligibility unverified; local embedding remains recommendation |
| B1 | [Challenge text captured locally](../challenge/CHALLENGE_BRIEF.md), supplied by user | Objective, sources, models, expected fields, metrics, ethics and infrastructure boundaries | Linked Notion page not independently retrieved; capture is based on pasted text |
| N1 | [Complete Notion page text supplied by user](../sources/NOTION_CHALLENGE_2026-10-18.md), 18 Oct 2026 | Confirms B1; domain Research & Innovation; exact supporting filenames; template/logo use only for this challenge | User-supplied page capture, not independent live verification; no attachment bytes/download URLs or workbook/branding inspection |
| M1 | Root [README.md](../../README.md), local template at baseline commit `e1a8246` | Required layout, environment names, deliverables, report/video limits, six 0–5 jury dimensions | Contains unfilled project/team/challenge placeholders; remote template ancestry/visibility not checked |
| M2 | Root [technical_report.md](../../technical_report.md), same baseline | Mandatory target architecture, Apertus/data/limitations/reproducibility sections, report license label | Contains no actual architecture, results or evidence yet |
| M3 | Root [LICENSE](../../LICENSE) and [.gitignore](../../.gitignore) | Apache-2.0 code template; existing secret/model-weight exclusion patterns | Not a license grant for institutional page content or recordings; ignore patterns do not guarantee clean publication |
| T01 | [Opening/pitches transcript](../recordings/WhatsApp%20Audio%202026-10-18%20at%2010.56.37.mp4.txt) | Primary user/problem; initial medical scope; later general event remarks | Also contains two other challenges; starts mid-pitch; audio not available |
| T02 | [Early navigator Q&A transcript](../recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.04.mp4.txt) | Workflow, expertise types, semantic needs, privacy, no-match behavior and technical options | Includes participant suggestions, static/noise and team-allocation chatter |
| T03 | [Navigator workshop transcript](../recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.21.mp4.txt) | Teaser workflow, business volume, relevance review, sources, boundaries and evaluation discussion | No assets, sample documents or labeled data attached; speaker identities unverified |
| T04 | [Follow-up transcript](../recordings/WhatsApp%20Audio%202026-10-18%20at%2011.04.13.mp4.txt) | Generic investor-oriented material and the terminology/location gap | Short, ends mid-sentence; sharing-channel remarks are ambiguous |
| T05 | [Additional follow-up transcript](../recordings/bern-navigator-followup-2026-10-18.txt), supplied as pasted-text attachment | Public-only operator input, terminology bridge, iterative instructions, concise research-specific presentation and configurable cross-field structure | Speaker identity/authority and original recording date unverified; not research-corpus evidence or publication consent |
| P1 | Historical sibling `hack-apertus-liebefeld/docs/`: `EVENT_BRIEF.md`, `SUBMISSION.md`, `EVALUATION.md`, `SOURCES.md`, `CONTEXT.md`, `OPERATIONS.md`, `CHALLENGES.md`, `TEAM_WORKFLOW.md`, `PEOPLE.md`, `DECISIONS.md`, `OPEN_QUESTIONS.md` | Dated event timeline; participant-supplied Sprintd delivery instructions; older Finals-slide summary and inference-key announcement | Read only; not copied wholesale. Most claims checked 17 Oct; several pending/pre-event assumptions are now superseded. Original messages/slide images are not in this submission repository |

All five transcripts were read completely. Their immutable IDs, last timestamps
and original hashes are in [recordings/README.md](../recordings/README.md). Derived
findings E01–E30 in [RECORDING_INSIGHTS.md](../recordings/RECORDING_INSIGHTS.md) link to original
files and give recording-relative time ranges. No original audio was accessed.

The later T05 text was also read completely and preserved byte-for-byte with a
hash in the recording inventory. E27–E30 record its timestamped implications.
Its public-only company-input statements do not authorize private one-pagers.

The data discussion transcript at local `docs/recordings/data-discussion.ogg.txt`
was read in full (00:00–16:19). It is team design debate, not an organizer mandate
or expertise evidence. It was untracked at intake and is left unchanged; this
documentation update does not automatically add/publish that raw transcript.
The subsequent chat corrections and user-selected stack are recorded as U6.

Earlier technical planning examined Weaviate/BGE-M3; those active choices are
superseded by U6. Current interfaces checked on 18 October 2026 include pgvector,
PostgreSQL text search, LangGraph persistence and Langfuse integration/self-hosting. See
[INGESTION_PLAN.md](../plans/INGESTION_PLAN.md#87-technical-references-checked-18-october-2026)
and [data-layer build references](../data/BUILD_AND_OPERATIONS.md#technical-references-and-deferred-work)
for direct links and capability limits. These checks establish documented
interfaces, not actual endpoint access, corpus quality or deployment success.

## External references and verification status

| Resource | Purpose | Status in this pass, 18 Oct 2026 |
| --- | --- | --- |
| [Public challenge page](https://hackapertus.notion.site/bern-economic-development-agency) | Additional challenge reference and named supporting materials | Direct retrieval hit a Cloudflare challenge; reader proxy returned a partial page. User then supplied the complete text, preserved as N1 and used for the update. Attachments not downloaded |
| [Selected challenge on Notion](https://app.notion.com/p/hackapertus/Bern-Economic-Development-Agency-fe5b4fec112a833daf9401a4771a7c12?source=copy_link) | Canonical challenge guide reference supplied by user | Retrieval inaccessible through web tool; use B1, not a claim of live verification |
| [Official local event page](https://hackapertus.ch/regions/bern-liebefeld) | Event timeline and location | Two retrieval attempts timed out; recorded schedule is inherited from P1's 17 Oct snapshot |
| [Sprintd submission guide](https://app.sprintd.org/events/hack-apertus-liebefeld/submit/guide) | Current submission form/packaging | Inaccessible through web tool; P1's participant-supplied instructions remain dated context |
| [HackApertus/liebefeld](https://github.com/HackApertus/liebefeld) | Historical dedicated template reference | Retrieval failed; actual local M1/M2 used instead; old 17 Oct 404 is not asserted to be current |
| [Terms & Conditions](https://hackapertus.ch/terms-and-conditions) | Event compliance/Open Commons wording | Request returned no extractable text; current §6 and legal interpretation not verified |
| [Resources & Tools](https://hackapertus.notion.site/liebefeld-resources-tools) | Organizer resource reference in M1 | Not independently checked; missing inventory is not assumed to be hosted here |
| [Apertus v1.5 8B](https://huggingface.co/swiss-ai/Apertus-v1.5-8B), [70B](https://huggingface.co/swiss-ai/Apertus-v1.5-70B) | Model references from B1/M1 | Model cards inspected during planning; weights, endpoint access and actual behavior remain unverified |

## Conflicts and ambiguity resolved for this context pack

- **Current storage and tracing:** U6/D09 supersedes D07's Weaviate/BGE-M3 and
  earlier SQLite defaults. PostgreSQL full-text ranking is not BM25; pgvector
  requires actual embeddings, not tokenizer IDs. LangGraph checkpoints and
  Langfuse traces do not replace canonical evidence or durable case history.
- **Retrieval trust:** contextualization and reranking improve candidate selection
  but do not establish factual support or completeness outside the indexed corpus.
  U6/D10 retains post-retrieval claim checks and bounded gap handling.
- **Additional Notion source:** N1 agrees with B1 on all product, model,
  deployment, output, metric and ethics requirements. It adds the domain and
  names `unibe_sous_domaines_publics_etendus.xlsx`, `powerpoint_template.pptx`
  and `Logo_SF_BE_EN.png`. The latter two are explicitly challenge-only. This
  initially resolved their names/location reference; U3 later supplied actual
  files, with inspection recorded separately.
- **Two templates:** N1's PowerPoint supports challenge presentations; M1/M2
  still govern the repository and technical report. The asset listing does not
  change report limits. The user's later task separately selected automatic
  teaser export for the implementation plan.
- **Inventory chronology:** B1 referred to an inventory; U2 said no official
  inventory existed; U3 then supplied a workbook. Use the received best-effort
  discovery map and extend it. Do not describe it as authoritative DNS coverage
  or continue waiting for a missing file. Preserve the original brief/answers
  as historical evidence; U3 resolves current file availability.
- **Selected pilot and evaluation:** user-delegated decisions and first-party
  page observations are recorded with direct links in
  [PILOT_SCOPE.md](../challenge/PILOT_SCOPE.md). ARTORG research, DBMR Bally Lab, DCB research
  and its 10 April 2026 announcement were inspected via web retrieval on
  18 October. These are discovery observations, not a completed crawl or
  robots/terms review. DCB's research page was found via navigation at
  `/en/projects/`; a guessed `/en/research/` retrieval failed and is not a seed.

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

## U8 / D16 — final pipeline and data alignment, 18 October 2026

User approved the implementation plan after choosing: docs/data only; new-source
flag-and-allow; reason-card review; clarification only when blocking; connected
and offline modes; PDF first with PowerPoint later. This supersedes older
“mapping/scraper undecided” statements for case-time research. Self-hosted
Crawl4AI is selected; exact model artifacts, search provider and HTTP/auth
integration remain future inputs. See [processing](../plans/REPORT_PROCESSING_BOUNDARIES.md),
[web research and dated primary sources](../data/WEB_RESEARCH.md), and
[storage additions](../data/CASE_PIPELINE_STORAGE.md). No live execution or
performance result is established by this decision. No commit/push is authorized.

## U9 provider/embedding research, 18 October 2026

- User supplies `https://gateway.keera.ch/api/v1` and gateway aliases; Keera
  `/api/v1/models` returned 401 without authorization. `/docs` and `/openapi.json`
  serve control-panel HTML; `/api/v1/openapi.json` returned 404. No authenticated
  request, model-output claim, or private credential was obtained.
- [CSCS API](https://docs.cscs.ch/services/inference/api/) documents bearer-auth
  chat/model conventions and no-tool thinking variants. Direct CSCS names/keys
  differ from the supplied Keera mapping; do not substitute them automatically.
- [Google model card](https://huggingface.co/google/embeddinggemma-2) and
  [developer guide](https://developers.googleblog.com/embeddinggemma-2-the-developer-guide/)
  establish the distinct EmbeddingGemma 2 artifact and configurable text-only use.
- [HF pricing](https://huggingface.co/docs/inference-endpoints/support/pricing),
  [credit rules](https://huggingface.co/docs/inference-providers/pricing) and
  [autoscaling](https://huggingface.co/docs/inference-endpoints/guides/autoscaling)
  support the deployment comparison; prices are dated examples, not team quotes
  or evidence that this team's credits cover dedicated hosting.

See [provider settings](../data/INFERENCE_CONFIGURATION.md),
[embedding comparison](../data/EMBEDDING_DEPLOYMENT.md),
[module routing](../plans/MODULE_HANDOFFS.md) and
[active unresolved items](OPEN_QUESTIONS.md).

## U10 — schema finalization request, 18 October 2026

User asks to finalize tables/fields for the agreed scope, remove useless structures
and give the corpus/hybrid-RAG teammate an unambiguous schema. D18 records the
implementation decision; runtime metadata and generated reference own exact fields.
No shared-host migration or push is inferred from this request.

## U11 — three backend contributors and exclusive agent prompts

18 October 2026: user requests push/cleanup and three mutually exclusive backend
implementation prompts with standardized interfaces. One contributor owns
ingestion/database/graph-supported retrieval/embedding; two own the rest, with
frontend excluded. User asks why 8B rather than 70B (referring to it as 7B).
D19 records boundaries and an unmeasured 70B-first comparison recommendation.
