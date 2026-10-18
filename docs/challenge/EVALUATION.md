# Evaluation plan and evidence requirements

**Status: proposed protocol; no evaluation has run and no performance is claimed.**

**18 October decision:** the user delegated aggregation/entity counting. Use
intent-balanced macro Recall@10 >= 0.80 for the English positive-query suite as
the internal primary gate, with unique typed person/unit IDs in one shared top
ten. Average frozen wording variants within each intent, then average intents;
report per-variant, per-type and micro diagnostics. Assess DE/FR/IT extensions
separately. Full details and broad-query handling are in
[PILOT_SCOPE.md](PILOT_SCOPE.md#evaluation-decision). This is our operational
definition, not an organizer-supplied aggregation clarification.

The numerical targets come from [B1 §4](CHALLENGE_BRIEF.md); the recordings supply
no labeled evaluation dataset and suggest constructing a pilot or synthetic
examples. [E20](../recordings/RECORDING_INSIGHTS.md#e20--evaluation-needs-to-be-constructed)

## Official targets versus proposed measurements

| Requirement | Proposed measurement | Interpretation/limit |
| --- | --- | --- |
| At least 80% of expected experts/units in top 10 | Per-query recall and primary intent-balanced macro Recall@10 >= 0.80; micro/type diagnostics | Aggregation defined under user delegation; not an official organizer formula |
| Equivalent wording finds the same experts | Expected-set recall for paired terminology variants; optionally top-10 set overlap | Same-intent pairs share gold entities; broader related terms need separate judgments |
| 100% traceable source-supported results | Result-level supporting-link rate and factual claim-support audit | A valid/reachable URL alone is insufficient; a supported name does not validate all of a result's roles/projects |
| Structured results where source provides fields | Supported-field completeness, missing-value accuracy, unsupported-field count | Judge availability from checked source material; do not reward fabricated completeness |
| All three source families covered | Collected/extracted/indexed counts plus actual retrieved evidence per family | Document overlap and failures; three configured seeds alone do not demonstrate coverage |
| Easy extension | Add a verified institutional source through documented configuration/short step | Record actual changes and observed result; do not claim extensibility from design alone |
| Fair discoverability | Audit coverage and retrieval by institution/group, including less prominent units | Diagnostic fairness evidence; no official numerical fairness threshold is supplied |

For query `q`, with independently verified expected entities `G(q)` and up to
ten **unique** returned entities `R10(q)`:

```text
Recall@10(q) = |G(q) ∩ R10(q)| / |G(q)|
Macro Recall@10 = mean of Recall@10(q) over positive queries
Micro Recall@10 = sum of matched expected entities / sum of expected entities
```

The plain per-query macro above is a descriptive diagnostic when wording variants
are listed individually. The selected primary gate groups variants within each
intent first, as specified in PILOT_SCOPE; label both aggregates explicitly.
Use the same frozen variant suite when comparing systems.

Use typed entities in the shared top ten, and report separate person/unit
diagnostics where their gold subsets exist. Do not count one unit as every
expected person within it. Duplicated
profiles do not create extra hits. Queries with no gold match are assessed for
abstention separately, not divided by zero or counted as perfect recall.

If a query has more than 12 expected entities, a top-10 list cannot reach 80%
recall. Surface that mismatch, report the attainable bound and resolve the
intended query/granularity with the partner; do not cherry-pick gold labels to
make the target achievable. Unjudged novel results are **unjudged**, not
automatically incorrect; audit them before revising a versioned expected set.

## Build a small defensible pilot

1. **Fix the scope and snapshot.** Use the selected diabetes-technology topic;
   name source families,
   collection dates, indexed pages and coverage exclusions.
2. **Create query cases.** Start with C01–C13 in
   [WORKFLOWS_AND_CASES.md](WORKFLOWS_AND_CASES.md), including same-intent pairs,
   related concepts, multiple result types, ambiguity and negative cases.
3. **Check expected results independently.** A person/partner reviewer should
   validate real identities, types, roles and relevance from public evidence.
   Record who/which reviewer role judged them and uncertain labels. Model-generated
   expected answers alone are not ground truth.
4. **Separate tuning from final checks.** Keep a small held-out query set if
   feasible. Freeze query/gold versions before the reported run; disclose any
   source-driven gold revisions.
5. **Run a baseline and the selected system.** Use the same corpus, expected
   entities and timing boundary. Record lexical baseline behavior before
   attributing improvements to Apertus or semantic retrieval.
6. **Audit all returned results in the small pilot.** Check links and actual
   field/claim support; human-review adjacent-application explanations and
   understandable wording.
7. **Report exact counts and failures.** Publish measured values only where
   tested, with sample size, protocol and limits. A small synthetic-query pilot
   is preliminary evidence, not proof of production-wide 80% recall.

Suggested case record: case ID, intent, synthetic/public input provenance,
query/variant group, expected typed entity IDs, supporting URLs/passages,
relevance labels, corpus/version, reviewer/date and unresolved judgments.
Use real verified expertise even when the company/query is synthetic.

## Reliability and workflow checks

Proposed checks beyond the formal metric wording:

- **No-match discipline:** test a known-unrepresented capability in the fixed
  corpus, a wrong-region request and a broad medical question. Avoid asserting
  that the capability is absent from all of Bern.
- **Field/evidence behavior:** missing contacts, similarly named people,
  cross-listed profiles, stale/conflicting affiliations and inaccessible pages.
- **Bounded inference:** confirm that related technologies remain suggestions,
  with no invented completed applications, clinical claims or availability.
- **Source safety:** if agent tools are used, test that instructions embedded
  in page content cannot override the evidence-only task or tool boundaries.
- **Usability pilot:** ask a business developer to identify relevant items from
  a public/synthetic brief; note readability, selection effort and irrelevant
  matches. A proposed keep/reject UI need not exist to conduct this review.
- **Performance/cost:** measure collection separately from query time, report
  latency distribution and query/model-call volume for the pilot, and label
  hardware/hosting costs as measured or estimated. About 300 cases/year is not
  300 queries/year and provides no measured time-saving estimate.
- **Deployment:** reproduce a clean run with the documented dependencies. Test
  network-disabled execution only if claiming air-gapped runtime; use actual
  hosting evidence for an independent/Swiss-cloud claim.

## Evidence for the six main-jury dimensions

M1 lists six dimensions scored **0–5**. It provides no weights. The older
photographed Finals-slide summary gives useful questions but does not override
this local scoring-scale statement. Stage-specific details remain unverified.

| Dimension | Evidence to prepare | Current status |
| --- | --- | --- |
| Purposeful use of AI | Observed Apertus contribution and comparison/justification for its chosen role | Not assessed; implementation absent |
| Technical rigour | Reproducible working pipeline, pilot metrics, evidence audit and known failures | Not assessed |
| Value, cost & scalability | Operator benefit, measured/estimated costs with assumptions, coverage/extension behavior | Stakeholder need documented; product evidence absent |
| Sovereign deployability | Selected target, full dependency map and verified operation for claimed mode | Air-gapped primary design proposed; no deployment tested |
| Implementation feasibility | Run instructions, data/rights boundary, maintenance and partner handoff requirements | Not demonstrated |
| Pitch & presentation | Clear, truthful working demo and coherent report/video within actual limits | Not produced |

Do not fabricate internal judge scores or imply that documentation proves a
working prototype. The report should state corpus size/coverage, query counts,
recall protocol, support/completeness results, baseline comparison, cost basis,
deployment evidence and limitations **once available**.

## Architecture extension and deployment checks

Additional user design gates, not new organizer metrics:

- Run a second domain profile with fixtures without changing core orchestration;
  verify different concepts/sources and unknown terms. This proves configuration
  behavior, not second-domain research quality.
- Exercise parser/taxonomy/chunker/embedding changes with staged rebuilds,
  compatible query vectors, publication failure and rollback.
- Verify manual text intake, disabled confidential attachments, intent revisions
  and full evidence-pack → report → export lineage.
- For the proposed air-gapped primary target, cold-start and complete a case and
  export with external networking disabled; inspect attempted egress and absence
  of downloads, external telemetry, CDN, remote vectorizers and model/search fallbacks.
- For any other claimed target, record the actual ownership/administration or
  Swiss operator/jurisdiction/residency and every runtime dependency.

[Architecture/dependency inventory](../plans/ARCHITECTURE.md#target-architecture-mandatory).
No checks in this section have been executed.

## Data-layer implementation checks

The [data-layer specs](../data/DATA_LAYER.md) add concrete acceptance cases:

- Compare PostgreSQL lexical-only, dense-only, RRF fusion and reranked retrieval
  on the same frozen snapshot/gold suite; report relevance and factual support
  separately. Relevant missing-label passages must remain retrievable.
- Start from exact filtered vector search. If adding HNSW, compare entity recall
  under scope/snapshot/language filters and handle candidate shortfalls honestly.
- Preserve run → snapshot/model/query → literal evidence → pack/review → export
  lineage; failed publication cannot replace the active snapshot.
- Resume after a business-state commit but before checkpoint persistence without
  duplicate writes. Reject stale clarification answers and cross-case access.
- Verify local Langfuse correlation/masking, absent usage/cost behavior and bounded
  outage handling. Trace scores are not independent gold judgments or probabilities.
- Restore the database and artifact package, resolve exact citations, and test
  revocation across old snapshots, checkpoints, traces and dependent exports.

These extend engineering validation; they do not add organizer scoring rules.
