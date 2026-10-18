# Hybrid retrieval and model handoffs

**18 October 2026 · Selected algorithm design; budgets require pilot validation.**
Storage: [relational schema](RELATIONAL_SCHEMA.md). Logical search functions:
[Phase 1 section 7](../plans/INGESTION_PLAN.md#7-shared-contract-v1--owned-here-consumed-by-phase-2).
No model repository, download source, endpoint or tokenizer implementation is
selected here. The named model roles are in [build and operations](BUILD_AND_OPERATIONS.md).

Read the [ingestion/retrieval handoff](INGESTION_RETRIEVAL_HANDOFF.md) for actual
repository calls, joins and write order. Use the [exact field reference](SCHEMA_REFERENCE.md);
removed plan/hit/match tables are not query targets. Plans/results can be persisted
in durable stage outputs using the existing DTOs.

## Query contract

`QueryPlan` carries the full permitted request, case/input revision, verified or
attributed company context, needs, priorities/exclusions, ambiguities, original
wording, generated query variants, proposed concepts with mapping kind, reliable
filters, access context, profile/taxonomy/snapshot/build IDs and budgets.

Apertus interprets context and consults the versioned vocabulary. It does not
force one company into one topic or silently turn a related technology into an
explicit company need. Ambiguity requiring a different search triggers a focused
question. Company identity uncertainty does not block a clear capability search.

Use the original query plus a few complementary formulations. `CGM` and its
reviewed long form may be aliases; broader biosensing is a discovery expansion,
not proof of identical expertise. Preserve negation as an explicit constraint;
do not feed an excluded keyword into lexical search as a positive requirement.

## Retrieval stages

1. Resolve authorization and pin a published snapshot once. Candidate eligibility
   is shared across lexical/vector branches: scope, snapshot membership, compatible
   embedding build, access and explicit reliable constraints. Inferred topic labels
   are optional hints. Unknown location cannot be silently treated as verified Bern
   location, but hard document-location filters must not hide relevant evidence
   that could establish geography through an entity or neighboring page.
2. Embed each contextual query using the same configured embedding space as its
   corpus build, with the appropriate query template. Retain original intent for
   reranking. Do not use Apertus token IDs as embedding-model inputs.
3. Run PostgreSQL full-text and pgvector cosine retrieval independently over
   eligible candidates. Keyword results do **not** gate the semantic branch.
4. Fuse ranks, deduplicate overlapping chunks and rerank bounded query/passage
   pairs with the BGE reranker. Retain separate score components and IDs.
5. Aggregate candidates into unique typed persons/units, obtain supporting
   profiles/projects and neighboring spans, and validate factual/constraint fit.
6. Close material gaps with bounded revised queries or eligible connected fetches;
   otherwise return supported partial/no-match results and coverage limits.

## Lexical branch

Store a `tsvector` generated from original title, headings and body, with title/
heading/body weights A/B/D as initial settings. Use a GIN index for matching and
`ts_rank_cd` for ranking. PostgreSQL built-in full-text ranking is **not BM25**.
Ignore opaque IDs/hashes when building searchable terms. Reviewed aliases may
be an additional low-weight field; keep generated labels out of literal evidence.

Use language-specific text-search configurations where supported, with matching
query configuration per language. Unknown/unsupported language uses `simple`;
names/acronyms may need a separate `simple` projection. Include a chunk once per
branch after deduplication, even if multiple projections/queries retrieve it.
Translate lexical query variants only as labeled search aids; preserve original
DE/FR/IT/EN text. Multilingual vector retrieval is evaluated separately.

## Vector branch and fusion

Use the configured dense vectors and cosine distance (`<=>`); lower distance
ranks first. A tokenizer splits input; it does not replace the embedding worker.
Query and document templates may differ by role, while sharing model/config/
normalization/dimension. Never mix embedding configurations or silently truncate.
Reject non-finite, wrong-dimension or zero-norm vectors before cosine retrieval.

Start with exact filtered search for the small pilot. If HNSW is introduced,
test filter selectivity and candidate recall: approximate scans can yield too few
eligible results after filtering. Configure adequate scanning/candidates or use
exact search on the authorized subset. Never broaden authorization to fill a list.

Proposed default: gather 30 candidates per branch across the bounded query
variants. For each chunk take its best rank within each branch, then use:

```text
rrf(chunk) = 1 / (60 + best_lexical_rank) + 1 / (60 + best_vector_rank)
```

Ranks start at one; an absent branch contributes zero. This avoids adding scores
with incompatible scales and stops many near-identical expansions from voting
repeatedly. Keep the top 30 fused unique chunks initially; expand within budgets
when entity/support coverage is inadequate. Constants are profile configuration,
not measured optimum. Use deterministic tie-breaking by stable chunk ID.

## Rerank, entity aggregation and support

Rerank the original contextual need against each original passage plus clearly
separated heading context. Record pair-token counts and any bounded window with
its evidence offsets. A reranker is not an embedding encoder or a fact checker.

Entity ranking starts from the strongest supported reranked passage per entity;
do not reward a professor simply for having more duplicate profiles. Add only
documented, versioned relevance adjustments after evaluation. Fetch evidence for
role/affiliation/capability and projects/services where available. Same names do
not justify merging. Return up to ten unique typed entities for pilot Recall@10;
passages, projects and cards are not substitute entity counts.

Code checks IDs, literal spans, scope and revisions. Semantic assessment checks
whether evidence supports the claim and whether it fits the intended need.
Unknown contacts/services stay null; adjacent applications stay hypotheses.
Reranking/contextualization cannot eliminate this validation gate. Do not require
a second full browsing pass or extra model call for every passage by default.

Initial maximum is three retrieval rounds, with separate time/token/call limits.
Eight passages is a starting synthesis budget, not an eight-entity result cap.
Expand the pack within model limits or surface the limitation. Record reasoned
evidence strength separately from match relevance; none is a calibrated probability.

## Connected extension and response

Air-gapped mode cannot browse. Connected mode may fetch an eligible missing or
freshness-sensitive page through the collection policy, normalize/validate it,
and add it to the case evidence manifest. Unverified search snippets/URLs remain
leads. The shared snapshot is unchanged until a separate publication succeeds.
External origins undergo scope/access checks; actual ambiguity requires review,
not blanket manual approval of every permitted page.

Search results include source/evidence/entity IDs, original text/locators, dates,
component scores, ranking version, snapshot/build, coverage and limitations.
The model cannot know that an unindexed expert does not exist. Measure corpus
coverage separately from retrieval quality, with the [evaluation protocol](../challenge/EVALUATION.md).

## U8 connected branch

Case-time [web research](WEB_RESEARCH.md) runs beside hybrid DB retrieval only
when connected. Merge canonical URLs with the whole pinned corpus and preserve
corpus versions. New case-local evidence requires literal checks and explicit
claim assessments before pack assembly; it is flagged even when supported.
The taxonomy's short activity label never replaces full intent in either search
branch. Existing independent lexical/vector fusion and budgets remain active.
