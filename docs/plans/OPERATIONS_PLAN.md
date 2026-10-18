# Phase 2 — Case research, matching and presentation

**18 October 2026 · Workflow implemented and integrated; real-corpus deployment pending.**
Start with the [visual pipeline](../architecture.html). The
[architecture contract](ARCHITECTURE.md) owns component placement, domain profiles,
evidence-pack requirements and deployment. [Phase 1](INGESTION_PLAN.md#7-shared-contract-v1--owned-here-consumed-by-phase-2)
owns shared evidence/memory schemas; do not duplicate them here.

## 1. Outcome and current intake

The operator reads the confidential business plan and one-pager outside the
application, then **types permitted keywords, context, public company information,
what she knows and suggested research directions**. No PDF or automatic email
intake now. Her suggestions are leads, not established public facts.

Support conversational corrections, targeted agent questions, inspectable
matches, a cited draft and PDF-first report; editable PowerPoint follows later. The
[output structure](OUTPUT_REPORT_STRUCTURE.md) remains unchanged. Historical
comparisons and numerical economics require eligible data; neither is invented.

Future PDF intake is a disabled extension requiring explicit permission and
revised information-handling/access/retention/deployment rules. Local inference
or model redaction does not override the confidential-document boundary.
Public linked research PDFs remain eligible for Phase 1 collection.
[T05 00:48–01:22, 01:43–04:41](../recordings/bern-navigator-followup-2026-10-18.txt).

Selected stack: LangGraph with PostgreSQL checkpoints, Phase 1 PostgreSQL
full-text + pgvector retrieval with RRF fusion, EmbeddingGemma 2 candidate,
BGE reranking, Apertus v1.5 8B and optional bounded 70B fallback; local Langfuse
observes execution. [Keera aliases/base URL](../data/INFERENCE_CONFIGURATION.md) are supplied; exact
revisions, compatible runtime/tokenizer packages and limits remain open.
The engine is domain-independent; pilot concepts, sources, geography, validation
and ranking settings come from a versioned profile. Current pilot remains Bern
diabetes technology across UniBE, ARTORG and DCB, English-first with DE/FR/IT
extensions. No model endpoint/hardware capability is yet verified.

Physical case tables, graph recovery and export lineage are owned by
[case state](../data/CASE_STATE_AND_LINEAGE.md); [retrieval](../data/RETRIEVAL_SPEC.md)
owns branch/fusion/ranking rules, and [observability](../data/OBSERVABILITY.md)
owns sanitized traces. See the [data-layer router](../data/DATA_LAYER.md).

## 2. Case/run state and contracts

```text
draft → intake_validated → interpreting → researching_company
      → retrieving → validating → evidence_pack_ready
      → drafting → ready_for_review → export_ready → exported
```

Any active step may become `needs_clarification`, `partial`, `failed` or
`cancelled`. Preserve completed evidence and the failed stage. Resume idempotently:
no duplicate successful calls, case records or artifacts.

| Record | Required contents |
| --- | --- |
| Case | ID, owner/access policy, permitted message, current input revision, resolved company, corrections, selections and export history |
| CaseRun | Case/input/result revisions; pinned domain-profile, schema, taxonomy, snapshot, index/embedding build and case evidence manifest; model/prompt versions; queries, budgets, stage status, timing/usage and limitations |
| UserIntentState | Full permitted request, priorities/exclusions, accepted answers, explicit assumptions and unresolved questions; passed through retrieval, synthesis and export |
| DialogueTurn | Turn/case IDs, role, permitted text, new request/answer/edit intent, targeted revision and timestamp |
| FollowUpQuestion | ID, affected field/revision, reason, question, optional choices, required/optional status, answer reference and checkpoint |
| ResultRevision / EditRequest | Parent/base revision, instruction and interpreted edit, affected sections/claims, retained/added/removed evidence and validation state |
| Selection | Claim/result/evidence IDs, keep/reject, operator note and run; relevance judgment does not establish factual truth |
| Export | Reviewed revision, selected claims, source manifest, template/logo versions/hashes, output path/hash, generation time and validation results |

Keep correspondence and case state isolated from the shared public corpus.
Only reviewed eligible records may enter Phase 1 publication; user corrections
do not automatically alter taxonomy, embeddings or shared facts.

## 3. Prepare the case evidence

| Stage | Processing | Produced record / limits |
| --- | --- | --- |
| Capture | Preserve typed message; check limits/access; pin profile and source snapshot | Immutable input revision; intake heuristics cannot certify arbitrary text as non-confidential |
| Interpret | Apertus extracts company/domain clues, objective, application, needs, stage if stated, constraints, exclusions and unknowns | `InterpretedNeed`; keep original wording and separately labeled concept/expansion proposals |
| Resolve company | Verify submitted domain/identity against public attributable sources; distinguish parent, subsidiary, origin and operating location | `CompanyProfile` with field-level claims; clarify ambiguous names before joining histories/contacts |
| Normalize research | Fetch permitted public pages in connected mode, then reuse Phase 1 parsing, spans and claim validation in case scope | Case evidence manifest; search snippets alone are not evidence; offline use packaged sources or explicit unknowns |
| Query plan | Combine full intent, verified profile, taxonomy, original terms/synonyms, related concepts, reliable filters and budgets | `QueryPlan` with revision/profile/snapshot IDs; suggested groups require verification; do not reduce intent to keywords |
| Expertise retrieval | Hybrid `search_evidence` / `search_entities` over required source families; retrieve project/person/unit detail and neighboring passages | Provenance-bearing candidates; broader ecosystem and company-specific needs are complementary query views |
| Historical retrieval | `search_cases` with access filtering and current case excluded, only when a permitted dataset exists | Similarities, differences, dates, known outcomes and separate similarity method; currently unavailable |
| Numerical preparation | Model-assisted extraction proposes figures; code validates value/unit/currency/period/geography, source and actual/plan/estimate status; calculate with explicit formulas | Numerical fact/scenario records, sensitivity and chart-ready data; absent inputs mean no numerical claim |
| Rank/aggregate | BGE reranks query/passage pairs; aggregate unique entities without counting duplicate pages as corroboration | Separate lexical/vector/reranker components and ranking-method version |
| Support/constraint checks | Resolve spans and assess semantic support, location/affiliation/status, explicit exclusions, direct versus adjacent application | Accepted matches, conflicts/review queue and evidence-strength reasons; unknown is not confirmed fit |
| Close gaps | Fetch neighboring evidence, revise queries or ask focused questions within budgets | Supplemental support or explicit partial/no-match/failure result |
| Derive arguments | Need → evidenced capability → possible benefit, prerequisites and limits | Labeled argument derivations; company benefits distinct from cantonal contribution |
| Freeze pack | Resolve permissions/references/revisions and include facts, literal evidence, matches, arguments, gaps and optional records | `ReportEvidencePack` per architecture contract; complete or explicitly partial |

The email/website does not silently replace the operator's current request.
Scientific capability and specific research fit take priority over personal
marketing connections. [T05 05:15–07:21](../recordings/bern-navigator-followup-2026-10-18.txt).

Contextualization uses the original request and versioned concepts without
forcing one category. Execute lexical and vector retrieval independently after
reliable access/snapshot constraints, then fuse and rerank. Inferred topics are
ranking hints; reranked passages still undergo claim/constraint validation.
The model cannot establish that a perfect expert is absent from unindexed pages.

Generate reproducible Boolean queries/encoded links for further research;
label suggestions separately from executed searches and factual sources.
Connected tool inputs contain only eligible context. Offline runs never claim
live source checks. Store visited URLs, timestamps, failures and permitted excerpts.

## 4. Scores, budgets and factual support

Keep these fields separate:

- `match_score`: relative expertise relevance, method/version, scale and reasons.
- `case_similarity_score`: historical-case similarity, its own method/scale.
- `evidence_confidence`: categorical support assessment with freshness, identity,
  missing facts and conflicts; never the model's self-reported certainty.

Initial ranking signals: lexical/semantic relevance, taxonomy/application fit,
evidenced geography and evidence quality. Tune on development data and freeze
before evaluation. No calibrated percentages or success probabilities are claimed.

Proposed evidence rubric: high = directly supported required facts with no
material unresolved contradiction; medium = supported facts with incomplete
freshness/identity/context; low = insufficient support for a recommendation.
Keep unsupported candidates in review/limitations. Freshness thresholds depend
on source type and remain implementation configuration.

Initial budgets: 30 candidate passages, eight synthesis passages, at most three
retrieval rounds plus time/token/call limits. These are tunable passage budgets,
**not** a cap on the final top-ten entity evaluation. Expand evidence within
budget or disclose insufficient coverage. Use the matching tokenizer/template,
reserve output capacity and avoid arbitrary truncation. An unavailable 70B route
leaves explicit limitations; it does not certify the smaller model's output.

A valid quote/ID/URL is necessary but insufficient: assess semantic support.
Never infer roles, contacts, clinical suitability, partnerships or willingness
to meet. No-match means no supported match in the searched scope; distinguish
source failures, partial coverage, unavailable fields and outside-pilot requests.

## 5. Report, review and export

U8: review is per reason card, not per database match. Every card must be kept or
rejected and at least one kept before accepted review/export. Rejected means
editorially omitted, not false. New web sources stay flagged and case-scoped.
Rephrase reuses the pack; focus/new-fact/identity edits rerun affected research.
The exact content/support hash controls selection carry; changed cards reset.


1. Compose the [agreed sections](OUTPUT_REPORT_STRUCTURE.md) from the frozen pack.
   Every new factual assertion must be supported; otherwise return to research.
2. Validate draft claims/citations and all numerical/chart lineage. Retain
   original-language support for derived English descriptions.
3. Let the operator inspect sources, correct interpretation and select/reject
   findings. Keep uncertainties even when a finding is selected.
4. Generate PDF from the exact reviewed revision/selections; editable PowerPoint is later work.
   Render charts deterministically from prepared datasets. Keep source references
   on slides, with detailed notes/appendix and snapshot dates.
5. Render slides; check readability, overflow, tables, links, citation completeness
   and editability. Store output hash, source manifest and validation results.

Use the [supplied template/logo](../provided_material/README.md), preserving
editable layouts/theme and original logo proportions. Replace German/lorem
ipsum/example figures, fake contacts and document IDs. Remove instruction slides
and unchosen classification footers. Nineteen example slides do not mandate a
19-slide deck; 5–10 concise slides is a proposed adjustable format, not an
organizer submission rule. Branding is separate from evidence selection.
Sending exports and arranging meetings remain human actions.

## 6. Clarification and revision loops

Ask focused questions when company identity, application, priorities or edit
scope materially changes the answer. Required questions pause only dependent
steps; independent work can continue. Record optional assumptions explicitly.
Silence is not an answer; declined answers leave unknowns. Match replies to
question and revision IDs so stale answers cannot overwrite a newer report.

| Edit | Resume point | Reuse / invalidation |
| --- | --- | --- |
| Shorten/reword/layout | Synthesis/rendering | Reuse accepted pack; revalidate wording; regenerate affected exports |
| Change need/focus/exclusion | Query planning/retrieval | Preserve unaffected facts, update intent and evidence; create new pack |
| Correct company identity/new fact | Identity research/validation | Recheck dependent facts/matches; invalidate incompatible selections and exports |
| Remove caveat/assert unsupported claim | Evidence review | Cannot make missing support valid; retain limitation or retrieve support |

Keep a compact change description and earlier revisions subject to retention.
Model interpretation of an ambiguous edit remains pending until clarified.
No automatic public-memory updates or model training from conversational edits.

## 7. Implementation and validation gates

The selected [source structure](SOURCE_STRUCTURE.md) places HTTP transport,
application use cases, contracts, workflows, data/model adapters, evidence and
reports under `src/backend/`, with an independent `src/frontend/`. Read the
[HTTP handoff](FRONTEND_BACKEND_API.md) before extending UI/server. The graph,
adapters and PDF are implemented; [integration evidence](../team/INTEGRATION.md)
records synthetic end-to-end checks. Optional web uses controlled HTTP acquisition
and Crawl4AI conversion. Real corpus/models and target-host operation remain
[live setup prerequisites](../data/LIVE_SETUP.md).
These modules need not be separate services. LangGraph owns
bounded state/checkpoints, not the corpus. Keep credentials server-side,
authorization/access-aware caches and cancellation/retries. Disable external
tracing and runtime downloads for the isolated target.

Use PostgreSQL for business case history and the supported saver in a separate
LangGraph database for checkpoints. No distributed transaction is assumed;
persist stage outputs idempotently and reconcile on resume. Instrument stages
through local Langfuse with masked/allowlisted metadata. Its outage must not
block search or export, and traces cannot replace canonical evidence.

Text intake, fixed-snapshot research, clarification/revisions and reviewed PDF
export are integrated. Next validate them against the published pilot corpus;
historical cases, numeric figures and editable slides remain optional later work. Future attachments
remain outside this implementation baseline until separately authorized.

Acceptance scenarios: synonyms/negation, multiple needs, ambiguous company,
missing site/facts/contacts, malicious source text, stale/conflicting profiles,
partial institutions, missing historical dataset, economic input absence,
model timeout, isolated concurrent cases, focus/wording edits, unanswered/stale
replies, superseded exports and network-disabled execution. Verify evidence and
intent survive every handoff. Tests of future attachments belong to that later scope.

Use [pilot/evaluation rules](../challenge/EVALUATION.md): independently reviewed
Recall@10, full claim support, supported-field completeness, three-family coverage,
case isolation and export traceability; record latency/cost where measurable.
The two phases integrate when one permitted case pins a snapshot, returns
supported matches or honest limitations and exports reviewed claims with lineage.

Keera connection details are supplied; authenticated limits, actual model/embedding
hardware, taxonomy contents, search provider and export library remain open.
Historical cases and gold examples are absent. The
[active register](../project/OPEN_QUESTIONS.md) owns unresolved items.
See [architecture/dependencies](ARCHITECTURE.md#target-architecture-mandatory) and
[decision backlog](../project/DECISIONS_AND_OPEN_QUESTIONS.md).
