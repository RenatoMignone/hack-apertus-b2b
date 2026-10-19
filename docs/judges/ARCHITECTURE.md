# How B2B works

B2B separates research, factual support, writing and editorial selection.
Apertus proposes interpretations and assessments; code assigns identifiers,
checks literal support, pins evidence and enforces review/export consistency.

## From company need to reviewed brief

1. **Intake:** authorized API persists permitted company context as an immutable
   input revision. Confidential documents remain outside the application.
2. **Interpret:** Apertus preserves full intent, priorities, negation and uncertain
   operator leads. Versioned taxonomy/profile data helps bridge vocabulary.
   Blocking intent questions pause the workflow; unknown public facts become
   research gaps rather than questions the operator must invent answers to.
3. **Research:** independent lexical and vector retrieval, reciprocal rank fusion,
   optional reranking and bounded connected web research find candidate evidence.
   Topic labels do not suppress otherwise eligible vector matches.
4. **Prepare evidence:** exact passage/hash checks and semantic support/fit
   assessment separate supported statements from gaps and contradictions.
   Models cannot create authoritative quotation offsets or source metadata.
5. **Freeze:** code assembles an immutable `ReportEvidencePack` with claims,
   context, matches, provenance, coverage and limitations.
6. **Draft:** Apertus writes only from that pack. Literal references and semantic
   wording support are checked before persisting an exact-hash draft assessment.
7. **Review/export:** every reason is kept or rejected, at least one is kept, and
   approval binds exact report and selection hashes. Deterministic rendering adds
   no newly researched facts.

The [execution graph](../plans/EXECUTION_GRAPH.md) provides the system diagram.
The [processing contract](../plans/REPORT_PROCESSING_BOUNDARIES.md) defines stage
and revision boundaries.

## Components and source map

- [Frontend](../../src/frontend/README.md): React/TypeScript/Vite, authenticated
  HTTP polling, case board, evidence inspection, chat, history and review.
- [API](../../src/backend/api/README.md) and
  [application](../../src/backend/application/README.md): FastAPI transport,
  identity/access checks, revision/idempotency policy and durable commands.
- [Workflows](../../src/backend/workflows/README.md): LangGraph stages, budgets,
  interruption/resume and worker execution; LangChain adapters support model tasks.
- [Models](../../src/backend/models/README.md): explicit Apertus reasoning,
  compatible local/hosted embeddings and optional CPU reranking.
- [Ingestion](../../src/backend/ingestion/README.md) and
  [data](../../src/backend/data/README.md): public acquisition, versioning,
  PostgreSQL/pgvector retrieval, authorization and source/export artifacts.
- [Evidence](../../src/backend/evidence/README.md) and
  [reports](../../src/backend/reports/README.md): assessed claims, frozen packs,
  supported drafting and deterministic PDF/optional PPTX.
- [Observability](../../src/backend/observability/README.md): masked local
  diagnostics; tracing failure cannot block a case.

These are logical modules in one backend, not independently deployed
microservices. API and worker are separate processes. Database evidence is
authoritative; LangGraph checkpoints resume execution and traces diagnose it.

## Evidence lifecycle and changes

A release can pin a published corpus snapshot. Development live mode instead
captures ready authorized evidence immutably for each case/run while ingestion
continues. New runs may see new data; old packs and formatting-only rewrites retain
their pins. New case-time web evidence remains flagged and case-scoped. Duplicate
URLs prefer pinned corpus versions; no automatic public-corpus learning occurs.

A wording edit reuses the pack and receives fresh validation. A focus/fact change
creates a new input and research cycle. Changed card content or support resets
review; matching card IDs alone cannot preserve approval. History is read-only.
Optional memory compares only explicitly eligible own cases; it provides neither
a shared agency library nor success probabilities.

## Deployment and dependencies

The current development setup uses member-hosted PostgreSQL, S3-compatible
artifacts, separate checkpoint access, local application processes and connected
Keera/HF inference. The browser needs only HTTP access to the API; provider keys,
database credentials and artifact credentials stay backend-only.

Build/provisioning needs Python/npm packages, images when containerized, pinned
tokenizers/configurations, model assets for local adapters and a prepared corpus.
Connected runtime needs the configured provider and infrastructure connections.
Optional web requires private SearXNG plus Crawl4AI in a separate environment;
its dependency lock cannot be combined with the backend lock.

The selected **air-gapped design target remains unverified**. It needs local
Apertus serving, local encoding/reranking, transferred corpus/assets, local
database/storage/checkpoints and no external web/telemetry dependency. A hosted
gateway cannot establish this target. Likewise no Swiss-cloud residency or
jurisdiction claim follows from connected development.

For independent judge access, the delivery recommendation is stable application
hosting with private database/storage connectivity. A public frontend alone
cannot run background research; database hosting alone does not host the API or
worker. See [hosting decision and acceptance](DELIVERY.md#hosting-decision).
