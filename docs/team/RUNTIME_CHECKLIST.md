# Backend readiness checklist

19 October 2026. Latest measurements are from Renato's Linux workstation. Earlier
Mac/sandbox observations in historical handoffs do not describe this environment.
[Access status](RUNTIME_ACCESS_STATUS.md), [live corpus mode](../data/LIVE_CORPUS_RUNTIME.md)
and [web research](../data/WEB_RESEARCH.md) contain setup and evidence.

| # | Area | Status | What remains |
| --- | --- | --- | --- |
| 1 | Python environment | Done for Renato | Backend/hosted dependencies, pinned tokenizer and isolated Crawl4AI are installed and tested. Repeat packaging checks on other target hosts. |
| 2 | Runtime configuration | Done locally | Private live binding/profile installed; credentials preserved. API and worker must restart after code/config changes. |
| 3 | Operator authentication | Verified | Existing token preserved and bound to the correct live principal/namespace. Verify each other user's own binding separately. |
| 4 | Infrastructure access | Verified from Renato | DB identity/schema, actual case capture, checkpoint write/read and storage integrity passed. Current readiness and production bootstrap pass; broader deployment hardening remains. |
| 5 | Live Keera adapter | Interpretation verified | Current Apertus 70B interpretation/repair passed in 27.64 seconds. Complete live extraction, assessment, drafting and case-to-PDF; measure end-to-end latency/quality. |
| 6 | Isolated full pipeline | Done | 224 backend tests passed on disposable PostgreSQL, including live/published modes, user isolation and actual reviewed PDF with synthetic providers. Real-provider full-case acceptance remains. |
| 7 | Recovery/reliability | Partial | Automated recovery and checkpoint checks pass. Perform controlled restart/resume with the actual running worker and PostgreSQL saver. |
| 8 | Gap-driven research | Open | Generate revised queries from assessed gaps; current bounded follow-ups reuse original interpretation/search terms. |
| 9 | Optional web research | Implemented and live-tested | Private keyless SearXNG + controlled fetch + isolated Crawl4AI works through actual LangChain tools. Ten-page default budget and partial-engine diagnostics tested. Verify combined DB/web deduplication/provenance in a live case; monitor upstream blocks. |
| 10 | Reranking | Open | Pin/provision a reranker and evaluate real-corpus relevance, compatibility and latency. |
| 11 | Search lineage | Open | Persist/expose real input → concept → evidence links; keep unavailable UI state when absent. |
| 12 | Evaluation suite | Plan exists | Build reviewed cases, expected entities, variants, negatives and human audit records; measure recall/support/coverage. |
| 13 | Runtime operations | Partial | Local setup/readiness/bootstrap and principal-scoped queue design verified. Demonstrate supervision, tracing, restart recovery and checkpoint isolation on the deployment host. |
| 14 | Deployment target | Open | Choose and demonstrate the target. Connected local development does not prove an air-gapped or sovereign Swiss deployment. |

## Output gaps

- **Live structured result fields:** UI supports hierarchy, expertise, missing-field
  labels and infrastructure cards; backend population/classification remains incomplete.
- **Connected PowerPoint:** demo PPTX exists; backend approval, generation and artifact
  persistence are not implemented. Connected PDF is implemented and synthetically tested.

## Latest fixes and limits

The original real case failed before inference because raw taxonomy rows exceeded
the model input budget. A compact vocabulary reduced taxonomy JSON from 107,282
to 24,255 characters, retaining 132 concepts, 132 labels and 230 relationships.
Model-facing short codes map back to canonical IDs. A bounded activity-word array
improves schema repair while keeping the public activity-label string unchanged.
The live interpretation probe passed and requested four clarifications; it changed
no stored case/run. It is not a complete live research/report acceptance result.

Eric's live mode captures ready authorized evidence at run creation while ingestion
continues. Per-run captures stay stable; publication is optional for development.
A transactionally rolled-back peer probe captured 13,705 ready chunks. No shared
schema/grant changes, broad role grants or ingestion replacement were performed here.
