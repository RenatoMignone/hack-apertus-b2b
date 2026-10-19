# System architecture

B2B connects a company's needs to public Bern research capabilities. The operator
supplies permitted context, inspects cited reasons, reviews them and exports a
brief. The diabetes-technology pilot spans UniBE, ARTORG and Diabetes Center Berne.

## Components

| Layer | Implementation and responsibility |
| --- | --- |
| Browser | React, TypeScript, Vite, Tailwind, Radix Themes; cases, chat, source inspection, review, history and downloads |
| HTTP API | FastAPI / Pydantic; authorization, validation, idempotent commands and projections |
| Application | Identity, transactions, case/input revisions, run queue, approval and artifact access |
| Worker | Durable LangGraph stages and LangChain tool/task adapters; bounded research and recovery |
| Reasoning | Apertus v1.5 70B through Keera in connected development; structured interpretation, extraction, assessment and writing |
| Knowledge | PostgreSQL/pgvector; scoped source versions, supported entity relationships, taxonomy, hybrid retrieval and case evidence |
| Models | Separate compatible embedding encoder and optional cross-encoder reranker |
| Research tools | Private SearXNG URL discovery, controlled public HTTP fetch, isolated Crawl4AI conversion |
| Storage | S3-compatible artifacts; separate PostgreSQL checkpoints; optional self-hosted Langfuse traces |

The [execution graph](EXECUTION_GRAPH.md) shows control flow. API and worker are
separate processes; backend modules communicate through [typed ports](SERVICE_CONTRACTS.md).
The browser uses [HTTP](FRONTEND_BACKEND_API.md), never DB or provider credentials.

## Input and output boundary

The operator reads company plans outside the app and supplies only permitted
context. Interpretation preserves full needs, negation, uncertainty and attributed
operator leads; it produces company identity/description, profile-defined fields,
a short activity label, Bern objectives, keywords and clarification questions.
A short label never replaces the complete request. Ambiguity blocks only when
necessary to proceed; unknown optional facts remain explicit.

Database lexical and vector branches are independent, fused with RRF and optionally
reranked. Connected web research runs alongside them. Canonical duplicates prefer
the pinned corpus version; new web text remains case-local and unreviewed.
Exact passage validation and semantic claim assessment precede generation.

## Evidence pack: the report-generation gate

`ReportEvidencePack` is an immutable, hash-bound supported input to drafting.
It contains interpretation, supported claims and their canonical evidence links,
matches/fit, coverage, gaps, limitations, recorded search lineage and applicable
attributed manual context. See `contracts/pipeline.py` for exact fields.

Code checks identity, scope, literal spans and hashes. Apertus assesses semantic
support and company fit. Unsupported/contradicted claims cannot enter the supported
pack. Draft wording receives a separate assessment against that exact pack.
Each reason resolves claim IDs to evidence IDs and original sources. Ranking and
operator selections remain separate from factual validation.

Operators review every card and keep at least one. An accepted review binds the
exact result and selection hashes; the renderer includes kept reasons, their
sources and caveats. Access/currentness are checked again at export and download.
Wording-only edits reuse the pack; changed focus/identity creates new research.

## Data-independent core and configurable domain profile

One application database separates corpus, taxonomy, retrieval, cases and ops.
Entity relationships are source-backed relational claims, with bounded expansion;
there is no separate graph database. Domain profiles version field vocabularies,
institution labels and taxonomy. Each run pins profile/taxonomy, snapshot/build,
embedding configuration and relevant model/prompt versions.

Live mode captures immutable ready evidence per case while ingestion continues.
Published mode uses a reviewed active release. Neither mode grants access to
otherwise hidden sources. See [live captures](../data/LIVE_CORPUS_RUNTIME.md).

## RAG rebuild rules

Changed encoder weights/revision, tokenizer, templates, dimensions or normalization
require compatible new embeddings and index builds. A new reranker does not
change the embedding space. Source updates create versions; existing runs retain
their pinned evidence. Corpus publication is an explicit ingestion operation.

## Target architecture (mandatory)

The selected design target is an **air-gapped case runtime on independent
infrastructure outside cantonal ICT**. Demonstration remains pending. Package
Apertus serving assets, encoder/reranker/tokenizers, dependencies, corpus/indexes
and report assets; disable web and external egress. Verify cold start, case,
review/export and recovery without external networking.

Current development is connected: Keera and hosted HF embeddings, independent
PostgreSQL/MinIO and local API/worker/browser. This path is implemented and has a
recorded partial live PDF; it does not establish offline or sovereign deployment.
See [verification](../judges/VERIFICATION.md) for evidence and acceptance limits.
