# PostgreSQL and artifact adapters

`schema.py` owns tables; repositories own parameterized SQL, RLS access and
transactions; retrieval owns independent full-text/vector fusion; artifacts owns
controlled byte storage. Source head is 0012. Never import migration baseline
metadata or query retired `legacy` structures in runtime. Generate/check fields
with `python -m backend.data.schema_docs --check`.

Read the [focused specification](../../../docs/data/DATA_LAYER.md) and [module map](../../../docs/plans/MODULE_HANDOFFS.md).
Coordinate shared DTO/schema/configuration changes with their consumers and run
relevant boundary checks against isolated infrastructure.
