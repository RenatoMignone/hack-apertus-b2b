# Open design choices and integration inputs

**18 October 2026 · Post-integration current register.** This is the authoritative active list.
Integration update: [D20 / merged baseline](../team/INTEGRATION.md) implements
FastAPI/auth, service ports, LangGraph, model/retrieval adapters, PDF and the HTTP
frontend. Remaining rows below concern deployment or quality, not missing scaffolds.
[Decision history](DECISIONS_AND_OPEN_QUESTIONS.md) retains provenance and older
Q01–Q18. Resolved choices below are not blockers. Rows describe module roles, not
assigned people; no roster is invented. Use [module handoffs](../plans/MODULE_HANDOFFS.md)
to select an independent task.

## Settled baseline

PostgreSQL/pgvector with separate corpus/taxonomy/case schemas; LangGraph/LangChain
for agentic behavior; local Langfuse; text-only permitted intake; independent
lexical/vector branches + RRF/reranking; case-local flagged web sources allowed
after support checks; controlled HTTP/Crawl4AI conversion; frozen evidence pack before
draft; reason-card editorial keep/reject; clarification only when blocking;
connected and offline modes; PDF first and PPTX later. React/Vite frontend is
owned by a separate teammate and remains untouched by backend work.

D18 finalizes schema contract v1 at `0005_finalize_schema`: [exact fields](../data/SCHEMA_REFERENCE.md)
and [corpus/retrieval handoff](../data/INGESTION_RETRIEVAL_HANDOFF.md). D20 advances
head through 0006/0007; current head is `0008_live_corpus`. Database shape
is implemented; O04/O13/O14 concern model configuration, corpus
population and taxonomy contents, not alternative database designs.

Keera URL and four model aliases are supplied (Q05 partially resolved). A private
key worked for the [synthetic comparison](../team/intelligence/MODEL_COMPARISON.md);
current key validity, sustained quotas and broader gateway behavior remain open. EmbeddingGemma 2
artifact/revision and tokenizer are pinned; user-selected HF hosting and the
shared adapter passed synthetic protocol/parity checks. [Hosted configuration](../data/HOSTED_EMBEDDINGS.md)
records the evidence; real corpus retrieval quality remains unmeasured.

## Active engineering decisions

| ID / related old question | What remains open | Recommended starting point / how to close | Module / impact |
| --- | --- | --- | --- |
| O01 / Q05 | Current team-key validity, quotas/rate/concurrency limits and expiry | Reuse the privately supplied team key; limited 8B/70B calls passed. Confirm deployment limits through [inference config](../data/INFERENCE_CONFIGURATION.md); no confidential inputs | Models/operations; live deployment input, not missing transport code |
| O02 / Q05,Q15 | Keera JSON Schema/tool dialect, usage, max input/output, streaming and timeout behavior | Chat Completions non-streaming first, non-thinking tools; verify actual responses before selecting structured-output mode | Models/workflows |
| O03 / Q15 | Served Apertus weight revision, prompt/template versions and tokenizer access | Record aliases as served IDs, obtain version provenance; never invent immutable hashes; use compatible tokenizer limits | Models/evaluation |
| O04 / Q06,Q15 | Corpus/query acceptance and throughput for the configured HF encoder | Endpoint/image/model revision supplied; 768d exact-token query/document parity passed. Use identical verified JSON for build and runtime; evaluate real corpus latency/recall | Embeddings/data; no remaining missing HTTP adapter |
| O05 / Q15 | Actual HF endpoint billing, credit eligibility, region, quotas and data handling | Hosted use explicitly selected; confirm with endpoint owner. No assumption of Swiss residency, pooled credits or offline operation | Embeddings/operations |
| O06 / Q15 | Real-corpus reranker quality, target-host packaging and controlled latency | Compact multilingual MiniLM revision/runtime provisioned on Elia; real 30-hit probe passed. Compare reviewed relevance with RRF/BGE; see [setup](../data/RERANKING.md) | Reranking |
| O07 / Q17 | Deploy and supervise the implemented API/worker on the actual host | FastAPI/CLI/LangGraph are integrated; assign process owner and verify restart behavior on target infrastructure | API/operations |
| O08 / Q17 | Transfer prepared per-user bundles, confirm peer access and pilot-profile grants | Eric reports shared 0008 and verified live bindings; Renato has peer checkpoint/S3/HF checks. Confirm combined live case-to-PDF, server forwarding policy and direct checkpoint credential trust boundary; publication is optional in live mode | API/security/deployment |
| O09 / Q17 | Validate integrated HTTP frontend against the populated shared environment | OpenAPI, safe errors, pagination, polling and real client are implemented; local synthetic browser smoke passed | API/frontend/deployment |
| O10 / Q18 | Evaluate prompt/task quality and resource budgets on representative corpus cases | Ports, graph and bounded settings are implemented; benchmark passage/context sizes, retry costs and evidence coverage before tuning defaults | Workflows/models/evaluation |
| O11 / Q18 | Representative quality and thresholds for implemented extraction/support/draft tasks | Fixed prompts, bounded repair and independent semantic assessment exist; evaluate omissions, contradictions and exact wording on reviewed real cases | Evidence/validation; synthetic labels alone do not establish accuracy |
| O12 / Q14 | Monitor private SearXNG upstream availability and provision worker crawler assets | SearXNG DuckDuckGo/Yahoo passed live pilot queries; browser HTML challenged. Crawl4AI stays isolated. CAPTCHA/blocks are unavailable; public capability queries only; [setup](../data/WEB_RESEARCH.md) | Research/tools |
| O13 / Q01,Q14 | Corpus acquisition completeness, page/PDF formats, chunking, access/refresh rules | Inventory plus three source families; validated snapshots; record exclusions and freshness; bulk ingestion remains separate | Ingestion/data |
| O14 / Q18 | Published reviewed taxonomy/profile pins and corpus assignments | MeSH category/subcategory + document subject support is implemented; import/review actual contents, preserve broader/related distinctions and unknowns; other domains use profiles | Taxonomy/interpretation |
| O15 / Q08 | Partner acceptance of implemented PDF layout and larger real reports | Deterministic renderer, company introduction, kept-only citations, fonts/logo and visual fixtures verified; PPTX remains later | Reports/evaluation |
| O16 / Q18 | Live inspection of recorded query/evidence lineage, structured result metadata, explicit formatting-only chat UX and connected PPTX | HTTP, source badges, review/hash gates and PDF remain; board replaces desk/actions screens. Demo PDF/PPTX exist; backend PPTX and evidence-backed optional hierarchy/expertise fields remain. Query/evidence links now derive from actual retrieval and exact mirror identities; unrecorded ontology mappings remain absent | Frontend/API |
| O17 / Q06,Q16 | Runtime placement, Windows normal bootstrap verification and offline packaging | Migration complete: [host result](../team/MIGRATION_STATUS.md). Apply [LF fix](../data/WINDOWS_SHELL_FIX.md). Hosted HF/Keera require connected mode; offline needs local assets | Operations |
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
