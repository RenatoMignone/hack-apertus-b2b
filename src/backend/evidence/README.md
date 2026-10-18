# Evidence preparation

The [processing contract](../../../docs/plans/REPORT_PROCESSING_BOUNDARIES.md)
defines retrieval → assessed claims → frozen ReportEvidencePack. Storage is
implemented in `data/repositories/evidence.py`: interpretations, exact claim
assessments, case manifests, pack freezing and authorized citation reads.
[Pack content](../../../docs/plans/ARCHITECTURE.md#evidence-pack-the-report-generation-gate)
remains authoritative. A ranked hit is not a fact; live model extraction and
semantic validators are subsequent adapters, not implemented by persistence.

## Parallel feature routing

[Module handoffs](../../../docs/plans/MODULE_HANDOFFS.md) lists this module's
focused read path, outputs and acceptance checks. [Active questions](../../../docs/project/OPEN_QUESTIONS.md)
own unresolved inputs. Implement scoped behavior against agreed contracts and
fixtures; coordinate shared schema/config changes. Leave `src/frontend/` untouched.
