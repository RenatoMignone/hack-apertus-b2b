# Phase 2 — Case intake, research, matching and presentation

**Date:** 18 October 2026. **Status:** implementation proposal based on the user's
case workflow; no interface, endpoint integration or measured results exist.

**Dependency:** [Phase 1 — Ingestion, taxonomy and memory](INGESTION_PLAN.md),
especially its shared contract v1 in section 7. Do not create a second taxonomy,
duplicate evidence schema or incompatible case-memory format in this phase.

**Initial architecture to validate:** use LangGraph for state/control and the
Phase 1 Weaviate/BGE-M3 hybrid memory interface, followed by BGE-reranker-v2-m3.
Apertus 1.5 8B is the initial interpretation/synthesis model; route difficult
work to 70B when available within budget. These are starting choices, not
measured superiority or verified endpoint support. Section 8 of the ingestion
plan specifies exact stage-to-stage information handoffs.

**Selected pilot:** [diabetes technology](../challenge/PILOT_SCOPE.md), focused on glucose
monitoring, automated insulin delivery and supporting digital tools. English is
required for UI/results/slides; German/French/Italian query/source support is
desired, with English explanations and original-language evidence retained.

## 1. User outcome

A business developer opens a new case, pastes permitted email/context and presses
Enter. The system interprets the request in context, researches the company's
identity and background, searches Bern expertise and approved previous cases,
and presents concise, source-backed recommendations. The operator can correct
the interpretation, add supported attachments, select findings and export an
editable PowerPoint with sources and limitations.

Required outputs from the user's workflow:

- A company description supported by evidence.
- Relevant primary sources and reproducible Boolean search queries/links for
  further investigation.
- Related previous cases with explained similarity scores, when permitted data
  exists.
- Relevant people, units, projects, capabilities and services with match reasons.
- Potential economic benefits/impact, with assumptions and uncertainty visible.
- Confidence indicators with an explicit evidential basis.
- Final PowerPoint slides containing the reviewed material and sources.

This extends the baseline search prototype with the user's requested case and
presentation workflow. It does not establish new official organizer criteria.

## 2. Experience and case state

### 2.1 New case and submission

Provide a case workspace with a text composer, attachment control, progress
display, interpreted request, company profile, findings and source inspector.
Enter submits; Shift+Enter adds a line break. Preserve the submitted text and
its revision so corrections do not silently rewrite earlier runs.

Accept public/non-confidential context only. Clearly explain that confidential
business plans must be kept out of model inputs, including local inference.
The operator prepares a permitted summary before submission; model-based
redaction of a confidential plan would already violate that boundary. Local
intake checks can flag obvious prohibited content, but cannot certify that an
arbitrary email is safe. Avoid automatic remote processing on paste/upload.

Begin with pasted text and text PDFs; add image/scanned-PDF extraction as a
second milestone. Offer only formats actually supported, with explicit size,
page and processing limits. Preserve file/page provenance using Phase 1's
document/evidence schemas. Do not promise support for arbitrary file types.

### 2.2 State machine

```text
draft → intake_validated → interpreting → researching_company
      → retrieving → validating → ready_for_review → export_ready → exported
```

Any active step can produce `needs_clarification`, `partial`, `failed` or
`cancelled`. Record the failed stage and retain completed evidence. A user
correction creates a new input revision/run and invalidates dependent results
and exports. Resumption is idempotent; it must not duplicate case records,
model calls already committed successfully or published artifacts.

### 2.3 Case and run records

- **Case:** ID, title, owner/access policy, permitted inputs and attachment IDs,
  current revision, interpreted need, resolved company entity if any,
  operator corrections, selections and export history.
- **CaseRun:** run/case/revision IDs, pinned `snapshot_id`, `taxonomy_version`,
  case evidence manifest ID, model/prompt versions, budgets, step statuses,
  query variants, results, limitations, timing and usage.
- **Selection:** result/claim/evidence IDs, keep/reject state, operator note and
  run ID. Selection expresses relevance judgment, not automatic factual proof.
- **Export:** selected run/revision, selected claim IDs, source manifest, template
  version, output hash/path, generation time and validation results.
- **DialogueTurn:** turn/case IDs, role, permitted text, intent
  (`new_request`, `clarification_answer`, `revision_instruction`), parent
  result/input revision and timestamp. Attach optional explicit edit targets.
- **FollowUpQuestion:** question ID, case/run/result revision, reason,
  affected field, question text, suggested answers if useful, required/optional
  status, answer reference and graph checkpoint ID. Record any assumption
  separately from an actual answer.
- **ResultRevision:** revision/parent IDs, triggering user instruction,
  interpreted edit, retained/removed/added claim IDs, priorities/exclusions,
  evidence-pack ID, run/snapshot IDs and validation status. A result revision
  can reuse an input revision when the change affects only presentation.

Keep raw correspondence and private case state out of the public expertise
corpus. A reviewed permitted summary can later become a Phase 1
`CaseMemoryRecord` through its staging/publication interface.

## 3. Understand the request before selecting keywords

The supplied follow-up transcript confirms natural-language context plus
keywords and iterative narrowing [T05 01:43–04:41](../recordings/bern-navigator-followup-2026-10-18.txt).
The operator can provide public company facts and suggestions about Bern groups;
they should not have to know scientific terminology in advance. T05 00:48–01:22
explicitly excludes non-public information, including the discussed one-pager.
Treat inputs as permitted public context/operator-authored safe descriptions;
do not assume arbitrary correspondence or a one-pager is model-eligible.

Use Apertus to build an `InterpretedNeed` with:

- Company name/domain clues and evidence spans from the permitted input.
- Plain-language objective, desired collaboration and intended application.
- Relevant technology, medical domain, development stage and geography when
  stated; explicit unknowns otherwise.
- Positive requirements, exclusions/negations and constraints.
- Original keywords plus contextual synonyms, each linked to input evidence or
  marked as a proposed expansion.
- Concept candidates from the pinned taxonomy, ambiguities and alternatives.

Validate the structure and show a compact editable interpretation. Continue
automatically when sufficiently clear; ask a focused clarification only when
an ambiguity materially changes company identity or the search direction.
An unclear field must not prevent independent useful work on clear fields.

Use the same `resolve_concepts` interface and definitions as ingestion.
Classification can be multi-label. Preserve the complete permitted request for
retrieval/reranking; do not reduce it to a bag of keywords. Test terms used in
different senses, negation and adjacent applications as distinct cases.

## 4. Establish company context before final matching

Prioritize scientific fit over personal marketing. T05 05:15–05:48 deprioritizes
American/Harvard personal-background pitches and emphasizes reusable search
structure; 06:01–07:21 asks for specific, concise, readable activity descriptions.
Company-specific research means relevant products/needs and research fit;
nationality, alumni connections and speculative personal appeal are not required.

Resolve the legal/operating identity from the submitted website, public company
pages and other attributable public sources. Distinguish headquarters, origin,
operating locations, subsidiaries and target expansion location. An American
background is a possible fact to verify, not a default assumption.

Create a `CompanyProfile` containing supported description, website, locations,
products/technology, research interests and relevant public activities. Each
field points to claim/evidence IDs and dates. Keep user-stated information
separate from independently sourced facts. Do not invent a profile when public
information is missing; return an explicitly incomplete profile.

When several companies share a name, retain alternatives and obtain a decisive
identifier before attaching their histories or contacts. The email expresses
the current request; generic website content must not silently replace it.

In connected mode, company research uses bounded search/fetch tools. Retrieved
pages enter a case-scoped evidence collection through Phase 1 normalization and
validation. Search snippets alone do not establish claims. Record queries,
visited URLs, timestamps, failures and permitted excerpts. Tool inputs contain
only permitted public/non-confidential information.

In disconnected mode, use packaged company evidence or the permitted input,
state the snapshot date and disclose missing information. Do not claim a live
company check. External research and complete offline operation are separate
execution modes.

## 5. Run the complementary searches

### 5.1 Bern ecosystem search

Answer why Bern could be relevant to this company's field: institutional
expertise, infrastructure, services and evidenced regional connections. Query
Phase 1 `search_evidence` and `search_entities` across UniBE, ARTORG and DCB,
then any additional configured sources. Surface partial coverage explicitly.

### 5.2 Company-specific opportunity search

Combine the interpreted need with the verified company profile to identify
specific research groups, people, projects or services that could help. Preserve
hard constraints and distinguish direct matches from adjacent capabilities.
Other relevant companies may appear only with supporting public evidence;
topic overlap does not prove a partnership or supply relationship.

### 5.3 Previous-case search

Call `search_cases` using need, concepts and permitted company context, with
access filtering and `exclude_case_id` set to the current case. Return a short
summary, similarities, material differences, dates, known outcomes and evidence.
Do not imply that a previous outcome predicts this company's success.

The partner can provide example needs and expected experts/units; these have
not yet arrived and do not establish availability of historical cases.
No approved historical dataset is currently supplied. Return “previous-case
data unavailable” when appropriate, separately from “no similar case found.”
Synthetic demonstration cases must be labeled in results and slides.

### 5.4 Query expansion and further research

Run exact wording, reviewed synonyms and broader/related concept variants.
Keep expansion provenance and avoid treating a related concept as an exact
synonym. Generate inspectable Boolean query strings and encoded search links
for additional exploration; label them “further research,” not factual sources.
Keep generated suggestions distinct from searches actually executed.

The application controls bounded research steps and tool permissions. Do not
assume that the hosted model supports every tool-calling or reasoning mode.
Simple orchestrated steps are sufficient; autonomous browsing is not required.

## 6. Rank, validate and express confidence

Retrieve candidate evidence using Phase 1 indexes, then assess relevance to the
full need and company context. Entity results aggregate supporting passages
without counting duplicated pages as independent corroboration. Apply hard
constraints explicitly; an unknown attribute is not a confirmed match.

Proposed first ranking signals are lexical/semantic relevance, taxonomy fit,
application fit, supported geography and evidence quality. Store component
values and the ranking method/version. Tune weights on a development set and
freeze them before evaluation; do not invent calibrated percentages.

Use separate output fields:

- `match_score`: relative relevance score with method, scale and explanation.
- `case_similarity_score`: historical-case similarity with its own method/scale.
- `evidence_confidence`: categorical assessment with reasons, missing facts,
  freshness and conflicts; not the model's self-reported certainty.

A proposed evidence rubric is high when all required factual claims have direct,
accepted support and no unresolved material contradiction; medium when claims
are supported but freshness/identity/context is incomplete; low when evidence
cannot support a recommendation. Low-confidence candidates belong in review or
limitations, not accepted factual recommendations. Define freshness by source
type during implementation rather than assuming one universal age threshold.

Before rendering an accepted result, check that all referenced claims and spans
resolve, each claim is semantically supported, and the result does not assert
an unobserved relationship or willingness to collaborate. Unsupported results
are removed or explicitly downgraded. Human selection does not bypass support
checks. Keep relevance judgment distinct from source verification.

## 7. Result contract and economic opportunity

Each `MatchResult` contains entity ID/type, supported name, affiliation/unit,
role/contact where available, expertise, projects/services, matched concepts,
plain-language reason, direct-versus-adjacent status, evidence/claim IDs,
scores, confidence reasons, limitations and snapshot/run IDs. Missing source
fields remain unavailable. The UI resolves citations to exact excerpts/pages.

The `CaseResultBundle` contains the interpreted need, company profile,
ecosystem findings, specific matches, previous cases, further-research queries,
economic opportunity assessment, coverage/failures and source manifest.

For economic opportunity, distinguish benefits to the company from possible
benefits to the Canton of Bern. Begin with qualitative, evidence-linked
mechanisms such as access to an evidenced facility or a relevant research
capability. Describe them as potential benefits with prerequisites; do not
assert revenue, jobs, cost savings or time savings without inputs and a method.

If quantitative scenarios are later requested, record input values, sources,
units, assumptions, time horizon, formula and sensitivity. Label estimates and
unknowns. A confidence indicator does not validate an unsupported forecast.

## 8. Operator review and PowerPoint export

### 8.1 Conversational revision and follow-up requirements

**User requirements:** the operator can instruct the agent to modify/refocus an
existing output, and the agent can ask follow-up questions. These are normal
parts of the case workflow, including after a report has been drafted. The
stakeholder confirms correction instructions such as disregarding a direction
in [T05 04:24–04:41](../recordings/bern-navigator-followup-2026-10-18.txt).

Accept natural-language edits such as “focus less on nutrition and more on
glucose monitoring,” “exclude this unit,” or “make the report shorter.” Preserve
unaffected case facts/selections and link every edit to the result revision it
targets. Provide the updated report and a compact change description; retain
earlier revisions for comparison/rollback subject to retention policy.

Interpret an edit as an `EditRequest`: instruction/turn ID, base revision,
target sections/results, requested focus/exclusions, presentation changes,
new factual needs and ambiguity. Treat a proposed interpretation as pending
when it could materially misread the user. A formatting change reuses accepted
evidence; a changed research need updates the query plan and retrieves supporting
evidence. Revalidate every changed claim and citation. Requests to remove caveats
or assert unsupported facts cannot turn missing evidence into a supported claim.

Use `FollowUpQuestion` when identity, intended application, priorities or edit
scope materially affects the answer. Examples: “Do you mean sensor development
or clinical validation?” and “Should nutrition be removed or just shortened?”
Ask one or a small set of focused questions with optional choices and free text;
do not require the user to complete a scientific taxonomy or rigid intake form.
Avoid repeating questions already answered in the conversation.

Required questions pause only dependent steps at `awaiting_user`; independent
retrieval may continue. Optional questions allow progress with an explicitly
recorded assumption. Silence/timeouts are not answers. Resume from the matching
case/revision checkpoint when the reply arrives. Correlate replies by question
ID; an answer to an old revision must not overwrite a newer report. The user can
decline a question, yielding an explicit unknown or bounded partial result.

Store a versioned `UserIntentState`: full permitted request, answers, priorities,
exclusions, accepted clarifications and unresolved questions. Pass this state
through retrieval, reranking, synthesis and export so “focus less on X” is not
lost at the next node. Corrections are scoped to this case unless the user
explicitly initiates reviewed shared-memory changes.

An edited result marks its old export as superseded; regenerate from the chosen
reviewed revision. The export ID and source manifest must identify that revision.
Edits to a deck's visible text should be represented as reviewed content changes
so the stored report and subsequent exports remain consistent.

### 8.2 Review and output generation

Show the interpretation and company profile before the shortlist, with sources
accessible beside each factual statement. Let the operator correct identity,
refine the need, keep/reject findings and review adjacent opportunities. Warn
when a correction makes an existing selection/export stale.

Generate an editable `.pptx` from the reviewed bundle using a deterministic
template. Proposed structure: company/context, need, Bern ecosystem fit,
selected expertise, relevant previous cases if available, potential benefits
and next steps, then sources/limitations. Omit unavailable optional sections
rather than filling them with invented content. Target a concise 5–10 slides,
adjustable to the case; this is a proposed format, not a new submission limit.

Put useful source references on slides and complete evidence references in
speaker notes or a source appendix. Retain uncertainty, snapshot dates and
adjacent-application labels. Exclude rejected findings and confidential inputs.
Use permitted assets only; do not assume permission to reuse institutional logos.

The [partner template and English logo](../provided_material/README.md) are now
supplied and inspected. Use their design as the export baseline, selecting
appropriate layouts from the 19-slide example deck rather than reproducing all
examples. Preserve theme/layouts and editable elements. Replace German/lorem
ipsum/example data with English case content; remove instruction slides, fake
contacts, document-number placeholders and unchosen classification footers.
Use the original logo without distortion. Record template/logo hashes in export
metadata and validate actual rendering during implementation. Keep branding
configuration independent of evidence selection and export logic.

Render generated slides for visual QA: check overflow, readability, tables,
links and citation completeness. Reopen the `.pptx` to verify editability and
content integrity. Store its source manifest and output hash. Export is a local
artifact action; sending slides or contacting experts remains a separate human
action. The company deck is distinct from the hackathon technical-report PDF.

## 9. Implementation structure and dependencies

Implement the bounded agent flow as LangGraph nodes:

```text
interpret or apply_edit → resolve_company → build_query_plan
  → hybrid_search → rerank → validate_evidence → synthesize → review/export
                              ↓
                   missing context or ambiguity
                              ↓
                     ask_user → await_answer → resume appropriate node
```

Formatting-only edits can go directly to synthesis with the accepted evidence
pack. Missing evidence can loop to query planning within the three-round budget.
The query plan carries snapshot/taxonomy IDs, full intent state and exclusions.
Search returns provenance-bearing hits, reranking returns the same IDs with
separate scores, and synthesis receives an explicit evidence pack. Checkpoints
store revisions, question IDs and evidence references with per-case access
isolation; LangGraph is not the corpus store. Persist local checkpoints and
disable unsolicited external tracing for a disconnected target.

Keep 30 initial candidate passages/eight initial synthesis passages configurable;
they do not limit the final top-ten entity evaluation. Sufficient supporting
evidence and the official retrieval target remain the acceptance criteria.

**Proposal:** implement orchestration and typed records in `src/`, sharing the
Phase 1 schema/repository layer. Use a small web interface with backend job
status and durable case state; choose the frontend framework during
implementation. Keep model credentials server-side and out of stored prompts,
exports and logs. Use the required `LLM_*` configuration names.

Logical modules: intake/parser adapter, case repository, interpretation,
company research, memory client, matching/validation, result presentation and
PowerPoint export. These can run in one application; separate services are not
necessary for the pilot. Enforce per-case authorization and access-aware caches.

Apply time/call budgets, cancellation and bounded retries to model/research
steps. Preserve partial results with explicit limitations. Record token usage
and latency where the endpoint exposes them. Budget prompts with Phase 1's
matching tokenizer/processor and reserve output capacity; selected spans should
replace arbitrary truncation. Schema validation is required even if the endpoint
advertises structured output.

## 10. Build sequence and acceptance tests

1. **Memory integration and text intake:** consume a fixed Phase 1 snapshot;
   create cases, submit permitted text with Enter and show staged progress.
   Exit: result citations round-trip to exact evidence through shared contracts.
2. **Interpretation and company research:** validate contextual classification,
   identity resolution, user correction and connected/offline behavior.
   Exit: ambiguous identities never acquire the wrong company's profile.
3. **Matching and case retrieval:** implement both expertise searches and the
   historical-case path. Exit: source-backed structured results, explained
   scores and distinct unavailable/no-match/partial-coverage outcomes.
4. **Attachments and review:** add the documented formats, OCR/visual capability
   only when verified, selections and revision invalidation. Exit: attachment
   provenance survives retrieval and cross-case access tests pass.
5. **Presentation:** qualitative impact, source manifest and editable PowerPoint.
   Exit: every exported factual claim resolves to reviewed evidence and rendered
   slides pass visual QA.
6. **End-to-end evaluation:** freeze taxonomy/corpus/query versions, compare
   lexical baseline and enriched retrieval, and report observed results using
   [EVALUATION.md](../challenge/EVALUATION.md).

Required scenarios include synonym and misleading-keyword inputs, negation,
multiple needs, duplicate company names, missing websites, unsupported files,
scans with failed OCR, malicious source instructions, no prior-case dataset,
no-match, stale/conflicting affiliations, missing contacts, partial institutions,
model timeout, user corrections, concurrent isolated cases and unsupported
economic forecasts. Test scores without presenting them as probabilities.

Measure recall@10 against independently checked experts/units, claim support,
supported-field completeness, coverage of all three families, case isolation,
latency/cost and export traceability. The official 80%-in-top-10 and complete
traceability targets remain targets until measured; taxonomy classification
accuracy alone does not prove useful matching.

Additional dialogue acceptance checks: a focus change persists through retrieval
and exported slides; a shorter wording request does not trigger unnecessary
recrawling; new facts require new evidence; retained claims keep citations;
ambiguous edits trigger a targeted follow-up; answering resumes the correct
checkpoint; declined/unanswered questions remain unknown; stale replies cannot
overwrite newer revisions; a revised report invalidates old export selections
as appropriate. Measure both initial and revised outputs on the same pinned
snapshot unless a refresh is explicitly recorded.

## 11. Joint integration gate and unresolved dependencies

Both phases are ready to integrate when one permitted case can pin a snapshot,
use its taxonomy, resolve a company or disclose ambiguity, retrieve evidence
across the required ecosystem, explain matches, handle the previous-case branch
honestly and export selected supported claims without losing provenance.

Missing historical cases should disable that branch transparently, not block
expertise search. Missing company facts should yield partial context, not a
fabricated description. Missing required institutional coverage must remain a
visible acceptance failure.

Endpoint access and deployment/hardware decisions will be supplied by the user
before development; do not guess them or repeatedly request them during planning.
Use [PILOT_SCOPE.md](../challenge/PILOT_SCOPE.md) for the selected languages, source focus and
macro Recall@10 acceptance protocol. Remaining choices include verified
tokenizer/modality capabilities, taxonomy content, permitted historical data,
research provider, file parsers and presentation implementation. Keep
connected research separate from an optional demonstrated disconnected runtime.
Record choices in [DECISIONS_AND_OPEN_QUESTIONS.md](../project/DECISIONS_AND_OPEN_QUESTIONS.md).
