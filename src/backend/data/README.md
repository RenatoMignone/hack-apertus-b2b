# Data adapters

Implemented adapters for canonical records, scoped evidence, snapshots and search.
Use [data-layer router](../../../docs/data/DATA_LAYER.md) and its focused specs.

- `repositories/`: parameterized PostgreSQL access and transaction boundaries.
- `migrations/`: application-owned navigator schema migrations only.
- `retrieval/`: independent lexical/vector branches, RRF and reranker integration.
- `artifacts/`: controlled original/normalized/pack/export byte storage adapters.

Inputs: typed IDs/queries plus snapshot/scope/access context. Outputs: versioned
records/hits/artifact references. No model-generated SQL. Retrieval uses injected
model ports. See [deployment](../../../docs/data/DEPLOYMENT.md) for services,
CLI, migrations and tests. LangGraph and
Langfuse retain their own migration tools and framework-owned tables.
