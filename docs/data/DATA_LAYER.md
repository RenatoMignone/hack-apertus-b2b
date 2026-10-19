# Data layer

One PostgreSQL/pgvector application database stores five logical areas:
`corpus`, `taxonomy`, `retrieval`, `cases`, `ops`. Source institutions share one
knowledge ecosystem. LangGraph checkpoints and Langfuse use separate framework
storage/migrations; artifacts live in S3-compatible storage or a configured local
adapter.

| Concern | Reference |
| --- | --- |
| Tables and relations | [Schema overview](RELATIONAL_SCHEMA.md), [generated exact fields](SCHEMA_REFERENCE.md) |
| Public-source lifecycle | [Ingestion](ingestion/INGESTION_SPEC.md), [curation](CORPUS_REVIEW.md), [provenance](DATA_AND_PROVENANCE.md) |
| Query pipeline | [Hybrid retrieval](RETRIEVAL_SPEC.md), [encoder](HOSTED_EMBEDDINGS.md), [reranker](RERANKING.md) |
| Run corpus selection | [Live and published snapshots](LIVE_CORPUS_RUNTIME.md), [profiles](DOMAIN_PROFILES.md) |
| Case/report authority | [Lineage](CASE_STATE_AND_LINEAGE.md), [memory](CASE_MEMORY.md), [optional outputs](RICH_OUTPUTS.md) |
| Runtime | [Setup](LIVE_SETUP.md), [deployment](DEPLOYMENT.md), [performance](CAPTURE_PERFORMANCE.md) |

`data/schema.py` defines current tables and constraints. Application access uses
restricted roles, authenticated principal/namespace and scope grants. RLS remains
active for every retrieval/persistence path. `contracts/data.py` defines repository
and model inputs, including exact spans and compatible configuration hashes.

Ingestion records immutable original/normalized versions and chunk/evidence maps,
encodes exact formatted document inputs, builds retrieval projections and either
leaves ready evidence for live capture or publishes a checked release. Case runs
pin authorized membership and configuration. Web findings and generated claims
stay owned by the case; publication is an explicit corpus-owner operation.

Full-text and vector retrieval operate independently over the same authorized
membership. Graph expansion uses supported entity relationships in relational
claims. The model supplies no SQL. Current source migration is
`0013_retrieval_scope_sets`; installed-host revision must be checked independently.
Shared-host 0013 rollout and restricted-role retrieval measurements are recorded in
[live retrieval performance](LIVE_RETRIEVAL_PERFORMANCE.md).
