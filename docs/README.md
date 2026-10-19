# B to Bern documentation

B to Bern (B2B), by **Team Stregoni**, turns permitted company context into a
source-backed, human-reviewed Bern opportunity brief.

**Jury:** [start here](judges/README.md). **Contributors:** select a module below.
[Current delivery status](project/STATUS.md) is the single acceptance summary;
[verification](judges/VERIFICATION.md) records measured scope.

| Area | Authoritative guide |
| --- | --- |
| Product, requirements and examples | [Requirements](challenge/PRODUCT_REQUIREMENTS.md), [workflow](challenge/WORKFLOWS_AND_CASES.md), [pilot](challenge/PILOT_SCOPE.md) |
| End-to-end design | [Architecture](plans/ARCHITECTURE.md), [execution graph](plans/EXECUTION_GRAPH.md) |
| Code and interfaces | [Modules](plans/MODULE_HANDOFFS.md), [source structure](plans/SOURCE_STRUCTURE.md), [service ports](plans/SERVICE_CONTRACTS.md), [HTTP](plans/FRONTEND_BACKEND_API.md) |
| Runtime and evidence | [Operations](plans/OPERATIONS_PLAN.md), [processing](plans/REPORT_PROCESSING_BOUNDARIES.md), [output](plans/OUTPUT_REPORT_STRUCTURE.md) |
| Setup and deployment | [Local services](data/LIVE_SETUP.md), [infrastructure](data/DEPLOYMENT.md), [Docker](judges/DOCKER.md) |
| Persistence | [Data layer](data/DATA_LAYER.md), [schema](data/RELATIONAL_SCHEMA.md), [exact fields](data/SCHEMA_REFERENCE.md), [case lineage](data/CASE_STATE_AND_LINEAGE.md) |
| Corpus | [Ingestion](data/ingestion/INGESTION_SPEC.md), [curation](data/CORPUS_REVIEW.md), [profiles](data/DOMAIN_PROFILES.md), [provenance](data/DATA_AND_PROVENANCE.md) |
| Search and models | [Retrieval](data/RETRIEVAL_SPEC.md), [Apertus](data/INFERENCE_CONFIGURATION.md), [embeddings](data/HOSTED_EMBEDDINGS.md), [reranking](data/RERANKING.md), [web tools](data/WEB_RESEARCH.md) |
| Optional capabilities | [Own-case memory](data/CASE_MEMORY.md), [plans and PPTX](data/RICH_OUTPUTS.md) |
| Reliability and quality | [Performance](data/CAPTURE_PERFORMANCE.md), [observability](data/OBSERVABILITY.md), [evaluation](challenge/EVALUATION.md) |
| Demo and submission | [Walkthrough](judges/DEMO.md), [delivery checklist](judges/DELIVERY.md), [technical report](../technical_report.md) |
| Original requirements and materials | [Challenge](challenge/CHALLENGE_BRIEF.md), [source provenance](project/SOURCES.md), [assets](provided_material/README.md), [transcripts](recordings/README.md) |

Executable contracts and schema take precedence for exact fields. Source snapshots,
transcripts and supplied assets retain their original contents; they document
requirements, not current implementation or research evidence. Completed task
prompts, lane ownership records and incremental access-status handoffs have been
removed. Current operational instructions are in the runbook, with no developer
credentials or machine-specific access bundle required to understand the design.
