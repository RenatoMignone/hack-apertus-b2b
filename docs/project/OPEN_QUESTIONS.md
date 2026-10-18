# Open design choices and integration inputs

**18 October 2026 · U9 current register.** This is the authoritative active list.
[Decision history](DECISIONS_AND_OPEN_QUESTIONS.md) retains provenance and older
Q01–Q18. Resolved choices below are not blockers. Rows describe module roles, not
assigned people; no roster is invented. Use [module handoffs](../plans/MODULE_HANDOFFS.md)
to select an independent task.

## Settled baseline

PostgreSQL/pgvector with separate corpus/taxonomy/case schemas; LangGraph/LangChain
for agentic behavior; local Langfuse; text-only permitted intake; independent
lexical/vector branches + RRF/reranking; case-local flagged web sources allowed
after support checks; Crawl4AI for future fetching; frozen evidence pack before
draft; reason-card editorial keep/reject; clarification only when blocking;
connected and offline modes; PDF first and PPTX later. React/Vite frontend is
owned by a separate teammate and remains untouched by backend work.

D18 finalizes schema contract v1 at `0005_finalize_schema`: [exact fields](../data/SCHEMA_REFERENCE.md)
and [corpus/retrieval handoff](../data/INGESTION_RETRIEVAL_HANDOFF.md). Database shape
is settled for implementation; O04/O13/O14 concern model configuration, corpus
population and taxonomy contents, not alternative database designs.

Keera URL and four model aliases are supplied (Q05 partially resolved). API key,
authenticated access and gateway constraints remain untested. EmbeddingGemma 2
artifact reference is verified; **local text-only hosting is a recommendation**,
not a measured winner or an already running service.

## Active engineering decisions

| ID / related old question | What remains open | Recommended starting point / how to close | Module / impact |
| --- | --- | --- | --- |
| O01 / Q05 | Team Keera key, allowed models, quotas/rate/concurrency limits and expiry | Team requests key from Sabine; run the small tests in [inference config](../data/INFERENCE_CONFIGURATION.md); no confidential inputs | Models/operations; blocks live calls, not fixture work |
| O02 / Q05,Q15 | Keera JSON Schema/tool dialect, usage, max input/output, streaming and timeout behavior | Chat Completions non-streaming first, non-thinking tools; verify actual responses before selecting structured-output mode | Models/workflows |
| O03 / Q15 | Served Apertus weight revision, prompt/template versions and tokenizer access | Record aliases as served IDs, obtain version provenance; never invent immutable hashes; use compatible tokenizer limits | Models/evaluation |
| O04 / Q06,Q15 | Embedding host/device and supported runtime packages/model commit | Benchmark local text-only `google/embeddinggemma-2` first; 768d/float32 CPU baseline; decide only after latency/RAM/recall checks | Embeddings; blocks first real index build |
| O05 / Q15 | Hosted embedding fallback, exact HF credit eligibility/account/region and request parity | Keep unused unless local results require it; verify $10 credit terms; one shared endpoint owner; no assumed credit pooling | Embeddings/operations |
| O06 / Q15 | Reranker artifact/revision, tokenizer/pair limit, hardware and measured latency | Validate BGE-reranker-v2-m3 candidate independently of embedding/model services | Reranking |
| O07 / Q17 | HTTP framework, app/worker bootstrap and process ownership | Python HTTP server and durable worker using existing jobs/outbox; choose framework in the API task, not in a data adapter | API/application/workflows |
| O08 / Q17 | Authentication/session mapping to DB principals, colleague access, CORS/CSRF | Enforce existing owner/namespace isolation; do not interpret shared DB or similar-case UI as sharing authorization | API/security; required before real multi-user integration |
| O09 / Q17 | Machine-readable API schema, errors/pagination/limits and mock-client mapping | Implement [HTTP handoff](../plans/FRONTEND_BACKEND_API.md), agree additions with frontend teammate; stable IDs and 202 polling | API/contracts/frontend owner |
| O10 / Q18 | Full service ports, graph state schema, prompt/task versions and exact stage budgets | Start from implemented DTOs/repositories; three research rounds, one repair/task remain bounds; set token/time/tool/candidate budgets per run | Workflows/evidence/models |
| O11 / Q18 | Extraction/entailment/contradiction prompts and quality thresholds | Batch bounded passages; exact claim/statement/support assessment and exact draft hash; independently review representative cases | Evidence/validation; persistence alone is not a semantic validator |
| O12 / Q14 | URL discovery provider and allowed public-query scope | Separate provider from Crawl4AI; smallest public capability queries, explicit unavailable result when unconfigured | Research/tools |
| O13 / Q01,Q14 | Corpus acquisition completeness, page/PDF formats, chunking, access/refresh rules | Inventory plus three source families; validated snapshots; record exclusions and freshness; bulk ingestion remains separate | Ingestion/data |
| O14 / Q18 | Actual reviewed taxonomy concepts/aliases/relations and domain-profile contents | Start with diabetes-tech terms; preserve broader/narrower/related distinctions, multilingual labels and unknown concepts | Taxonomy/interpretation |
| O15 / Q08 | PDF renderer/layout/font/citation rules and report size | Deterministic concise PDF from selected reasons and caveats; use supplied challenge-only assets; verify actual pages; PPTX later | Reports/rendering |
| O16 / Q18 | Frontend additions and exact export/revision UX | Frontend teammate adds source-origin/review badge, all-reviewed gate, revision/hash commands and PDF naming; document contract before touching their code | Frontend/API |
| O17 / Q06,Q16 | Team-host migration scheduling, hardware, worker placement and full offline model packaging | Do not migrate shared host automatically; Keera is connected only; separate local Apertus adapter/weights needed for offline | Operations |
| O18 / Q16 | Trace/backup/artifact/checkpoint retention, gateway data handling/locality, restore policy and resource monitoring | Local masked tracing and nonblocking outages; select concrete durations/capacity with host owner; respect revocation | Operations/observability |
| O19 / Q03,Q04 | Gold queries, expected experts/units, approved examples and measured quality | Obtain partner examples; evaluate intent-balanced Recall@10 ≥ .80 and claim support/coverage; synthetic fixtures are not a benchmark | Evaluation |
| O20 | Final prompts for adjacent opportunities and source conflicts | Keep direct/idea labels and unresolved contradictions visible; never imply availability, willingness or clinical suitability | Evidence/reports |

## Optional data and delivery inputs

| ID / old question | Unresolved input | Treatment until resolved |
| --- | --- | --- |
| O21 / Q03 | Authorized historical case dataset, similarity method and outcome evidence | `search_cases` remains unavailable and frontend mock scores illustrative; no cross-owner access or success prediction |
| O22 | Eligible numeric investment/jobs/timeline data and economic formulas | Omit optional economics rather than infer numbers; formulas/scenario methods need independent support |
| O23 / Q07 | DE/FR/IT beyond English baseline | Preserve source language; evaluate query/answer translations before claiming multilingual quality |
| O24 / Q09 | Additional Bern organizations/people/companies and confirmed locality | Add evidence-backed entities within selected scope; membership is not proof of local presence |
| O25 / Q10 | Source/recording redistribution rights and exact Open Commons terms | Keep supplied materials/transcripts intact; avoid automatic publication; challenge-only branding |
| O26 / Q11,Q12 | Current submission package, report reference count, live pitch/Q&A and cutoff | Confirm current organizer instructions; historical deadlines/video limits are not live-pitch requirements |
| O27 / Q13 | Final team/project name, submission account, remote ancestry/visibility | Use actual team choices; preserve submission template; no publish/push without authorization |

Update this register when a question is resolved, with date, source, selected
behavior, affected interfaces and verification. Keep unmeasured recommendations
separate from decisions; feature agents need not wait on unrelated rows.
