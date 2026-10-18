# Shared contracts and ports

`data.py` implements validated storage/search DTOs, exact span validation,
model configuration, and artifact/embedding/reranking ports without SQL dependencies.
Use opaque IDs, explicit versions and source/access context throughout.

Specification owners:

- [Ingestion §7](../../../docs/plans/INGESTION_PLAN.md#7-shared-contract-v1--owned-here-consumed-by-phase-2): shared records/read interfaces.
- [Architecture pack boundary](../../../docs/plans/ARCHITECTURE.md#evidence-pack-the-report-generation-gate): ReportEvidencePack contents.
- [Data specs](../../../docs/data/DATA_LAYER.md): physical storage, retrieval and lineage.
- [HTTP handoff](../../../docs/plans/FRONTEND_BACKEND_API.md): implemented HTTP transport/projections.

Do not invent a competing evidence schema. See `pipeline.py` and the agreed processing contract.

## Implemented pipeline and service contracts

`pipeline.py` owns typed interpretation, fetched source, assessment, pack, draft reason and export contracts. `services.py` owns implemented async ports and DTOs; the application composes
reasoning/backbone/web/PDF adapters. Actual model/corpus provisioning remains
separate. See [integration](../../../docs/team/INTEGRATION.md).

## Parallel feature routing

[Module handoffs](../../../docs/plans/MODULE_HANDOFFS.md) lists this module's
focused read path, outputs and acceptance checks. [Active questions](../../../docs/project/OPEN_QUESTIONS.md)
own unresolved inputs. Implement scoped behavior against agreed contracts and
fixtures; coordinate shared schema/config changes. Leave `src/frontend/` untouched.
