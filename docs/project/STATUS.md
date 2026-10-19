# Current development status

19 October 2026. The backend research completion and frontend integration audit
are integrated into main. See the [backend acceptance](../team/BACKEND_RESEARCH_COMPLETION.md),
[frontend audit](../team/FRONTEND_RUNTIME_AUDIT.md) and
[current checklist](../team/RUNTIME_CHECKLIST.md). The [ordered completion roadmap](../team/COMPLETION_ROADMAP.md) adds retrieval
evaluation, curation tools, own-case memory, domain profiles, process recovery,
manual plans and reviewed PPTX, with connected frontend controls. Optional source
head is `0010_rich_outputs`; shared host last verified at 0008.
[Eric must activate the optional features](../team/OPTIONAL_FEATURE_ACTIVATION.md);
flags remain false until migration/assets are ready. Earlier handoffs are dated
measurements, not the current backlog.

| Area | Implemented / measured | Still needed |
| --- | --- | --- |
| Backend | Authenticated API, durable LangGraph, interpretation/extraction/support/fit, frozen packs, checked drafting and reviewed PDF | Better named-expert/facility coverage, quality and latency evaluation |
| Corpus | Shared schema `0008_live_corpus`; immutable ready-evidence capture while ingestion continues | Coverage and source-context quality; publication is optional for live development |
| Inference | Actual Keera 70B interpretation, extraction, assessment and partial report passed; bounded context and same-pack rewrite | Representative quality, sustained quotas and resource budgets |
| Research | Independent lexical/vector + RRF, bounded novel gap queries, retained evidence/claims and exact source-context expansion | Combined real DB/web deduplication/provenance acceptance |
| Reranking | Pinned multilingual CPU model, integrity manifest, exact windows; actual 30-hit retrieval probe passed | Human-reviewed RRF/reranker quality and controlled latency comparison; other-host packaging |
| Search lineage | Actual query → canonical evidence paths stored in pack; browser diagram/text fallback verified synthetically | Real-corpus UI review; no invented ontology mappings |
| Frontend | HTTP, clarification/retry/rewrite/history, source quotes, exact PDF/PPTX review/export, optional manual plans and own-case opt-in | Optional feature activation; richer evidence-backed hierarchy/expertise metadata |
| Access | Elia’s pinned key-only SSH, DB binding/schema, checkpoints, separate MinIO credentials and source-artifact hash pass | Server SSH policy and direct checkpoint row-isolation review |
| Operations / target | Local API/worker, readiness and actual reviewed PDF pass; automated recovery tests | Controlled target-host restart/resume, supervision, retention/restore and demonstrated required deployment target |

## Measured verification

**243 backend tests passed**, including all disposable PostgreSQL tests; **15
frontend tests passed**, TypeScript and production build passed. Browser smoke on
isolated storage/synthetic providers verified intake, free-text clarification,
cited results, quotes without entry metadata, blocked unreviewed export, kept
selection, exact-hash review and downloaded backend PDF. Explicit formatting reused
the exact frozen pack. Viewing v1 left v2 active and disabled historical mutations.
Build warnings concern optional demo export bundle size, not failed checks.

The real Mac API/worker used Eric’s authorized live corpus, HF embeddings, local
reranker, Keera 70B, PostgreSQL checkpoints and separate MinIO credentials. An
initial context failure and unsupported wording were blocked and fixed. A later
same-pack drafting retry produced five partial cards with coverage caveats. All
were reviewed; one source-verified ARTORG capability was kept and downloaded as a
**66,979-byte PDF**. This is a partial acceptance result, not an expert-search or
reranking quality benchmark. No web service was configured on this Mac.

Private settings, credentials, weights and diagnostic artifacts stay ignored.
No shared migration, grant, ingestion or source-artifact change was performed.
Checkpoint logins still share rows; separate usernames do not establish isolation.

## Next actions

1. Teammates fast-forward main, preserve private settings and restart API/worker.
   Renato repeats the fictional Helvetic case with his configured web services.
2. Review named experts/facilities, direct versus adjacent relevance, exact source
   support and combined DB/web deduplication. Improve coverage without inventing data.
3. Repeat the verified disposable subprocess crash/resume on the selected deployment host.
4. Build reviewed evaluation cases; measure recall, factual support, reranking
   relevance and latency. Synthetic engineering checks are not gold labels.
5. Choose and demonstrate the required target architecture. Connected Keera/HF
   development does not establish air-gapped or Swiss sovereign operation.

Keep docs/team for current integration evidence and historical ownership records.
Start fresh feature branches from updated main; do not reset completed lanes.

## Optional completion release

Own-case comparison uses explicitly eligible reviewed non-synthetic cases only;
no automatic agency library, pitch learning or success probabilities. Domain
vocabularies come from pinned profile configuration. Curation is dry-run-first,
with immutable reviewed claim successors and audit provenance. Candidate evaluation
labels remain unreviewed, so no Recall@10/quality score is claimed. Manual plans
are operator inputs, not model estimates or economic impact. New features are
covered by isolated tests/browser verification; no shared corpus/migration changed.

Final verification: **267 backend tests passed** with disposable PostgreSQL;
**20 frontend transport/policy tests passed**, and the frontend production build
passed. Focused final capability/history/manual-output checks also passed.
Provider quality, human labels and shared feature activation are not implied.
