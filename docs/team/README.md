# Team documents

18 October 2026 · The original backend lanes and `ui-polish` are merged into main.
Keep this directory for integration evidence and interface provenance. The active
work plan is [current status](../project/STATUS.md), [module routing](../plans/MODULE_HANDOFFS.md)
and [open questions](../project/OPEN_QUESTIONS.md).

| Document | Use now |
| --- | --- |
| [Current backend checklist](RUNTIME_CHECKLIST.md) | Current 14-area readiness and remaining live/output gaps |
| [INTEGRATION.md](INTEGRATION.md) | Current merged baseline, reviewed tips, fixes and dated verification |
| [Runtime access status](RUNTIME_ACCESS_STATUS.md) | Eric's live binding; Renato's case/capture, network readiness and production bootstrap pass after metadata grant |
| [Backend acceptance](BACKEND_RUNTIME_ACCEPTANCE.md) | Renato’s partial sandbox run and explicit disposable-test guard |
| [SERVICE_CONTRACTS.md](SERVICE_CONTRACTS.md) | In-process service boundaries; executable DTOs/ports are authoritative |
| [Eric runtime access prompt](prompts/05_RUNTIME_ACCESS_HANDOFF.md) | Active access/credential and publication handoff; preserve ongoing ingestion |
| [Renato runtime acceptance prompt](prompts/06_BACKEND_RUNTIME_ACCEPTANCE.md) | Active local setup, isolated tests and real-provider/corpus acceptance |
| [Eric migration prompt](prompts/04_SHARED_HOST_MIGRATION.md) | Completed rollout instructions; do not rerun for runtime setup |
| [Migration outcome](MIGRATION_STATUS.md) | Completed 0004 → 0007, backup/preservation and services |
| [Hosted embeddings](../data/HOSTED_EMBEDDINGS.md) / [LF fix](../data/WINDOWS_SHELL_FIX.md) | Current adapter and Windows follow-up |
| [Live setup](../data/LIVE_SETUP.md) | Current rollout steps, migration authority and local/shared prerequisites |
| [PARALLEL_BACKEND.md](PARALLEL_BACKEND.md), [original prompts](prompts/01_RUNTIME.md) | Historical completed assignments, not instructions for the next feature |
| [Runtime handoff](runtime/HANDOFF.md), [original HTTP map](runtime/HTTP.md) | Historical lane-A snapshot; use the [current HTTP contract](../plans/FRONTEND_BACKEND_API.md) for client work |
| [Intelligence handoff](intelligence/HANDOFF.md), [model comparison](intelligence/MODEL_COMPARISON.md) | Historical lane-B snapshot and measured limited provider probes |
| [Backbone handoff](backbone/HANDOFF.md), [results](backbone/RESULTS.md), [source manifest](backbone/SOURCE_MANIFEST.json) | Historical lane-C snapshot, collection/test observations and explicit omissions |

Old lane freezes, A/B/C write allowlists, outstanding integration requests and
pre-merge branch instructions no longer govern the integrated baseline. Their
remaining deployment/quality issues are reconciled in the active register.
Source manifests and diagnostic results are evidence; deleting the entire
folder would remove useful provenance and break references. No move is needed.
