# Shared contracts and ports

Reserved for future typed DTOs, validation schemas, narrow service/repository/
model/storage ports and schema exports. No framework/client/SQL dependencies.
Use opaque IDs, explicit versions and source/access context throughout.

Specification owners:

- [Ingestion §7](../../../docs/plans/INGESTION_PLAN.md#7-shared-contract-v1--owned-here-consumed-by-phase-2): shared records/read interfaces.
- [Architecture pack boundary](../../../docs/plans/ARCHITECTURE.md#evidence-pack-the-report-generation-gate): ReportEvidencePack contents.
- [Data specs](../../../docs/data/DATA_LAYER.md): physical storage, retrieval and lineage.
- [HTTP handoff](../../../docs/plans/FRONTEND_BACKEND_API.md): proposed transport projections.

Do not invent a competing evidence schema. Exact pack/intermediate DTOs and
report-processing contracts still require the planned mapping work.
