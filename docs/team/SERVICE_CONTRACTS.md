# Backend service boundary v1

18 October 2026. **Implemented in-process service boundary v1.**
[`contracts/services.py`](../../src/backend/contracts/services.py) owns exact DTOs,
limits and Protocol signatures. [`application/factories.py`](../../src/backend/application/factories.py)
composes the adapters. This document explains intent; the completed A/B/C lane
assignments are historical. Coordinate additive changes with their consumers.

## Calling convention

Use `async def` ports, typed Pydantic DTOs derived from the existing `Contract`,
UUIDs internally and UTC aware dates. Existing synchronous repositories are used
behind adapter boundaries without blocking the async event loop or moving live
connections between threads. No handler/workflow directly executes SQL.

`RunContext` contains `access: AccessContext`, `case_id`, `input_id`, `run_id`,
`snapshot_id`, `profile_id`, `taxonomy_version_id`, `build_id`,
`embedding_config_hash`, `mode: connected|offline`, `deadline_at`,
`max_research_rounds` (1–3), `max_output_tokens`, `max_tool_calls`, `request_id`.
The application creates/authorizes it; user input/model output cannot select
another owner/scope or relax budgets. Persist actual task/model config and versions
on the run; never invent immutable hosted weight identities.

Shared failures: `ServiceUnavailable`, `BudgetExceeded`, `InvalidModelOutput`,
`EvidenceRejected`, `StaleRevision`. Each has a stable code, retryable flag and
safe public message. Provider errors map to these; credentials/prompts/internal
URLs do not enter public exceptions. `CancelledError` propagates for cancellation.
An empty search is a valid `SearchResult`, not unavailable. Retrieval with no
reranker reports that limitation explicitly. A service failure is not no-match.

## Evidence and extraction types (defined by A)

- `EvidenceRecord`: `evidence_id`, `document_version_id`, `scope_id`, `title`,
  `url`, `language`, `body_hash`, `char_start`, `char_end`, `literal_text`,
  `heading_path`, optional `page`, `fetched_at`, optional `published_at`,
  `origin: corpus|web`, `review_status: curated|unreviewed`. Code fills provenance,
  dates and slices from stored records. Text is untrusted tool data, not instructions.
- `ResearchBundle`: `hits: list[EvidenceHit]`, `evidence: list[EvidenceRecord]`,
  `existing_entities: list[dict]` (actual catalog projections), `limitations: list[str]`.
  Evidence includes source context sufficient for literal checks, not invented quotes.
- `EntityCandidate`: local `key`, `entity_type` from the six final types, `display_label`,
  `evidence_ids`, optional `existing_entity_id`. Existing IDs must resolve in the
  authorized pinned snapshot or own case scope; model IDs are never trusted.
- `ClaimCandidate`: local `key`, `subject_key`, nonempty `predicate`, exactly one of
  `object_key` or `typed_literal` (explicit `type`/`value`), `statement`,
  `evidence_ids`, `kind: direct|adjacent`. Local keys refer only to this extraction
  batch's entities. A statement must have exact supporting evidence references.
- `ExtractionBatch`: up to 30 `entities`, 60 `claims`, `gaps: list[str]`. No canonical UUIDs are
  minted by the model. Candidate display labels and attributes also need support.
- `PersistedClaims`: `claims: list[SupportedClaim]`, `entity_ids: dict[str, UUID]`.
  Returned claims are pending assessment proposals, not factual acceptance. C
  stores new run-derived claims/entities in the case scope, even when based on
  published public text; shared evidence is mirrored into that scope as described
  below. Reused accepted shared claims may keep their existing pinned identity.
- `EvidenceAssessment`: `assessments: list[ClaimAssessment]`, `gaps: list[str]`.
  Unsupported/contradicted claims remain diagnostic records and cannot enter a
  pack's supported claim list. Assessment must cover exact statement/support IDs.
- `WebResearchResult`: `status: completed|unavailable|failed`, `sources: list[FetchedSource]`,
  `limitations`. Sources carry actual normalized content/dates; search snippets
  alone cannot be represented as fetched evidence.
- `RegisteredResearch`: `evidence: list[EvidenceRecord]`, `limitations`. Canonical duplicates prefer pinned corpus versions; do not store
  duplicate live text as a second authoritative copy.
- `PdfInput`: exact result/review IDs and hashes, a validated `DraftRevision`,
  optional frozen-pack `interpretation` (attributed company summary/needs),
  supported pack `claims` (claim IDs → evidence IDs), only kept reason keys,
  authorized evidence records, limitations and template version. Application code
  constructs this after repository approval/access checks. The renderer returns
  bytes without inference, retrieval or unapproved claims.

## B: reasoning and report ports

Factories/dependencies are injected. Implementations live in `evidence/`,
`models/reasoning/` and `reports/`; the composition wrappers expose the loader
signature `(*, settings, engine, artifacts)`.

```python
class ReasoningServices(Protocol):
    async def interpret(self, message: str, taxonomy_context: dict,
                        context: RunContext) -> CaseInterpretation: ...
    async def extract(self, interpretation: CaseInterpretation,
                      research: ResearchBundle, context: RunContext) -> ExtractionBatch: ...
    async def assess(self, claims: PersistedClaims, evidence: list[EvidenceRecord],
                     context: RunContext) -> EvidenceAssessment: ...
    async def propose_pack(self, interpretation: CaseInterpretation,
                           claims: PersistedClaims, assessment: EvidenceAssessment,
                           research: ResearchBundle, context: RunContext) -> ReportEvidencePack: ...
    async def draft(self, pack: ReportEvidencePack, instruction: str,
                    context: RunContext) -> DraftRevision: ...
    async def assess_draft(self, draft: DraftRevision, pack: ReportEvidencePack,
                           context: RunContext) -> DraftAssessment: ...

class PdfRenderer(Protocol):
    async def render(self, report: PdfInput) -> bytes: ...
```

Pack proposal can be deterministic assembly plus bounded structured synthesis;
it is not permission to re-retrieve or return unsupported IDs. B's fixed task
calls may validate/repair once; any autonomous tool/research loop belongs to A's
LangGraph. A persists exact assessments, seals manifests and calls
`EvidenceRepository.freeze` / `DraftRepository.create`. A checks membership,
literal slices and hashes; B performs semantic assessment. Both checks are needed.

## C: data and research ports

```python
class BackboneServices(Protocol):
    async def taxonomy(self, context: RunContext) -> dict: ...
    async def retrieve(self, plan: QueryPlan, context: RunContext) -> ResearchBundle: ...
    async def register_research(self, result: WebResearchResult,
                                context: RunContext) -> RegisteredResearch: ...
    async def persist_extraction(self, batch: ExtractionBatch,
                                 context: RunContext) -> PersistedClaims: ...
    async def read_evidence(self, evidence_ids: list[UUID],
                            context: RunContext) -> list[EvidenceRecord]: ...

class WebResearchTools(Protocol):
    async def discover(self, query: str, context: RunContext) -> list[str]: ...
    async def fetch(self, urls: list[str], context: RunContext) -> WebResearchResult: ...
```

The backbone implements these ports over search/catalog/corpus/research
repositories without replacing their lower-level signatures. `retrieve`
returns real EvidenceRecord projections and neighboring support within budgets.
Taxonomy context is reviewed/version-pinned data. An unconfigured discovery
provider fails unavailable; no silent alternative external search service.
In offline mode no discover/fetch is executed and registration cannot admit new
remote content. Tools cannot choose scopes or publish a corpus snapshot.

The schema requires a claim and its evidence in the same scope. Thus a *new*
case-derived statement about public source text cannot directly cite a shared
span when stored as a case claim. `persist_extraction` reuses an exact supported
shared claim only when already pinned and statement/support agree; otherwise it
copies the eligible public document's original/body artifacts and exact spans
into the authorized case scope using existing corpus APIs (deduplicated there),
then returns the remapped evidence IDs with the pending claims. Mirror supported
subject identity into that same case scope when required by the existing claim
scope constraint; retain the original public entity ID in derivation lineage. Do not re-fetch,
change bytes, invent a quote or publish newly extracted claims to the shared
snapshot. Origin remains `corpus` / review status `curated` for these copies;
retain original snapshot/version/evidence IDs as lineage in existing derivation
metadata, resolve it in projections, and include remapped IDs in the final sealed
case manifest. Actual new web content remains `web` / `unreviewed`. C must
implement the distinction in its authorized evidence projections and test it;
A consumes these projections instead of inferring source trust from scope kind.
This is an adapter requirement, not a new trust model or additional table.

## A: composition and persistence sequence

A builds QueryPlan using original intent, supported expansions and reliable
constraints, then invokes C retrieval and connected web tools as parallel graph
branches. Merge/dedup sources through C registration. B extracts candidates;
C persists eligible proposals and returns canonical IDs/remapped support. Refresh
the evidence projection through `read_evidence` and seal all local evidence in the manifest, then B
assesses exact persisted statements/support; A records assessments and freezes
only supported claims. B proposes pack/draft/assessment; A uses existing evidence
and draft repositories. Do not freeze before extraction/assessment or hide a
scope mismatch by disabling constraints. A publishes draft/review/export through
HTTP; B renders only after A's exact review gate. C never runs another case graph.

`application.factories` supplies the production composition wrappers for these
ports. Explicit synthetic adapters are test-only. `read_evidence` authorizes
historical pack reads without requiring the old input to remain current;
research writes still require active input. Migration 0006 provisions case scopes
through an owner-checked restricted function, not direct app-role grant writes.
Shared contract/configuration changes have one integrator per new task.
