# Report generation, checks and rendering

- `generation/`: frozen eligible pack → structured report revision.
- `validation/`: report assertions/citations checked against its pinned pack.
- `rendering/`: exact reviewed revision/selections → downloadable artifacts.

Read [processing Boundary B](../../../docs/plans/REPORT_PROCESSING_BOUNDARIES.md#boundary-b-reportevidencepack--final-output)
and [output sections](../../../docs/plans/OUTPUT_REPORT_STRUCTURE.md).
Application use cases own review/export authorization. Writer/checker/renderer
use service/model/artifact ports; no silent retrieval or evidence-pack mutation.
Unsupported content is a gap/escalation, never a newly invented fact.

Detailed transformations, prompts, intermediate schemas, job/run mapping and
rendering library/template mapping are deferred. Preserve supplied assets;
no deck generation, source files or renderer dependencies are added now.
