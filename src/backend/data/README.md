# PostgreSQL and artifact adapters

`schema.py` owns tables; repositories own parameterized SQL, RLS access and
transactions; retrieval owns independent full-text/vector fusion; artifacts owns
controlled byte storage. Source head is 0013. Never import migration baseline
metadata or query retired `legacy` structures in runtime. Generate/check fields
with `python -m backend.data.schema_docs --check`.

Migration `0013_retrieval_scope_sets` batches equivalent SELECT authorization
checks. Applied and measured on the shared host on 19 October 2026; each operator
still needs to pull and restart their API/worker. See
[retrieval performance](../../../docs/data/LIVE_RETRIEVAL_PERFORMANCE.md).

Read the [focused specification](../../../docs/data/DATA_LAYER.md) and [module map](../../../docs/plans/MODULE_HANDOFFS.md).
Coordinate shared DTO/schema/configuration changes with their consumers and run
relevant boundary checks against isolated infrastructure.
