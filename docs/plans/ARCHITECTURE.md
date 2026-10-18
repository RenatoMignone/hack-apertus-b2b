# Architecture and evidence preparation

**18 October 2026 · Design, not implemented or deployment-tested.**
The user selected a domain-independent pipeline, manual text intake and the
existing report structure. [Visual reference](../architecture.html) stacks the
overview, ingestion, case research, evidence pack, domain changes and deployment.
This file owns the architecture/deployment boundary; the paired plans own
processing contracts and operational details.

**U6/D09 update:** PostgreSQL + pgvector replace Weaviate/SQLite; LangGraph
uses PostgreSQL checkpoints and Langfuse provides local tracing. EmbeddingGemma 2
replaces BGE-M3 as the initial embedding candidate. Exact model/tokenizer sources,
revisions and deployment resources are deferred. [Data-layer router](../data/DATA_LAYER.md)
owns physical specs; logical payloads remain in ingestion section 7.

## Input and output boundary

The business developer reads the confidential business plan and one-pager
**outside this application**, then types permitted keywords, context, public
company information and suggestions. Her message is not an automatic upload of
either document. Operator knowledge is a lead or attributed statement until
supported by evidence; it is not automatically an established public fact.

**Now:** text-only case intake. Public linked PDFs may still be collected as
research sources. **Future extension:** an attachment adapter for the two PDFs,
disabled until permission, information handling, access, retention and deployment
requirements are explicitly revised. Parsing or local inference does not itself
make confidential documents eligible. No model-based redaction before permission.
Workshop basis: [T05 00:48–01:22, 01:43–04:41](../recordings/bern-navigator-followup-2026-10-18.txt).

The accepted [report structure](OUTPUT_REPORT_STRUCTURE.md) stays unchanged:
summary; company snapshot/needs; Bern expertise; related projects; pitch arguments;
gaps/next steps; sources/coverage; optional economic contribution and prior cases.

## Components and location

| Component | Responsibility | Proposed execution location |
| --- | --- | --- |
| Browser UI | Typed input, follow-up answers, source inspection, review, downloads | Operator device; assets served by the application, no CDN dependency |
| Application/API + LangGraph | Case revisions, bounded workflow, authorization, cancellation and checkpoints | Independent runtime host, outside cantonal ICT |
| Collection worker | Discovery, robots/access checks, safe fetch, public company research | Connected collection host; optional runtime tool only in connected mode |
| Parsers/normalizers | HTML/text-PDF extraction, tables, locators, quality checks; OCR later | Collection host or local case-research worker |
| Apertus v1.5 8B / optional 70B | Interpretation, evidence-linked enrichment, match reasoning, report writing | Local serving inside the deployment boundary for disconnected mode; otherwise only a verified compliant endpoint |
| EmbeddingGemma 2 candidate + BGE reranker | Document/query embeddings and passage reranking through separate adapters/tokenizers | Local runtime workers; embedding also runs during index build; exact artifacts deferred |
| Artifact store + PostgreSQL canonical records | Raw/normalized bytes, exact evidence, entities, claims, derivations, manifests | Controlled persistent storage inside the boundary |
| PostgreSQL + pgvector | Full-text lexical + vector cosine retrieval, RRF fusion, snapshot/access filtering | Runtime boundary; supplied vectors and versioned search configs |
| PostgreSQL case/checkpoint stores | Intent, questions, selections, run/export revisions; framework-owned checkpoints in separate DB | Runtime boundary; case access isolated from public corpus |
| Self-hosted Langfuse | Sanitized execution/model/retrieval observations and evaluation events | Runtime boundary; web/worker, PostgreSQL, ClickHouse, Redis/Valkey and S3-compatible storage |
| Calculator + export worker | Validated formulas, chart datasets, report rendering, editable slides | Runtime boundary with packaged template, logo, fonts and renderer |

Logical components may share a host/process. Hardware, serving endpoints and
frontend/export libraries remain unknown; do not read this table as a deployed topology.
Preserve `LLM_NAME`, `LLM_BASE_URL`, `LLM_API_KEY`; credentials stay server-side.

## Data-independent core and configurable domain profile

The engine knows documents, evidence, entities, claims, needs and matches. It
must not embed diabetes labels, institutions, website selectors or clinical
assumptions in orchestration or storage logic. The current Bern healthcare pilot
remains required; generality does not authorize automatic scope expansion.

| Stable core | Versioned domain profile / adapter |
| --- | --- |
| Collection and extraction contracts | Source registry, source families, site/parser adapters, access rules |
| Evidence/claim lineage and entity resolution | Taxonomy, definitions, multilingual aliases, optional entity/predicate extensions |
| Query planning and hybrid search API | Geography, languages, constraints, expansion/ranking settings |
| Validation and report-section contracts | Domain validation rules, relevance rubric, evaluation fixtures |
| Review, revisions and export | Terminology, branding/template and audience configuration |

Every run pins `domain_profile_id/version`, `schema_version`, `taxonomy_version`,
`snapshot_id`, case evidence manifest, index/embedding build and prompt/model versions.
New fields use a versioned extension; the core must tolerate unknown concepts.

## RAG rebuild rules

| Change | Recompute | Reuse where compatible |
| --- | --- | --- |
| Add source/domain | Collect new permitted sources; extract, enrich, chunk, embed and build a staged index | Existing raw evidence and compatible vectors |
| Parser/normalizer | Re-extract stored raw bytes; rebuild affected spans, claims, chunks and vectors | Raw artifacts; no unnecessary crawl |
| Taxonomy/definitions | Reclassify affected content; revise concept mappings, metadata/index and evaluation | Literal source text; vectors only if embedding text/settings are unchanged |
| Chunking or embedding model/settings | Rechunk and/or re-embed affected corpus; rebuild retrieval index | Raw and normalized evidence; compatible factual claims |
| Query/ranking/prompt rules | Rerun affected case retrieval/reasoning and evaluation | Corpus and index unless their representation changed |
| Wording/layout only | Regenerate report/export from the accepted evidence pack | Retrieval, evidence and calculations |

Never query one embedding space with another model's vectors. Build in staging,
check provenance/vectors/coverage, run domain-specific evaluation, then publish
an immutable snapshot and switch the active pointer. Keep old builds for rollback
subject to access/retention rules. Rebuilding an index is distinct from fine-tuning.

## Evidence pack: the report-generation gate

| Record | Minimum contents | Report use |
| --- | --- | --- |
| Intent + company | Current permitted message, priorities/exclusions, identity, field-level facts and unknowns | Company snapshot and context |
| Needs + matches | Explicit/inferred needs; entities, capability/project/service, need-to-capability links; direct/adjacent status | Expertise and related projects |
| Opportunity arguments | Need → supported capability → potential benefit, prerequisites and hypothesis label | Summary and pitch arguments |
| Gaps/actions | Unanswered questions, absent/conflicting/stale evidence, possible manual introductions | Next steps and limitations |
| Numerical facts / optional scenarios | Value, units, currency/date/period/geography, actual/plan/estimate status; formula, assumptions, sensitivity, chart data | Optional economic contribution |
| Optional case comparisons | Authorized cases, similarities/differences, dated evidenced outcomes, scoring method | Comparable cases; currently no corpus supplied |
| Provenance + run manifest | Literal passages, claim/evidence IDs, URLs or input locators, dates, coverage/failures, versions and selections | Every factual statement and sources section |

All factual claims resolve to accepted support; user statements remain attributed,
and generated interpretations cannot cite themselves. Validate IDs and literal
spans deterministically **and** assess semantic support separately. Relevance,
historical similarity and evidence strength are different fields, not success
probabilities. Missing optional data disables its section; missing core support
produces a partial/no-match result, not fabricated content.

Contextualization and reranking select candidates, not verified facts. Retrieval
uses independent PostgreSQL lexical and pgvector branches with rank fusion;
inferred concept labels cannot hide otherwise relevant evidence. The owning
[retrieval spec](../data/RETRIEVAL_SPEC.md) defines budgets and validation handoffs.

The report writer receives this frozen pack, then its draft undergoes another
claim/citation check and operator review. Render charts from prepared datasets;
render editable PowerPoint from the reviewed revision and supplied template.

## Target architecture (mandatory)

**Proposed primary target: b) air-gapped case runtime on independent infrastructure
outside cantonal ICT.** No external network connection at runtime. Build and
collection happen separately while connected; transfer only permitted, checked
artifacts. All inference, embeddings, reranking, storage, tracing, UI assets,
charts and export run inside the isolated boundary. Live company research is
unavailable; use packaged company evidence or mark missing context. Citation URLs remain
references and are not fetched automatically. No air-gap capability is yet tested.

| Template target | Proposed support / constraint | Proof required before a claim |
| --- | --- | --- |
| **a) On-premise** | Same components on an independently administered host; the track prohibits cantonal ICT/internal networks | Confirm ownership/administration and allowed infrastructure; document installation and run |
| **b) Air-gapped** | Primary design target; complete packaged snapshot/models/assets; external tools disabled with no silent fallback | Cold start and full case/report/export with external networking disabled; observe attempted egress and record failures |
| **c) Sovereign Swiss cloud** | Connected alternative, provider not selected; every runtime service and data flow must satisfy Swiss operation, jurisdiction and residency | Verify provider/operator, jurisdiction, region, storage/backups/logs, subprocessors and model/search dependencies; a Swiss URL is insufficient |

These are design options, not three achieved certifications. A generic independent
cloud does not automatically qualify as sovereign Swiss cloud. A development
inference endpoint does not prove either sovereign or air-gapped deployment.

## External dependencies by lifecycle

| Stage | External dependencies | Required record / offline behavior |
| --- | --- | --- |
| Build/package | Package/container registries, model/tokenizer weights, optional browser/OCR/render binaries, fonts | Pin versions/checksums/licenses; package assets, remove install-on-first-use behavior |
| Connected collection/refresh | Public institutional/company websites, robots/sitemaps, optional search provider | Access policy, requests, timestamps, failures, permitted storage/export; search provider remains unselected |
| Air-gapped runtime | **None external**; models, PostgreSQL/pgvector, app/checkpoints, local Langfuse and its auxiliary stores, renderer/assets | No hosted APIs, remote vectorizers, CDN, external telemetry/tracing, external fonts or runtime downloads; verify by blocked-network run |
| Connected runtime alternative | Only explicitly enabled web/search and verified model services | Disclose query/data egress and failures; enforce deployment policy; disable unsupported dependencies rather than silently switching |

Quantitative economics needs supplied public/eligible figures and a stated method;
there is no automatic economic data feed or forecasting model. Historical-case
data is absent. Future confidential PDFs require a separately authorized design.

Langfuse adds web/worker, its PostgreSQL database, ClickHouse, Redis/Valkey and
S3-compatible storage; include these in resource/backup/offline packaging. Trace
only masked eligible data through the local endpoint, without requiring tracing
availability to finish a case. [Observability](../data/OBSERVABILITY.md) owns these
contracts; [build/operations](../data/BUILD_AND_OPERATIONS.md) owns data-service
publication, migrations, recovery and implementation gates.

## Validation before implementation claims

- Reconstruct every citation; preserve evidence across edits and exports.
- Meet the pilot's Recall@10, factual support and three-family coverage gates.
- Exercise a second domain profile with fixtures without changing core flow;
  verify a staged index rebuild and rollback. Do not claim second-domain quality
  merely from configuration support.
- Verify dependency inventory, isolated cold start, inference resources and
  report/slide rendering on the actual selected target.

Owners: [ingestion/contracts](INGESTION_PLAN.md), [case operations](OPERATIONS_PLAN.md),
[data-layer implementation](../data/DATA_LAYER.md), [evaluation](../challenge/EVALUATION.md),
[decisions](../project/DECISIONS_AND_OPEN_QUESTIONS.md).
