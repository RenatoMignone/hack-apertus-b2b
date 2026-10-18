# Current development status

**19 October peer update:** see the [current backend checklist](../team/RUNTIME_CHECKLIST.md).
Renato's live binding, readiness and production bootstrap pass; 224 isolated
backend tests pass. Real Apertus interpretation/repair and keyless research tools
are verified separately; full real-provider case-to-PDF remains pending.

Live ingestion runtime (18 October, explicitly authorized by Eric): backend source
head is `0008_live_corpus`. `RUNTIME_CORPUS_MODE=live` creates case-owned captures
of ready authorized chunks, so cases no longer require completed publication.
New users receive a narrow corpus-read/case-write role. See
[deployment](../data/LIVE_CORPUS_RUNTIME.md) and the
[runtime access receipt](../team/RUNTIME_ACCESS_STATUS.md) for host rollout.
Earlier publication prerequisites below describe the reviewed-release path.

18 October 2026 · Integrated baseline plus Eric's published migration outcome
(`9367b9b`), runtime preparation, Renato’s acceptance fixes and refreshed UI.
This is the current status entry point; the [open register](OPEN_QUESTIONS.md)
owns remaining decisions and the [integration record](../team/INTEGRATION.md)
owns merge/test evidence. Historical lane docs describe earlier checkpoints.

| Area | Implemented / verified | Still needed |
| --- | --- | --- |
| Backend | Authenticated FastAPI, durable LangGraph worker, real reasoning/retrieval adapters, exact evidence assessment, frozen packs, drafts and reviewed PDF | Run against the actual corpus and providers on the selected host |
| Frontend | HTTP by default; explicit mock mode, polling/clarification, history, flags/actions, source badges and authenticated PDF download | Shared-environment acceptance; detailed real Sankey lineage, live structured result metadata and explicit formatting-only chat UX |
| Database | Migration head `0008_live_corpus`; case-owned live captures and restricted runtime users; 51 isolated runtime/access checks pass | Shared host 0008 and both user bindings verified after backup; see [runtime access status](../team/RUNTIME_ACCESS_STATUS.md) |
| Corpus / RAG | Collection, registry/MeSH, build/publication CLI, hybrid/relationship retrieval and local model adapters | Real HF encoding/parity verified; Eric is ingesting. Reviewed pilot corpus and published snapshot/profile pins remain |
| Inference | Configurable Keera Apertus; authenticated synthetic 8B/70B probes | Current key/quotas, tokenizer/revision provenance, full-case quality and resource budgets |
| Infrastructure | Compose definitions, individual SSH access design, storage/checkpoint/tracing adapters | Eric reports private bundles, checkpoint roles and synthetic saver/S3 writes verified host-locally; peer access and pilot pins remain. Apply [LF checkout fix](../data/WINDOWS_SHELL_FIX.md) on the Windows host |
| Offline / Swiss target | Mode checks, disabled web offline, local-assets policy and dependency inventory | Full packaged, network-disabled run; any Swiss residency/jurisdiction claim needs evidence |
| Later outputs | PDF implemented | Editable PPTX, supported numeric impact/charts and eligible historical-case similarity |

## Verification and remaining deployment gates

Original integration: **153 backend tests**, **8 frontend transport tests**, build
and synthetic browser-to-PDF on disposable PostgreSQL. These remain dated results.
Renato’s `66dbfd1` adds an explicit isolated-test-DSN guard and reports **119 passes,
58 skipped** under a sandbox workaround; his live acceptance was not completed.
See [his exact scope](../team/BACKEND_RUNTIME_ACCEPTANCE.md).

Eric’s [reported access handoff](../team/RUNTIME_ACCESS_STATUS.md) establishes
host-local checks only: separate private bundles, checkpoint read/write and S3
synthetic put/read. His original operational-metadata commit was not published.
Neither developer’s peer-side SSH is proven by those checks. Elia’s route failure
remains unresolved. There is **no published pilot snapshot/index build** in this
latest handoff; an unpublished trial profile is not usable runtime publication.

Latest UI adds board-as-home, infrastructure cards and optional result fields.
HTTP PDF retains backend hash/review gates. Browser PDF/PPTX are demo-only;
live metadata and connected PPTX need coordinated backend support.

## Next actions

1. Transfer each private bundle securely; verify developer-side SSH and run the
   read-only readiness check. If Renato can connect outside his sandbox, he can
   lead live acceptance while Elia’s route is diagnosed separately.
2. Eric/admin confirms key-only SSH and forwarding restrictions after validating
   working keys; retain ingestion and private service ports. Review direct
   checkpoint credential isolation before stronger multi-user deployment claims.
3. Corpus owner completes reviewed UniBE/ARTORG/DCB publication and delivers
   profile/snapshot/build/taxonomy/config pins plus access grants and coverage.
4. Run one permitted real case through clarification, cited evidence, review and
   actual PDF. Record provider latency, stage outcomes, gaps and exact support.
5. Measure quality/deployment claims and finish submission materials. PPTX/economics/
   historical cases remain extensions; demo exports do not complete backend work.

## Working together

Everyone fetches and fast-forwards a clean local `main`, then creates a new
feature branch (`codex/<feature>` for agent work). Completed backend and UI
branches remain historical references; no routine branch reset/re-alignment is
needed. Assign one integrator per shared contract/config/migration change.
Frontend ownership continues; backend/docs tasks leave `src/frontend/` unchanged.

Keep `docs/team/`: current integration evidence and service boundaries are useful.
Its [index](../team/README.md) marks old prompts/lane instructions as historical;
do not rerun them as a new development plan. Requirements, supplied originals,
recordings and decision history remain distinct from the current backlog.

## Latest merged verification — 18 October 2026

On this Mac, the merged code passed **177 backend tests**, including all 58
PostgreSQL integration tests, on isolated local PostgreSQL 18.0 / pgvector 0.8.1.
No asyncio polling workaround was used. The first attempts were blocked by socket
sandboxing and an incorrect local admin role; the final run used the isolated
cluster’s configured administrator with approved local network access.
Frontend clean locked install, **11 tests** (8 transport + 3 export-policy),
TypeScript/build passed; npm reported zero vulnerabilities. Browser export bundles
produce size warnings; demo PPTX visual/PowerPoint compatibility is not certified.
These are synthetic engineering checks, not real corpus/provider acceptance.

Merged browser smoke also passed against the isolated synthetic API/worker:
board home, authenticated case creation, cited result, unavailable-trace wording,
blocked export before review, kept selection, exact-hash review, queued export and
HTTP 200 PDF download. Connected export offered PDF only. Source providers and
company input in this smoke were synthetic; no shared host was contacted.
