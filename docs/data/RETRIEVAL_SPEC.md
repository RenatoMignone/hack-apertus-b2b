# Hybrid retrieval

`HybridSearch.search(access, QueryPlan)` searches a pinned authorized snapshot/
build. Plans preserve the full permitted request, original terms, negation,
constraints and supported concept/alias expansions. The first plan can use the
original query plus bounded variants; gap revisions add at most five novel variants.
Exact DTO limits live in `contracts/data.py` and `contracts/services.py`.

## Search sequence

1. Resolve access, snapshot membership and exact embedding configuration.
2. Encode bounded query inputs with the same compatible encoder configuration as
   ingestion; batch where supported.
3. Run full-text and vector branches independently against eligible membership.
   Authorization/language/explicit reliable constraints apply; topic labels and
   keyword hits cannot exclude otherwise eligible vector matches.
4. Fuse unique chunk ranks using reciprocal rank fusion, deterministic tie-breaking
   and bounded candidates. Optionally rerank original passages against full intent.
5. Expand bounded supported entity/neighbor context, then return actual evidence,
   IDs, source locators, query lineage and limitations.

Lexical search uses PostgreSQL `tsvector` / `tsquery` with GIN support and
`ts_rank_cd`; it is not BM25. Constant language-specific query construction avoids
rebuilding a query per row. Dense search uses pgvector cosine distance; only
compatible vectors are comparable. An ANN index must preserve eligible recall
under filtering; never widen authorization to fill candidates.

For each chunk, fuse its best rank within each branch:

```text
RRF = 1 / (60 + best_lexical_rank) + 1 / (60 + best_vector_rank)
```

Ranks start at one; missing branches contribute zero. Duplicate expansions do
not vote repeatedly. Candidate/window limits are explicit configuration, not
measured universal optima. The reranker has a separate tokenizer and its scores
measure relevance, not factual support. [Reranking](RERANKING.md) specifies windows.

## Evidence and iteration

`EvidenceHit.query_matches` records actual retrieval queries and branches;
`reranker_windows` records composed scoring windows. The workflow maps real hits
to canonical evidence in frozen pack coverage. Unobserved ontology paths remain
absent. Title/heading hints guide discovery; public assertions still need exact
body passages and semantic assessment.

Connected web research runs in parallel, followed by canonical deduplication.
New material remains flagged/case-local. A bounded gap stage proposes novel
queries from assessed omissions while preserving earlier evidence. Stop when
budgets/finalization reserve are insufficient; return supported partial work.

Measure unique experts/units rather than counting duplicate passages or cards.
[Evaluation](../challenge/EVALUATION.md) compares lexical/dense/RRF/reranked
variants under identical pins. [Performance](CAPTURE_PERFORMANCE.md) separates
query cost, authorization/membership, encoding and source registration.
