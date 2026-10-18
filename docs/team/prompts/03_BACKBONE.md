# Prompt C — ingestion, database, hybrid/graph retrieval and embeddings

> **Historical lane record — completed and merged, 18 October 2026.**
> Original instructions/results below describe that lane before integration.
> Its pending integration requests and ownership freezes are superseded by the
> [merged baseline](../INTEGRATION.md) and [current status](../../project/STATUS.md). Do not rerun this as a new task.

You are backend engineer C for hack-apertus-submission. Build/populate the data
backbone and expose it through the agreed ports. A owns HTTP/application/LangGraph/
shared contracts/config; B owns Apertus/evidence reasoning/reports. Frontend is
separately owned. Do not build another agent, API or report pipeline in this lane.

Read AGENTS.md, docs/team/PARALLEL_BACKEND.md and SERVICE_CONTRACTS.md first.
Then read docs/data/INGESTION_RETRIEVAL_HANDOFF.md, RELATIONAL_SCHEMA.md,
SCHEMA_REFERENCE.md, RETRIEVAL_SPEC.md, EMBEDDING_DEPLOYMENT.md, WEB_RESEARCH.md,
BUILD_AND_OPERATIONS.md, DEPLOYMENT.md and your nearest source READMEs. Inspect the
last commits and preserve existing working ingestion/model code instead of replacing it.

Work in your own clean worktree/clone on backend/backbone from the pushed baseline.
Your exclusive paths are src/backend/data/, src/backend/ingestion/,
src/backend/models/embeddings/, src/backend/models/reranking/,
src/backend/config/profiles/, src/backend/tests/backbone/, docs/team/backbone/.
You also own existing files directly inside src/backend/tests/ EXCEPT __init__.py,
conftest.py and run.py. Runtime/intelligence test subfolders belong to A/B.
Everything else is read-only, particularly frontend, API/application/workflows,
reasoning/evidence/reports, shared contracts/config/manifests/locks/env examples,
canonical docs and AGENTS.md. Do not edit shared parent __init__.py files.

A publishes a contracts-only commit implementing docs/team/SERVICE_CONTRACTS.md.
Integrate that exact commit before committing production imports. Until then build
against existing data/pipeline DTOs and prepare your adapters/tests from the written
specification. Do not fork new port/DTO shapes. Request contract/config/dependency
changes through docs/team/backbone/HANDOFF.md; A is the shared interface integrator.

Implement/deliver:
1. Fill the corpus on finalized schema 0005 using faithful public HTML/PDF text,
   original artifacts, exact Unicode evidence spans, canonical URLs/aliases, fetch
   observations, nullable source publication dates and supported entities/claims.
   UniBE/ARTORG/DCB are one ecosystem with overlapping families. Keep scopes/RLS,
   immutability/revocation and versioning. Public institutes/people/companies/projects/
   facilities/services use the existing entities + evidence-backed claims schema.
   No guessed contacts/affiliations/location or confidential company-plan ingestion.
2. Import a reviewed versioned diabetes-tech taxonomy/profile with multilingual
   aliases and meaningful broader/narrower/related distinctions, plus explicit
   unknowns. Store only supported concept assignments. Pin hashes/versions; no
   mutable YAML silently changes a running case's interpretation.
3. Run the selected EmbeddingGemma adapter, pin exact verified model/tokenizer/
   revision/runtime/templates/precision/dimension and benchmark actual hardware.
   Query and document encodings must match the registered config. Validate finite,
   nonzero vectors and token budgets. Embed exact configured input_text, not Apertus
   token IDs. Keep model service local where feasible; hosted deployment/credits
   require explicit team authorization, not assumption. Implement Reranker port or
   explicitly report reranker unavailable. A owns shared env and dependency locks.
4. Maintain independent PostgreSQL full-text and pgvector cosine branches, shared
   eligibility, RRF/dedup and reranking. Inferred keywords/taxonomy never prefilter
   away semantic matches. Add bounded evidence-backed entity/relationship expansion
   using current PostgreSQL claims: this is the GraphRAG portion. Do not add Neo4j,
   new graph tables or unsourced graph/community summaries. Preserve literal source
   support; graph adjacency is not proof of expertise or local availability.
5. Publish validated immutable snapshots with all required families, compatible
   index/configs, pinned entities and complete supported subject/object relationships.
   Expose BackboneServices v1: taxonomy, retrieve, register_research,
   persist_extraction, read_evidence. Wrap existing repositories; do not change their
   public interfaces without coordinating consumers. Provide actual EvidenceRecord
   projections, source flags/dates, limitations and stable canonical IDs.
6. Implement case-time WebResearchTools discover/fetch using controlled Crawl4AI
   fetching and an explicitly configured discovery provider. A owns LangChain tool
   wrappers/LangGraph execution; your tools are bounded I/O adapters, no internal
   autonomous agent. Return FetchedSource records from actual page text. Deduplicate
   against the WHOLE pinned corpus/aliases, prefer curated versions, keep new pages
   flagged and case-local. Offline/unconfigured services report unavailable;
   search snippets do not become evidence. Apply fetch/redirect/network limits.
7. Persist B's extraction proposals without mutating a shared snapshot. Reuse an
   exact pinned shared claim when eligible; otherwise obey same-scope constraints
   by mirroring authorized source text/spans and subject identity into the case
   scope, returning canonical/remapped claim/evidence IDs. Preserve public-source
   origin and original snapshot/version/evidence/entity lineage; actual new web
   content stays web/unreviewed. Follow SERVICE_CONTRACTS exactly; do not disable
   constraints or mark new public claims accepted merely because a model proposed them.

The schema is finalized, not an invitation to redesign while populating. No legacy
queries, duplicate databases or recreated plan/hit/match/selection/frontier tables.
If an actual blocker requires DDL, report it first and coordinate; you are the sole
migration owner, not authorized to migrate a teammate's shared host automatically.
Canonical docs updates go into your handoff for later serial integration. Do not
start/stop shared infrastructure or paid services implicitly. Use uniquely named
local disposable resources, remove only yours, and leave teammates' containers alone.

Test idempotent ingestion, exact dates/spans, claim/entity relations, config/vector
compatibility, independent lexical/vector hits, authorization/revocation,
publication failure, graph support, whole-corpus dedup, case-source lineage and
new service ports. Preserve/run existing backend DB tests. Deliver real source/
coverage manifests, snapshot/build/config IDs and expected-expert query examples;
measure Recall@10 with reviewed labels, not synthetic fixture scores.

Write dependency proposals under ingestion/requirements.in. Write an owned
HANDOFF.md with actual importable factories, exact port mappings, startup/embedding
service details, required env, tested commands/results, corpus omissions, snapshot
IDs and interface requests. Never commit credentials, unauthorized raw source data,
model weights or local database dumps. This prompt authorizes commits/pushes to
your own feature branch only after checks pass. Stage only owned paths; no
force-push, shared-history rewrite or main merge.
