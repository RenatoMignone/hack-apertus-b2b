# Backend readiness checklist

19 October 2026. Renato's merged Linux measurements and Elia's new branch checks
are distinguished below. See the [branch handoff](BACKEND_RESEARCH_COMPLETION.md).
[Access status](RUNTIME_ACCESS_STATUS.md), [live corpus mode](../data/LIVE_CORPUS_RUNTIME.md)
and [web research](../data/WEB_RESEARCH.md) contain setup and evidence.

| # | Area | Status | What remains |
| --- | --- | --- | --- |
| 1 | Python environment | Verified on Renato; refreshed on Elia | Backend/hosted dependencies, pinned tokenizer and isolated Crawl4AI are installed and tested. Repeat packaging checks on other target hosts. |
| 2 | Runtime configuration | Done locally | Private live binding/profile installed; credentials preserved. API and worker must restart after code/config changes. |
| 3 | Operator authentication | Verified | Existing token preserved and bound to the correct live principal/namespace. Verify each other user's own binding separately. |
| 4 | Infrastructure access | Renato verified; Elia SSH/DB verified | DB identity/schema, actual case capture, checkpoint write/read and storage integrity passed. Renato readiness/bootstrap pass. Elia’s separate credentials are now applied; all network readiness checks and authenticated API health/capabilities pass; broader deployment hardening remains. |
| 5 | Live Keera adapter | Interpretation verified | Current Apertus 70B interpretation/repair passed in 27.64 seconds. Live extraction, assessment, drafting-only retry and reviewed PDF passed on Elia. Improve named-entity coverage and measure end-to-end latency/quality. |
| 6 | Isolated full pipeline | Done | The completion checkpoint extends the integrated regression suite using disposable PostgreSQL, including live/published modes, user isolation, actual reviewed PDF, gap follow-up, recorded lineage and safe failure diagnostics with synthetic providers. Real-provider partial report and reviewed PDF now pass; expert-search quality remains open. |
| 7 | Recovery/reliability | Isolated process acceptance passed | Killed worker after persistence commit, resumed in a separate process through real PostgreSQL checkpoints without duplicate extraction/claims. Repeat on the selected deployment host. |
| 8 | Gap-driven research | Implemented on new branch | Novel gap queries, accumulated supported work, no-repeat stopping and final freeze are tested. Verify useful gaps/queries on real cases. |
| 9 | Optional web research | Implemented and live-tested | Private keyless SearXNG + controlled fetch + isolated Crawl4AI works through actual LangChain tools. Ten-page default budget and partial-engine diagnostics tested. Verify combined DB/web deduplication/provenance in a live case; monitor upstream blocks. |
| 10 | Reranking | Provisioned and live retrieval tested on Elia | Pinned multilingual CPU model; all 30 real-corpus hits reranked. Review quality/latency against fused baseline and provision on other hosts. See [setup](../data/RERANKING.md). |
| 11 | Search lineage | Query/evidence paths implemented | Persist/expose actual query → canonical evidence paths from retrieval. Synthetic browser diagram/text paths verified; inspect real-case UI; do not fabricate phrase/ontology mappings absent from observations. |
| 12 | Evaluation suite | CLI and candidate suite implemented | Same-capture lexical/dense/RRF/reranked timing and reviewed-label Recall@10 tooling exists. Human gold labels and quality results remain pending. |
| 13 | Runtime operations | Partial | Local setup/readiness/bootstrap and principal-scoped queue design verified. Demonstrate supervision, tracing, restart recovery and checkpoint isolation on the deployment host. |
| 14 | Deployment target | Open | Choose and demonstrate the target. Connected local development does not prove an air-gapped or sovereign Swiss deployment. |

## Output gaps

- **Live structured result fields:** UI supports hierarchy, expertise, missing-field
  labels and infrastructure cards; optional backend metadata remains incomplete; facility/service classification is wired.
- **Connected PowerPoint/manual plans/own-case matching:** implemented and connected;
  enable only after [Eric’s optional migration/asset checks](OPTIONAL_FEATURE_ACTIVATION.md).
  Shared agency case access, real case-pair calibration and economic forecasts are deferred.

## Latest fixes and limits

The original real case failed before inference because raw taxonomy rows exceeded
the model input budget. A compact vocabulary reduced taxonomy JSON from 107,282
to 24,255 characters, retaining 132 concepts, 132 labels and 230 relationships.
Model-facing short codes map back to canonical IDs. The later Helvetic reproduction showed the bounded activity array still failed after
repair. The new branch uses a neutral display fallback and preserves all scientific
wording; non-blocking research questions are distinct from unclear user intent.
The live interpretation probe passed and requested four clarifications; it changed
no stored case/run. It is not a complete live research/report acceptance result.

Eric's live mode captures ready authorized evidence at run creation while ingestion
continues. Per-run captures stay stable; publication is optional for development.
A transactionally rolled-back peer probe captured 13,705 ready chunks. No shared
schema/grant changes, broad role grants or ingestion replacement were performed here.

Elia’s later key-only SSH and current DB identity/schema checks now pass. The
expanded branch suite and live retrieval probes are recorded separately in the
[branch handoff](BACKEND_RESEARCH_COMPLETION.md). A valid no-match in an initial
model-task probe is not useful case-to-PDF acceptance.

Current ordered feature deliveries and measured limits: [completion roadmap](COMPLETION_ROADMAP.md).
