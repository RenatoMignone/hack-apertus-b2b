# End-to-end case and report processing

**18 October 2026 · Integrated implementation; live deployment still pending.**
HTTP frontend/API, LangGraph, reasoning/retrieval adapters and PDF are implemented.
See [integration evidence and remaining gates](../team/INTEGRATION.md). Synthetic
cross-lane tests do not establish model quality or a working shared-host deployment.
This document owns the processing stages; [architecture](ARCHITECTURE.md) owns
pack content, [physical schema](../data/RELATIONAL_SCHEMA.md) owns storage.

Schema contract v1 was finalized at 0005; additive runtime/UI changes advance head
through `0007_frontend_lifecycle`; live captures advance head to `0008_live_corpus`.
Corpus/retrieval agents start
with the [data handoff](../data/INGESTION_RETRIEVAL_HANDOFF.md); use the
[exact field reference](../data/SCHEMA_REFERENCE.md) for queries. The pack owns
match output; reason selections own editorial review; durable stage outputs own
query plans and retrieval observations.

## Execution and ownership

1. **Intake:** persist the permitted message as an immutable input revision.
   Confidential one-pagers/business plans remain outside the application.
2. **Interpretation:** Apertus reads the full intent and reviewed, versioned
   taxonomy. Return `CaseInterpretation`: company name (nullable), one-sentence
   summary, primary/additional fields, 2–3-word activity label, Bern intents,
   needs, concepts/search terms, constraints, operator leads and ambiguities.
   Preserve original wording, priorities and negations; the activity label is not
   the retrieval query. Initial field codes: `medtech`, `biotechnology`,
   `pharmaceuticals`, `digital_health`, `healthcare_services`, `other`, `unknown`.
   These extensible labels do not imply corpus coverage beyond the pilot.
3. **Clarification:** missing capability/intent or material ambiguity pauses the
   dependent workflow for a targeted answer. Missing company name or optional
   context does not block. Validation errors concern malformed input; an unknown
   fact is not a technical error. Store input-span attribution separately from
   public factual support; operator leads are unverified until researched.
4. **Research:** independent PostgreSQL full-text + pgvector branches, RRF and
   reranking; reliable explicit metadata constraints apply to both. In connected
   mode run bounded public web discovery/fetch in parallel; offline disables it.
   See [web research](../data/WEB_RESEARCH.md) for source flags/deduplication.
5. **Evidence preparation:** expand support around relevant entities/passages;
   extract atomic claims in bounded evidence batches, then assess semantic
   support, need-to-capability fit, contradictions and gaps. Code checks IDs,
   membership, exact Unicode slices and hashes. Reranking is not validation.
   Novel follow-up queries derive from assessed/extraction/fit gaps, including partial
   matches; preserve earlier evidence/claims and stop if no novel query is supplied.
   At most three research rounds and one structured-output repair per task;
   deadline/token/tool budgets belong to the pinned run configuration. Exhausted
   budgets yield explicit gaps/partial output. Never invent a missing field.
6. **Pack:** code assembles and freezes `ReportEvidencePack` from validated claims,
   matches, attributed input, arguments/gaps and literal support. Its evidence is
   the union of a pinned published snapshot and an immutable case-local manifest.
   Development live mode may instead use an immutable case-owned capture of ready
   authorized corpus chunks while ingestion continues; it requires no publication.
   See [live runtime](../data/LIVE_CORPUS_RUNTIME.md). No-match/partial packs may
   have no public claims, with an explicit limitation.
   A model cannot assign authoritative source metadata or quotation offsets.
7. **Draft:** Apertus receives only the frozen pack and writing instructions.
   Produce concise `Why Bern?` reasons, direct/adjacent labels, entries and claim
   references. Draft persistence requires a supported assessment of its exact content hash.
   Code checks citation membership and literal support; semantic
   assessment confirms wording is entailed. Missing support routes to evidence
   preparation/new pack, never silent browsing by the writer.
8. **Review:** publish an immutable draft revision. The operator keeps/rejects
   each reason card. Rejected means editorially excluded, not factually false.
   `none` means unreviewed. Factual assessments and editorial decisions are
   separate records. Unsupported statements cannot become facts by approval.
9. **Export:** all cards reviewed and at least one kept; freeze an accepted review
   of the exact result hash and selection hash. PDF first, editable PowerPoint
   later with challenge-only assets. Include kept claims, sources and material
   caveats. The deterministic renderer uses no model or retrieval to add facts.

## Model boundaries and contracts

Use focused stages: interpretation/query planning; batched claim extraction;
claim/fit assessment; draft synthesis. Neither one enormous call nor one call per
field is the default. Code assembles identifiers, dates, provenance, manifests and
hashes. Validate Pydantic outputs and bound repairs; grammar-constrained output
is endpoint dependent, not assumed. The current connected environment explicitly selects Apertus 70B; 8B remains
configurable and both use the same evidence checks. There is no automatic fallback. U9 supplies [Keera model aliases/base URL](../data/INFERENCE_CONFIGURATION.md)
and the [EmbeddingGemma 2 reference](../data/EMBEDDING_DEPLOYMENT.md); exact revisions,
compatible runtimes and authenticated limits remain open. Embeddings/reranking use their
own compatible models/tokenizers.

LangGraph coordinates every agentic branch, join, tool budget, revision
and interruption; LangChain provides model/structured-output/tool adapters.
Apertus tool-selection calls use non-thinking mode: the current model card says
thinking mode cannot be combined with tool calling. Benchmark on representative
cases before claiming a model can reliably fill the pack.

`SupportedClaim` contains text, evidence IDs, direct/adjacent kind and a supported
assessment. `DraftReason` links a headline/line and entries to claim IDs.
`ReportEvidencePack` contains attributed intent, supported claims, matches,
argument candidates, gaps/actions, coverage and pinned configuration references.
References must resolve to accessible evidence in its snapshot/manifest. Keeping
raw structured fields does not establish semantic truth; model-backed assessment
adapters record explicit assessments whose quality still requires evaluation.

## Chat and revisions

- Wording only: reuse the pack; revalidate draft wording and create a result revision.
- New focus/facts: new input/query plan, retrieval and pack; old artifacts remain historical.
- Identity/objective changes: reinterpret and invalidate dependent outputs.
- Preserve a card selection only when its content **and support** hash is unchanged.
  Changed/new cards become `none`. An unchanged card ID alone is insufficient.
- Review/export binds exact revision/hash and selection set; subsequent selections
  invalidate the old approval for new exports. Stale answers/results cannot win.

## Frontend and implemented HTTP projection

Keep the existing `BriefRevision`, `Reason`, `ReasonEntry`, `Evidence`, `Coverage`
and `SearchTrace` projections. Each reason has underlying atomic claim links;
`CitedText.evidenceIds` is their deduplicated support. Evidence shows a literal
excerpt/highlight, original URL, title, fetch/publication dates, source origin and
review status. Source badges and the HTTP adapter are implemented. Sankey links reflect
actual recorded input → concept → evidence decisions, not a generated story.
Case statuses describe the business lifecycle; run stages describe execution.
Similar-case scores remain unavailable without an authorized dataset/method.
The [HTTP handoff](FRONTEND_BACKEND_API.md) defines the implemented endpoints.

## 19 October implementation additions

Display-label formatting cannot abort research: overlong labels use a neutral
short label with the entire scientific phrase preserved in search terms. Public
unknowns use `research_questions`, not blocking clarification about the user's
intent. Extraction is bounded into literal batches and all exclusions are explicit.

Need-fit proposals precede the final authoritative pack freeze, allowing novel
gap-driven rounds without drafting interim packs. Actual query/evidence lineage is
stored by code in pack coverage. It resolves exact canonical mirror identities;
the writer's trace stays empty. [Branch evidence](../team/BACKEND_RESEARCH_COMPLETION.md)
and [reranking setup](../data/RERANKING.md) distinguish tests from live acceptance.

Need-fit calls use canonical support for accepted claims, not the entire retrieval
pool. Follow-up planning compares remaining time with the observed preceding-round
cost and reserves 120 seconds for finalization/drafting; if time is insufficient,
it preserves supported partial/no-match work with an explicit limitation. This is
a conservative planning default, not a measured performance optimum.
