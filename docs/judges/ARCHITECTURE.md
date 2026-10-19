# Architecture for reviewers

The browser is a React/Vite client. FastAPI authenticates and persists commands;
a separate durable LangGraph worker runs bounded research. PostgreSQL/pgvector
stores authorized corpus/taxonomy/cases and retrieval. Source/report artifacts,
framework checkpoints and optional masked Langfuse tracing have separate roles.

1. Apertus v1.5 70B interprets permitted company context against a reviewed domain
   vocabulary and asks for blocking clarification when needed.
2. Independent full-text and vector retrieval run over pinned authorized evidence,
   followed by RRF and optional reranking. Connected web research runs alongside.
3. Canonical deduplication prefers corpus versions; new web pages stay flagged and
   case-local. Exact spans and semantic claim assessment gate supported evidence.
4. Code freezes a hash-bound `ReportEvidencePack`. Apertus drafts cited reasons
   and assesses their wording against that pack.
5. The operator reviews every card and keeps at least one. Exact result/selection
   hashes and accepted review gate deterministic export and authorized download.

Wording edits reuse the pack; changed focus/identity starts new research. Runs
resume through PostgreSQL LangGraph checkpoints while application records remain
business authority. Recorded query/evidence links explain actual retrieval;
models cannot invent lineage. Graph relationships are supported relational claims,
with bounded expansion rather than a separate graph database.

The main design strengths are provenance across stages, explicit uncertainty,
independent lexical/vector recall, modular typed interfaces, durable execution and
human-controlled output. These mechanisms reduce risk; their existence is not a
measured accuracy claim.

See the [execution graph](../plans/EXECUTION_GRAPH.md),
[technical architecture](../plans/ARCHITECTURE.md), [module map](../plans/MODULE_HANDOFFS.md)
and [verification](VERIFICATION.md). The technical report selects an independent
air-gapped target; current connected development has not demonstrated that target.
