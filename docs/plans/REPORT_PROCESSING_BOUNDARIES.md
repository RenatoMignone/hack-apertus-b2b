# Retrieved evidence, ReportEvidencePack and final output

**18 October 2026 · Boundary agreement; detailed processing remains unmapped.**
U7 reserves further design for both transformations. Existing plans describe
intended capabilities, not a completed algorithm or working path. This document
allocates ownership without selecting a scraper, prompts, models' exact sources,
intermediate schemas or report-generation library.

```text
Acquisition / scraper (deferred)
  → normalized, source-located records → published snapshot
  → query-time retrieval (data/retrieval)
  → retrieved EvidenceHit / EntityHit and provenance
  → evidence preparation (evidence)                 [mapping still needed]
  → frozen ReportEvidencePack
  → report generation + checks + review (reports)   [mapping still needed]
  → reviewed report revision → rendering → final artifacts
```

Source acquisition and query-time retrieval are distinct. Hits, URLs, a reranked
answer or a checkpoint are not a report evidence pack. Workflows coordinate
handoffs; HTTP exposes authorized progress and resource views to the frontend.

## Boundary A: retrieval → ReportEvidencePack

**Owning code location:** `src/backend/evidence/`. Inputs: full versioned user
intent, company context, retrieved records, supporting evidence references and
pinned run/snapshot/model/profile identities. Retrieval payloads follow
[ingestion §7](INGESTION_PLAN.md#7-shared-contract-v1--owned-here-consumed-by-phase-2)
and [retrieval](../data/RETRIEVAL_SPEC.md). Reranking is relevance, not factual approval.

`ReportEvidencePack` is the set of source elements, facts and supported derivations
needed to build the report. Content authority remains
[architecture: evidence pack](ARCHITECTURE.md#evidence-pack-the-report-generation-gate),
with persistence in [case state](../data/CASE_STATE_AND_LINEAGE.md). It includes:

- Current permitted intent, attributed company input, supported company facts
  and explicit unknowns.
- Needs and supported people/unit/capability/project/service matches, keeping
  direct and adjacent interpretations distinct.
- Literal evidence and claim references, public URLs/input locators, source dates,
  coverage/failures; original material sufficient to verify derived statements.
- Labeled argument derivations, constraints, contradictions, gaps and actions.
  Optional numerical/scenario/historical material only when eligible.
- Run/input/snapshot/case-manifest/profile/configuration IDs, validation state,
  manifest/hash and explicit partial/no-match limitations.

Store durable references plus eligible literal support per the owning contracts.
The pack is not a duplicate corpus or unconstrained prompt dump. Freeze before
writing; changed support creates a new pack revision. Revocation overrides access.

**Still to map:** intermediate DTOs, identity/deduplication rules, evidence
expansion, factual/semantic validation stages, need-to-capability links,
contradiction resolution/review thresholds, completeness rules, optional
calculations, token budgets and exact conditions for asking/searching again.
[Phase 2 preparation](OPERATIONS_PLAN.md#3-prepare-the-case-evidence) informs this
design; its high-level table is not implemented processing.

## Boundary B: ReportEvidencePack → final output

**Owning code location:** `src/backend/reports/`, separated into generation,
validation and rendering. Inputs: frozen eligible pack, output settings,
permitted writing instructions and reviewed selections for export. Report
sections remain [output structure](OUTPUT_REPORT_STRUCTURE.md).

The intended boundary is pack → structured revision → claim/citation checks →
human review → rendered report/slide artifacts. Drafts are not approved exports.
The writer cannot silently retrieve facts, promote hypotheses to evidence or
overwrite its pack. Missing support becomes a gap/escalation back to evidence
preparation with a new revision when needed.

**Still to map:** section-level DTOs, content planning, prompts/tasks, deterministic
versus model checks, repair/retry rules, citation placement, operator review,
selection/edit invalidation, report job/run lineage, renderer/library choice,
slide-template mapping and artifact checks. No detailed generation graph or
renderer has been selected by this scaffold.

## Future handoff acceptance criteria

| Handoff | Invariant |
| --- | --- |
| Retrieval → evidence preparation | IDs, locators, literal support, permissions, revisions and uncertainty survive |
| Evidence preparation → pack | Facts resolve to support; input/hypotheses stay labeled; intent/exclusions and gaps survive |
| Pack → report | Hash/versions pinned; factual assertions resolve to accepted support; no new unsourced facts |
| Report → review/export | Exact revision, selections and review bound; citations/caveats survive rendering |
| Edit/restart/cancel | Existing [case recovery/invalidation](../data/CASE_STATE_AND_LINEAGE.md) applies; stale outputs cannot replace current work |

These are future acceptance criteria, not completed tests. Settle Boundary A and
Boundary B separately with worked examples/schema proposals before implementation.
Scraper choice and acquisition behavior remain a separate deferred workstream.
