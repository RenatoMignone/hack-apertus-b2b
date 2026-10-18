# Decisions, unknowns and next work

**Updated: 18 October 2026.** This records actual user choices and known gaps.
Proposed designs in other docs are not team decisions or completed work.

## Confirmed decisions

**D12 / implemented database layer and shared host, 18 October:** the user
authorized the implementation plan after selecting one shared database on the
user's Windows/WSL2 computer. Four developers run their code locally and connect
through individual SSH accounts/tunnels. Docker Compose packages PostgreSQL 17
+ pgvector, shared MinIO and optional local Langfuse. Database ports bind
loopback. Python 3.12/Pydantic/SQLAlchemy Core/psycopg/Alembic implement the data
contracts. See [deployment and measured checks](../data/DEPLOYMENT.md).
Real model artifacts/endpoints, actual team keys/network reachability, frontend
and complete report workflows remain pending. This supersedes the earlier
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

## Open-question backlog

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
Exact model/tokenizer sources/revisions/endpoints remain deferred at user request.

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
Retrieval feeds a frozen `ReportEvidencePack`; detailed processing both before
and after the pack still requires [mapping](../plans/REPORT_PROCESSING_BOUNDARIES.md).
Scraper choice/behavior is deliberately deferred; older acquisition plans remain
proposals, not an implementation selection.

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

**18 October user answers (U2):** recorded below. The agent selected the delegated
medical slice and evaluation protocol in [PILOT_SCOPE.md](../challenge/PILOT_SCOPE.md).
Selected scope is diabetes technology; English outputs are required and DE/FR/IT
support desirable. A later partner workbook now supplies the initial discovery
inventory (best-effort, not authoritative DNS coverage). Public robots-allowed
collection is authorized within relevant scope. Endpoint and deployment inputs
will arrive before development; branding has now arrived. Partner example needs and
expected entities can be supplied; neither those examples nor historical cases
have been delivered. No application implementation is authorized by this update.

These are a working backlog, **not a request for approval or a blocker to the
completed documentation pass**. Resolve them at the relevant next task; do not
ask again for facts already supplied.

| ID | Question | Who/source can resolve it | Why it matters / current handling |
| --- | --- | --- | --- |
| Q01 | Inventory and official discovery seeds | Partner workbook received and inspected, 18 October | 42 actual entries including ARTORG/DCB; Notes says 71. Import actual URL rows as best-effort candidates, verify live access and extend discovery; see provided_material/README. |
| Q02 | Medical slice | Resolved under user's delegation | Diabetes technology: glucose monitoring, automated insulin delivery and supporting digital tools; all three source families retained. |
| Q03 | Partner examples and expected experts/units | Availability confirmed by user; delivery pending | Partner can supply public/anonymized needs and labels. No files received; do not infer an available historical-case dataset. |
| Q04 | Recall aggregation and entity counting | Defined under user's delegation | Primary intent-balanced macro Recall@10 >= 0.80; typed unique persons/units in a shared top ten; per-type and micro diagnostics; protocol in pilot scope/EVALUATION. Internal definition, not organizer clarification. |
| Q05 | Endpoint, protocol, model ID, authentication, quotas | Deferred to user's pre-development handoff | User will supply before development; keep template `LLM_*` interface and do not guess values. |
| Q06 | Deployment and hardware/resources | Deferred to user's pre-development handoff | No deployment capability claimed; keep external self-contained deployment constraints. |
| Q07 | Languages | Resolved by user | English UI/results/slides baseline; DE/FR/IT source/query support desirable. Preserve original evidence; assess language extensions separately. |
| Q08 | Automatic teaser export and branding | Export confirmed; assets received | English logo PNG and 19-slide 16:9 PowerPoint template inspected. Use supplied design, replace placeholders and validate generated slides; no export implemented yet. |
| Q09 | Additional organizations | Policy resolved by user; actual additions require evidence | Start with partner references, expand to healthcare-related organizations operating in Canton of Bern; no assumed locality from network membership. |
| Q10 | What may be retained/redistributed from public pages, transcripts, logos and contact information under current terms? | Current organizer terms, N1 and source rights holders where needed | N1 limits template/logo use to this challenge; no broader asset license or blanket redistribution/transcript-publication consent established |
| Q11 | Does the current submission form still require the exact two-PDF ZIP and <=10-slide pitch, and how does it count report references? | Signed-in Sprintd guide/current organizer instructions | Historical addition remains flagged; local template's report naming/limits recorded separately |
| Q12 | What are the live pitch/Q&A duration and latest delivery cutoff? | Current on-site organizer announcements | Historical cutoff is 19 Oct 14:30 CEST; two-minute limit is the video cap, not live pitch time |
| Q13 | Are remote template ancestry and public visibility correct, and what is the final team name? | Team's GitHub/submission account | Initial context was committed/pushed to `origin/main` as `ab3d534` at user request; ancestry, visibility and team name are not established by that push |
| Q14 | Collection extent, formats and freshness | Website/public-source priority resolved; refresh policy proposed | Collect relevant accessible public information, websites first, linked PDFs next; use safe engineering budgets and report omissions. Dated snapshot and conditional pre-demo refresh proposed, no freshness SLA selected. |
| Q15 | Exact model/tokenizer sources, revisions, compatible adapters and limits | Explicitly deferred by U6 | Named roles/candidates are documented; resolve immutable configs before real embeddings/inference, without guessing artifact URLs. |
| Q16 | PostgreSQL/framework versions, Langfuse resources, trace/backup retention and deployment | Implementation/deployment handoff | Logical services and failure/isolation contracts selected; no provisioned database, working instrumentation or recovery test claimed. |
| Q17 | Backend language/framework, HTTP schemas, caller/session integration and frontend tooling | Team implementation handoff | U7 selects HTTP separation and modular folders only. API handoff proposes routes/projections; no OpenAPI/server or frontend setup yet. |
| Q18 | Exact retrieval → pack and pack → final output transformations | Dedicated processing design work | High-level content/invariants exist; intermediate DTOs, stage algorithms, support/repair/review rules and run/export mapping need worked examples before implementation. |

## Suggested next work after a new implementation task

**Material update / U3, 18 October:** the user supplied three files under
`docs/provided_material/`: a best-effort UniBE discovery workbook, a PowerPoint
template and an English agency logo. [Inspection notes](../provided_material/README.md)
record contents, exact counts, discrepancies and SHA-256 hashes. Preserve these
originals. This resolves inventory-file and branding delivery, not partner
examples, gold labels, historical cases, taxonomy, inference or deployment inputs.

Use the selected diabetes-technology scope and verified discovery seeds, obtain
the promised endpoint/deployment details and partner examples, and verify the
expected entities. Implement the paired plans with evidence and memory contracts
first, then the case workflow and confirmed PowerPoint export. Extra sources
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
