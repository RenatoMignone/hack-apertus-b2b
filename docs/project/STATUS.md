# Current development status

19 October 2026. Current backend work is on `codex/backend-research-completion`,
based on merged `main` at `e406d2b`. See the
[backend checklist](../team/RUNTIME_CHECKLIST.md) and
[implementation/acceptance handoff](../team/BACKEND_RESEARCH_COMPLETION.md).
Earlier team handoffs are dated evidence, not the current backlog.

| Area | Implemented / measured | Still needed |
| --- | --- | --- |
| Backend | Authenticated HTTP API, durable LangGraph, typed interpretation/extraction/support/fit/draft tasks, frozen packs and reviewed PDF | Real-provider partial report → reviewed PDF passed; improve expert coverage and demonstrate target-host restart/resume |
| Corpus | Shared schema `0008_live_corpus`; owned live captures of ready authorized evidence while ingestion continues | Coverage/source-context quality; reviewed publication is optional for live development |
| Inference | Actual 70B interpretation verified; reproduced Helvetic activity-label failure addressed without weakening factual checks; safe failure-stage/task details | Full-case quality, factual omissions, budgets/latency and deployment quotas |
| Research | Independent lexical/vector + RRF; gap-driven novel queries, accumulated evidence/claims; exact source-context expansion; case-local web integration | Real combined DB/web acceptance and useful extraction from the current corpus |
| Reranking | Pinned compact multilingual CPU model, integrity manifest, exact windows and lazy runtime; real authorized 30-hit probe passed | Human-reviewed fused/reranked quality and controlled latency comparison; target-host packaging |
| Search lineage | Recorded query → canonical evidence paths stored in pack and exposed through existing HTTP trace | Live UI inspection; explicit ontology/phrase mappings remain absent when not actually recorded |
| Frontend | HTTP default, explicit mocks, review/hash gates and backend PDF; demo-only browser PDF/PPTX | Live structured hierarchy/expertise fields, explicit formatting-only chat UX and connected PPTX |
| Access | Renato reports working peer readiness/bootstrap; Elia's pinned key-only SSH and DB live binding/schema now verified | Elia’s supplied separate credentials are applied privately; all network readiness checks and authenticated API capabilities pass. Real case/PDF acceptance remains |
| Operations / target | Recovery tests, checkpoint/tracing adapters and deployment definitions | Host supervision, checkpoint row-isolation review, retention/restore and demonstrated required deployment target |

## Verification boundaries

The updated `main` baseline passed **224 backend tests** on Elia's disposable local
PostgreSQL. The final expanded branch suite passes **241 tests**, including all database tests.
Details are in the branch handoff. Existing frontend verification remains
11 tests/build plus a synthetic browser-to-PDF smoke from 18 October; frontend code
was not changed by this backend task.

A real HF/hybrid/local-reranker probe used the fictional Helvetic request and actual
authorized public corpus. It created/cancelled its own case/run and changed no
source artifacts, grants, ingestion or migrations. It is not a quality benchmark.
An early isolated model-task probe returned no-match. The actual worker later
extracted and supported six claims, then exposed an oversized fit-context payload;
that payload is now bounded to accepted support. A subsequent same-pack drafting retry passed with canonical source context;
all five cards were reviewed and a kept ARTORG capability exported to an actual
66,979-byte PDF. This is a partial report, not an expert-search quality benchmark. Preserve exact support and close context/quality gaps
rather than claiming that reachable infrastructure means acceptance.

Eric reports separate Elia checkpoint/MinIO credentials with host-side saver,
storage and real-source hash checks. The user subsequently supplied Elia’s separate credentials directly; they are
applied to the ignored `.env`. Network readiness passes and API/worker are running. Separate
checkpoint logins still share checkpoint rows; do not claim direct-DB isolation.

## Next actions

1. Audit the frontend against the running HTTP API; fix clarification, retry and
   unsupported-control gaps. Local real-provider partial PDF acceptance now passes.
2. Renato reviews the branch and repeats the permitted Helvetic case. Inspect
   safe failing task/stage, source identity context, direct/adjacent fit and gaps.
3. Demonstrate real cited results → all-card review → backend PDF and controlled
   worker restart/resume. Check combined DB/web deduplication and provenance.
4. Build human-reviewed evaluation cases; measure entity recall, factual support,
   reranking quality/latency and representative resource budgets.
5. Select/demonstrate the required deployment architecture. Connected Keera/HF
   development does not prove air-gapped or Swiss sovereign operation.

Keep `docs/team/` for current integration evidence and bounded handoffs. Start fresh
feature branches from updated `main`; do not reset completed teammates' branches.
