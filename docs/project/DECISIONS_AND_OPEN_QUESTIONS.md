# Decisions, unknowns and next work

## Live ingestion development — 18 October 2026

Eric authorized Renato and other users to work against ongoing ingestion without
a completed version or production release. `RUNTIME_CORPUS_MODE=live` captures
ready authorized public chunks per owned case. Captures remain stable through
retries/review/export; new research runs can include later ingestion. Publication
stays available for reviewed releases. Embedding compatibility, evidence support
and case isolation remain required. Migration `0008_live_corpus` and the narrow
`navigator_runtime` role implement this boundary. See
[live runtime](../data/LIVE_CORPUS_RUNTIME.md) and its
[verification/rollout status](../team/RUNTIME_ACCESS_STATUS.md).

**Updated: 18 October 2026.** This records actual user choices and known gaps.
This is a chronological record: older implementation/authorization statements
describe their original task, not the current development boundary.
[Current status](STATUS.md) and [active questions](OPEN_QUESTIONS.md) take precedence.

**Current routing:** [active questions](OPEN_QUESTIONS.md) is the authoritative
unresolved-design register; [module handoffs](../plans/MODULE_HANDOFFS.md) routes
feature work. Integration D20 supersedes the completed lane assignments. Limited
authenticated probes passed; quotas, immutable revisions and live deployment remain open.

## Confirmed decisions

**D15 / implemented database layer and shared host, 18 October:** the user
authorized the implementation plan after selecting one shared database on the
user's Windows/WSL2 computer. Four developers run their code locally and connect
through individual SSH accounts/tunnels. Docker Compose packages PostgreSQL 17
+ pgvector, shared MinIO and optional local Langfuse. Database ports bind
loopback. Python 3.12/Pydantic/SQLAlchemy Core/psycopg/Alembic implement the data
contracts. See [deployment and measured checks](../data/DEPLOYMENT.md).
Keera endpoint/model aliases are now supplied; actual team keys, authenticated
behavior, immutable revisions and complete report workflows remain pending.
The React frontend exists on mocks and is separately owned. This supersedes the earlier
scaffold-only authorization for this database-layer scope.

| ID | Decision | Source and implication |
| --- | --- | --- |
| D01 | Select Bern Economic Development Agency — Research & Expertise Navigator | User's current task; supersedes the historical preparation state of “challenge not selected” |
| D02 | Use `hack-apertus-submission` as the active submission repository and strictly retain its template | User's current task; existing root template files remain in place |
| D03 | Use `hack-apertus-liebefeld` only as historical read-only context | User explicitly says not to touch the old repository; useful context has been summarized locally |
| D04 | Current work is documentation/context extraction and a root agent router | User's current task; no application or infrastructure implementation in this pass |
| D05 | Preserve supplied recordings and organize derived context under `docs/` | User supplied `docs/recordings`; originals stay unchanged and evidence is timestamped in derived documents |
| D06 | Incorporate the complete Notion page text supplied by the user | N1 agrees with B1; adds Research & Innovation domain, three supporting filenames and challenge-only template/logo use. Preserve the dated text snapshot; the files are now inventoried under `provided_material/` |

**Confirmed requirements, not team architecture choices:** medical/life-science
focus in Bern; UniBE/ARTORG/Diabetes Center Berne coverage; Apertus v1.5;
source-backed structured results; no confidential-plan ingestion; external,
self-contained deployment. See [PRODUCT_REQUIREMENTS.md](../challenge/PRODUCT_REQUIREMENTS.md).

**Current input/architecture update (U5), 18 October:** the user confirms manually
typed keywords, context and operator knowledge after reading confidential
business plans/one-pagers outside the app. Those PDF uploads are a future disabled
extension requiring explicit permission and revised handling rules. The user
requires a domain-independent pipeline/RAG and selects the existing report
structure plus [stacked visual architecture reference](../architecture.html).
Sources/taxonomy/settings/evaluation are versioned profiles; indexes can be rebuilt.
The [architecture contract](../plans/ARCHITECTURE.md) proposes an air-gapped primary
runtime with connected build/collection and records alternatives/dependencies.
That target is a design proposal, not a hardware choice or tested deployment.

**Not selected:** product/team name or roster, frontend framework,
taxonomy contents/ontology mappings, actual model endpoints/revisions,
deployment target, extra data sources, export library and UI design.
The Git remote organization is not evidence of a finalized team name.

## Two-phase planning update — 18 October 2026

**Two-phase user decision:** define Phase 1 as source collection, taxonomy processing
and memory publication; define Phase 2 as the case workflow consuming that
memory. The user requested two implementation plans, now recorded in
[INGESTION_PLAN.md](../plans/INGESTION_PLAN.md) and [OPERATIONS_PLAN.md](../plans/OPERATIONS_PLAN.md).
This authorizes documentation planning, not implementation in this pass.

**User-requested operational scope:** manual permitted text/context intake, future
disabled attachment adapter, contextual topic interpretation, company background research,
generic Bern and company-specific matching, previous-case retrieval, explained
scores/confidence, potential economic benefits and PowerPoint output. This
selects presentation export for the operational plan (Q08); the later partner
material supplies the logo/template. Historical-case data and taxonomy contents are not yet
supplied. Confidential-plan boundaries still apply.

**Shared design:** the plans share versioned documents, evidence, claims, concepts,
entities, cases and memory snapshots. D09 below supersedes both the earlier
SQLite-search proposal and D07's Weaviate/BGE-M3 storage choices. Endpoint support
for tokenization, modalities, quotas and the actual served model remains Q05.

## Historical architecture and UI decisions

**D07 / historical starting architecture, superseded by D09 for storage/embeddings:** validate Apertus
v1.5 8B for classification, 70B for difficult classification and optional
synthesis, BGE-M3 dense embeddings, Weaviate hybrid search, BGE-reranker-v2-m3
and LangGraph orchestration. This selects a plan to validate, not a measured
best-model claim or deployment. The ingestion plan specifies payloads and
storage ownership; actual endpoint/hardware details remain deferred.

**D08 / user requirements, 18 October:** accept conversational report revisions
and refocusing instructions, and let the agent ask follow-up questions. Keep
versioned case intent, answers, result revisions, citations and export lineage;
pause dependent work for required answers and resume the correct checkpoint.
The attached follow-up transcript is preserved as T05, with E27–E30 documenting
the public-input boundary, terminology gap and iterative refinement.

**D09 / current data architecture, U6, 18 October:** select PostgreSQL + pgvector
for canonical records, case state and independent lexical/vector retrieval;
LangGraph with PostgreSQL checkpoints; self-hosted Langfuse for execution tracking.
Artifact storage holds original/normalized files and exports. Framework databases
are separate from application tables; Langfuse adds ClickHouse, Redis/Valkey and
S3-compatible storage. No Weaviate or SQLite is an active default. Model roles are
Apertus v1.5 8B/optional 70B, EmbeddingGemma 2 embedding candidate and BGE reranking.
At U6, exact model/tokenizer sources/revisions/endpoints were deferred. U9 now
supplies Keera connection/aliases and the EmbeddingGemma 2 reference; revisions
and runtime validation remain open.

**D10 / retrieval and persistence contract, U6, 18 October:** preserve full intent;
use taxonomy for optional multi-label context/aliases; run lexical and vector
branches independently under reliable constraints, fuse ranks, rerank, then
validate claim support. Store versioned case evidence/reviews/exports separately
from shared snapshots. Reranking is not factual verification. No automatic corpus
updates from reports, user corrections or web discoveries. The focused
[data-layer specs](../data/DATA_LAYER.md) own physical schemas, search, cases,
tracing and build/restore gates; ingestion section 7 retains logical interfaces.
Current authorization at U6 was documentation and AGENTS routing, not implementation.

**D11 / source scaffold and HTTP boundary, U7, 18 October:** separate
`src/frontend/` and `src/backend/`; backend components have narrow responsibilities,
explicit contracts and folder-local guidance. HTTP is the frontend/backend
boundary. This update authorizes directories, READMEs and `.gitkeep` placeholders
only, superseding D04's docs-only scope for that limited purpose. No application
code, package setup or frontend internals. [Source structure](../plans/SOURCE_STRUCTURE.md)
owns the scaffold; [API handoff](../plans/FRONTEND_BACKEND_API.md) is a draft surface.
At U7, the retrieval → pack → report mapping and scraper choice were deferred.
U8 subsequently selected the [processing stages](../plans/REPORT_PROCESSING_BOUNDARIES.md)
and Crawl4AI for future case-time fetching; live adapters remain feature work.

**D12 / user decision, 18 October:** the user and agent build the **frontend only**,
on seeded mock data. Teammates build the backend. Stack: Vite + React + TypeScript
+ Tailwind in `src/frontend/`, bundled for offline use. Layout: brief in the centre
and agent chat on the right. Agent edits apply immediately, with highlighted
sections and a version history. Sources appear as inline citation chips, an
evidence drawer and a per-case source map. Workflow statuses: Draft, Researching,
In review, Pitch sent, Closed (visit / no interest), On hold. PowerPoint export is a
low-priority button. A global field/knowledge map is pitch-only, not part of the
operator's navigation. Contract and screens: [FRONTEND_PLAN.md](../plans/FRONTEND_PLAN.md).
Mock data uses synthetic companies and public page excerpts; no backend integration is claimed.
The UI's `NavigatorApi` still has to be mapped to the draft HTTP routes in
[FRONTEND_BACKEND_API.md](../plans/FRONTEND_BACKEND_API.md) (D11).

**D13 / user decision, 18 October (supersedes D12's layout details):** minimise text.
The output is a list of **reasons why Bern fits the company**, grouped by need. Each
reason is a headline, one cited sentence and its Bern entries; sources open on
click. The graph source map is replaced by a collapsible **"How I searched" Sankey**
at the bottom: message phrases → ontology terms → source entries, each entry
extracted from one URL. The 7-section brief in OUTPUT_REPORT_STRUCTURE.md stays a
content reference for backend/export, not the screen layout. See [FRONTEND_PLAN.md](../plans/FRONTEND_PLAN.md).

**D14 / user decision, 18 October:** a top navigation bar with three pages: **My desk**
(home cards: New case, My cases, Action items), **My cases** (a kanban board by
status, drag to move) and **Action items** (questions for agency colleagues, drafted
per case, marked Asked/Done). The case page opens with a short company description
from the operator's message, before the reasons.

**D15 / user decisions after a UX audit, 18 October:** board stages reduced to four
(To research, In review, Pitch sent, Closed with Visit / No interest outcome); *On
hold* becomes a flag. Cards move by drag or a ⋯ menu, with Undo. The case chat is
collapsible (remembered) and becomes an overlay drawer below 1100 px. Keep/Hide get
text labels. Case names stay auto-derived. Case-page content is unchanged; a jump bar,
compact version menu, toasts with Undo, keyboard focus, WCAG AA contrast and
per-browser demo persistence were added. Audit and rationale: the approved UX plan,
summarised in [FRONTEND_PLAN.md](../plans/FRONTEND_PLAN.md).

**D16 / user decision, 18 October (supersedes D14's page set):** remove *My desk* and
*Action items*. No recording asks for a dashboard or for tracking questions to
colleagues. Meetings, outreach and relationship follow-up are the agency's job and
outside the challenge (T03 11:04–12:09, 21:45–22:26; PRODUCT_REQUIREMENTS scope). The
app is now the cases board (home, `/`), the composer and the case page. The supported
part, "Gaps and next steps" (questions for the company, possible introductions with
availability not confirmed), moves into a *Next steps* block on the case page.

**D17 / user decision, 18 October:** the export produces two files from the items she
kept: a structured **PDF brief** with the supplied English agency logo, and an
editable **PowerPoint** built from the supplied partner template (its layouts,
master and theme; example slides removed). Both are generated client-side on the
`ui-polish` branch (`src/frontend/src/export/`) so they work with the mock and offline.
Open point for merging: `main` already has a backend ReportLab PDF renderer, with PPTX
listed there as later work. The team must choose one PDF path (backend renderer, or
this client-side brief) and whether PPTX stays client-side or moves to the backend.
Template and logo remain challenge-only (N1).

**18 October user answers (U2):** recorded below. The agent selected the delegated
medical slice and evaluation protocol in [PILOT_SCOPE.md](../challenge/PILOT_SCOPE.md).
Selected scope is diabetes technology; English outputs are required and DE/FR/IT
support desirable. A later partner workbook now supplies the initial discovery
inventory (best-effort, not authoritative DNS coverage). Public robots-allowed
collection is authorized within relevant scope. Endpoint and deployment inputs
will arrive before development; branding has now arrived. Partner example needs and
expected entities can be supplied; neither those examples nor historical cases
have been delivered. No application implementation is authorized by this update.

## Historical question IDs and current disposition

The previous Q01–Q18 list is retained by repository history. Its active unresolved
parts are now collected once in [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md), with O01–O27
and links back to old IDs. Do not re-open resolved choices because an older
historical paragraph says “pending.”

| Old IDs | Current disposition |
| --- | --- |
| Q01 | Workbook delivered; actual collection/freshness remains O13 |
| Q02,Q04 | Pilot and evaluation aggregation selected; real gold/results are O19 |
| Q03 | Partner examples and historical data not delivered: O19/O21 |
| Q05 | Keera endpoint/aliases supplied; key/limits/protocol verification O01–O03 |
| Q06,Q16 | Shared host/data implementation selected; deployment, hardware and retention O17/O18 |
| Q07 | English baseline selected; multilingual validation O23 |
| Q08 | Assets delivered; PDF first selected; renderer/PPTX implementation O15 |
| Q09 | Bern healthcare expansion policy selected; actual additions O24 |
| Q10–Q13 | Rights, delivery requirements and team/submission inputs O25–O27 |
| Q14 | Public websites/PDF priority selected; provider/collection freshness O12/O13 |
| Q15 | EmbeddingGemma 2 reference known; revisions/hosting/reranking O03–O06 |
| Q17 | Python data/React mock tooling selected; HTTP/auth/contracts O07–O09 |
| Q18 | Stages/DTOs/data implemented; live prompts, validators, graph and UI integration O10/O11/O14/O16/O20 |

## Suggested next work after a new implementation task

**Material update / U3, 18 October:** the user supplied three files under
`docs/provided_material/`: a best-effort UniBE discovery workbook, a PowerPoint
template and an English agency logo. [Inspection notes](../provided_material/README.md)
record contents, exact counts, discrepancies and SHA-256 hashes. Preserve these
originals. This resolves inventory-file and branding delivery, not partner
examples, gold labels, historical cases, taxonomy, inference or deployment inputs.

Use the selected diabetes-technology scope and verified discovery seeds, verify
the supplied Keera connection and obtain partner examples, and verify the
expected entities. Implement the paired plans with evidence and memory contracts
first, then the case workflow and PDF-first export (PowerPoint later). Extra sources
remain subject to the Bern healthcare rule. See [INGESTION_PLAN.md](../plans/INGESTION_PLAN.md),
[OPERATIONS_PLAN.md](../plans/OPERATIONS_PLAN.md) and [PILOT_SCOPE.md](../challenge/PILOT_SCOPE.md).

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

## U9 / D17 — independent modules, frontend ownership and Keera

18 October 2026: user requests agent-ready module routing, restores backend-agent
changes to the separately owned frontend, supplies Keera URL and four Apertus
aliases/tool rules, asks for environment examples and the complete open register.
Default connected model is `apertus-v1-5-8b`; optional 70B and no-tool thinking
aliases are documented in [inference settings](../data/INFERENCE_CONFIGURATION.md).
Unauthenticated model-list route returned 401; no key or successful inference was
tested. Offline remains a different local serving configuration.

`google/embeddinggemma-2` is verified as a model reference. Text-only local/shared
host is **recommended**, not yet selected by measured comparison; HF credit
eligibility, hardware and immutable config remain open. No endpoint/weights were
provisioned/downloaded. See [embedding recommendation](../data/EMBEDDING_DEPLOYMENT.md).
`AGENTS.md` and [module handoffs](../plans/MODULE_HANDOFFS.md) route scoped work;
[OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) is the current backlog. No commit/push.

## U10 / D18 — finalized schema and corpus/retrieval handoff

18 October 2026: user asks to remove useless structures and stabilize schemas
before a teammate populates the corpus and implements hybrid RAG. Contract v1
retains five PostgreSQL application schemas and evidence-backed typed entities/claims;
no separate institute/company databases. Migration 0005 removes unused/duplicate
plan/round/hit, match/support/selection and crawl-frontier tables from the active
schema, plus duplicate chunk encoding fields. Populated history is owner-only
archive; empty retired structures are removed. Frozen baseline metadata makes
older migrations independent of future runtime schema edits.

[Schema decisions](../data/RELATIONAL_SCHEMA.md), generated
[field inventory](../data/SCHEMA_REFERENCE.md), and the focused
[data teammate handoff](../data/INGESTION_RETRIEVAL_HANDOFF.md) are the query/build
contract. Actual DTOs own structured JSON; stages store bounded plans/results,
packs own matches, reason selections own editorial review. Source dates can be
passed at ingestion; relationship snapshots require full support and pinned
subject/object entities. Entity relations also use SQL NULL for the absent literal
(the previous JSON-null encoding blocked valid affiliations). Shared-host migration, real import/model quality and
live application integration remain future work.

Validation: 42 backend tests passed on disposable PostgreSQL 17 + pgvector, including
fresh schema parity and upgrades preserving 0003/0004 history. Generated field
reference and local documentation links checked. Frontend/template/recordings
unchanged. No shared-host migration or commit/push performed in this task.

## U11 / D19 — three exclusive backend lanes

User authorizes pushing pending schema work, stopping task services and preparing
three implementation prompts: A runtime/LangGraph/API/integration; B Apertus/
evidence/reports; C ingestion/database/hybrid and graph-supported retrieval/
EmbeddingGemma/reranking. Frontend remains separately owned.
[Exclusive paths](../team/PARALLEL_BACKEND.md) and the
[service contract bootstrap](../team/SERVICE_CONTRACTS.md) define the parallel pass.
A is the sole shared DTO/config/lock owner; each lane has its own tests/docs and
feature branch/worktree. Model recommendation is to measure hosted 70B first for
reasoning quality against the provisional 8B default; no quality result or silent
default switch is claimed. In-process typed ports, not HTTP between backend modules.
New source-derived case claims must preserve same-scope evidence and origin lineage.
Only task-owned Docker resources may be stopped; local inspection found no running
containers and the prior schema test container had already been removed.

## D20 — Integrate the backend lanes and HTTP frontend (18 October 2026)

Provenance: the user requested review/fixes and merge of `backend/runtime`,
`backend/intelligence`, `backend/backbone` and `ui-polish`, then explicitly chose
to implement the HTTP connection now. [Integration handoff](../team/INTEGRATION.md)
records reviewed branch tips, compatibility fixes, verified scope and prerequisites.

FastAPI/LangGraph, typed A/B/C adapters and deterministic PDF are composed in one
backend. The frontend defaults to authenticated HTTP; memory-only operator tokens
and explicit demo mode replace automatic mock serving. Board hold/outcome fields
and action notes persist. Exact visible report hashes and all-reviewed/one-kept
gates bind PDF export. Shared schema/config changes are centralized here.

Additive migration 0006 restricts case-scope provisioning and private runtime RLS;
0007 persists the UI fields. Historical migrations/assets/transcripts are preserved.
Disposable PostgreSQL tests and browser smoke use synthetic model/embedding adapters;
they establish integration behavior, not research quality or a live shared-host
deployment. No shared migration, ingestion/index publication or model download.
Future work starts in fresh branches from updated main, retaining completed lanes.

## D21 — Reconcile current documentation and rollout guidance (18 October 2026)

Provenance: user requests a full docs/status/TODO/team/migration audit after the
merge and asks whether they can perform the remaining setup. Code and reviewed
handoffs at main `4c6cfe2` establish the integrated baseline; current shared-host
state is not inferred. [Status](STATUS.md), [team index](../team/README.md) and
[live setup](../data/LIVE_SETUP.md) separate current tasks from historical lane
instructions and tests. Retain team provenance; no directory deletion is needed.

The user subsequently assigns the migration to Eric; the
[complete migration prompt](../team/prompts/04_SHARED_HOST_MIGRATION.md) bounds the
backup, upgrade, verification and handoff. Execution requires migration credentials
and a coordinated backup/window. Ordinary developer credentials remain the runtime
identity. No shared migration, ingestion, model download or service operation is
authorized/performed by this docs audit. Integration uses D20 (the earlier
parallel-build decision already used D19).

## D22 — Hosted encoder and Windows shell checkout (18 October 2026)

User requests permanent LF shell checkouts, implementation of Eric's supplied HF
endpoint, private env updates and commit/push to main. Explicit connected settings
select Apertus 70B and the supplied hf-serve CPU deployment/model revision.
The shared hosted encoder serves ingestion and runtime, with a pinned tokenizer,
exact remote usage checks and strict config hashes. [Live synthetic verification](../data/HOSTED_EMBEDDINGS.md)
establishes protocol/parity, not real corpus quality. Local models remain explicit
for offline operation. The user separately plans runtime identity/storage/checkpoint
configuration next; no shared DB writes/publication/deployment are inferred here.

Root `.gitattributes` enforces LF for shell scripts; simulated Windows-style Git
checkout and shell syntax passed. Eric must rewrite his existing checked-out script
and verify normal bootstrap before removing his temporary override. Secrets remain
only in ignored `.env`; public examples contain no private keys.

## D23 — Reconcile runtime handoffs and refreshed UI (18 October 2026)

Provenance: user supplies Eric’s host-access report and Renato’s acceptance output,
asks to keep docs consistent and merge the latest `ui-polish`, adapting as needed.
Renato’s `66dbfd1` is available remotely; Eric’s `300c677` is not published after
an automatic approval rejection. A reduced [runtime summary](../team/RUNTIME_ACCESS_STATUS.md)
records owner-reported results without publishing private bundles or reproducing
operational network/identity details. No rejected push is retried here.

Keep Mohamed’s board navigation and result presentation, with authenticated HTTP
and server-reviewed PDF from main. Browser PDF/PPTX remain explicit demo exports;
D17’s browser-export design is not a replacement for D20’s connected review gate.
New optional UI result metadata is not automatically supplied by the backend.
Host-local checks and sandbox tests do not establish either developer’s peer SSH
or a real provider-backed case. Renato can lead live acceptance if his terminal
has access; no live test success is inferred. Pilot publication remains the
corpus owner’s gate, independent of Elia’s unresolved route.

## D24 — Keyless browser discovery and isolated crawler (18 October 2026)

Provenance: user requests local-browser search without an API key and confirms
Crawl4AI should remain part of the tool pipeline. Select Playwright/Chromium with
DuckDuckGo HTML URL discovery, behind the existing discover/fetch ports and
LangChain tools/LangGraph research node. Chrome can be configured explicitly.
Brave API remains opt-in; neither provider is a hidden fallback. Browser pages
cannot execute commands or supply factual evidence from search snippets.

Keep robots-aware, public-IP-pinned acquisition and the existing case-local source
rules. Crawl4AI 0.9.5 requires xxhash<4, incompatible with locked LangGraph's
xxhash==4.0.1: provision an isolated conversion interpreter with its own lock.
Use sanitized acquired HTML and bounded JSON subprocess I/O, never backend
credentials or arbitrary page-controlled commands. [Web setup](../data/WEB_RESEARCH.md)
owns installation, configuration, verification and honest blocking behavior.

## D25 — Replace challenged HTML search with private SearXNG (18 October 2026)

Provenance: user asks to research and fix keyless search after the browser provider
hits challenges. A bounded local comparison found relevant results through private
SearXNG's DuckDuckGo/Yahoo engines and verified actual discovery → controlled
fetch → isolated Crawl4AI. Select this as the default, leaving browser and Brave API
as explicit alternatives. Do not describe SearXNG as an independent index or promise
unblockable search. Retain partial-engine diagnostics and explicit total failure;
keep DB retrieval and case-local source provenance. No frontend/schema changes.
[Evaluation](../data/WEB_SEARCH_EVALUATION.md) records experiments, alternatives,
observed limitations and primary references; [setup](../data/WEB_RESEARCH.md) owns
the private service/configuration. This supersedes D24's browser default.


## D26 — Gap follow-up, literal context and local reranking (19 October 2026)

Provenance: Elia requested updated-main testing, diagnosis of Renato's Helvetic
case failure and implementation of remaining backend research work on a new
branch. `codex/backend-research-completion` fixes the reproduced display-label
failure without accepting unsupported factual references; public research
unknowns are distinct from unclear operator intent.

Retain prior supported work across bounded novel gap queries and freeze after
research. Add literal source identity/neighbor expansion; title metadata remains
a discovery hint. Code records actual query/evidence paths with exact mirror
resolution. The writer cannot invent ontology links.

Provision pinned multilingual MiniLM locally as the compact CPU option, with
asset/runtime verification, full original query and exact bounded passage windows.
BGE remains an optional comparison; neither is a measured relevance winner.
[Setup/evidence](../data/RERANKING.md) and [branch acceptance](../team/BACKEND_RESEARCH_COMPLETION.md)
separate measured adapter checks from useful real-case/PDF acceptance. Shared
schema, ingestion and source artifacts were not modified by this task.

Actual worker acceptance exposed oversized fit context and unsupported draft
implications. Bound fit to accepted support, reserve finalization time, and allow
one same-pack wording rewrite with independent exact-hash reassessment. Supply
canonical cited passages to that assessment; do not relax factual/export gates.
User authorization now includes pushing to main and a subsequent frontend audit.

## D27 — Frontend integration and core workflow (19 October 2026)

Provenance: user explicitly requested frontend/backend compatibility fixes and
pushing the working core to main, permitting removal of unsupported extras. Add
free-text durable clarification, same-pack draft retry, explicit rewrite mode,
source quotes without entry metadata and read-only history. Honor server export
formats; connected PPTX stays unavailable. Optional structured metadata is not
inferred. The [audit](../team/FRONTEND_RUNTIME_AUDIT.md) records synthetic browser
checks separately from actual-provider partial PDF acceptance.
