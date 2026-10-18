# Current development status

18 October 2026 · Documentation audit against integrated `main` at `4c6cfe2`.
This is the current status entry point; the [open register](OPEN_QUESTIONS.md)
owns remaining decisions and the [integration record](../team/INTEGRATION.md)
owns merge/test evidence. Historical lane docs describe earlier checkpoints.

| Area | Implemented / verified | Still needed |
| --- | --- | --- |
| Backend | Authenticated FastAPI, durable LangGraph worker, real reasoning/retrieval adapters, exact evidence assessment, frozen packs, drafts and reviewed PDF | Run against the actual corpus and providers on the selected host |
| Frontend | HTTP by default; explicit mock mode, polling/clarification, history, flags/actions, source badges and authenticated PDF download | Shared-environment acceptance; detailed real Sankey lineage and explicit formatting-only chat UX |
| Database | Migration head `0007_frontend_lifecycle`; fresh/upgrade and restricted-role tests | Confirm Eric's actual revision; coordinate backup/upgrade if behind |
| Corpus / RAG | Collection, registry/MeSH, build/publication CLI, hybrid/relationship retrieval and local model adapters | Reviewed pilot corpus, compatible real embeddings and published snapshot/profile pins |
| Inference | Configurable Keera Apertus; authenticated synthetic 8B/70B probes | Current key/quotas, tokenizer/revision provenance, full-case quality and resource budgets |
| Infrastructure | Compose definitions, individual SSH access design, storage/checkpoint/tracing adapters | Confirm actual services, runtime placement, credentials and restart behavior |
| Offline / Swiss target | Mode checks, disabled web offline, local-assets policy and dependency inventory | Full packaged, network-disabled run; any Swiss residency/jurisdiction claim needs evidence |
| Later outputs | PDF implemented | Editable PPTX, supported numeric impact/charts and eligible historical-case similarity |

Latest integration verification: **153 backend tests**, **8 frontend transport
tests**, frontend build, local browser-to-PDF smoke and PDF visual inspection.
These used disposable PostgreSQL 18.0 / pgvector 0.8.1 and synthetic model responses
and embeddings. Earlier host/lane results use different environments and counts;
see their dated records. This docs-only audit does not rerun those suites or
establish real-model accuracy, target-host readiness or a submission-ready package.

## Next actions

1. **Eric + rollout operator:** confirm host schema/service state, agree a backup
   and upgrade window. Eric will perform the migration; use the [complete prompt](../team/prompts/04_SHARED_HOST_MIGRATION.md).
   Migration execution can be delegated; SSH access alone
   does not supply the required database role. Follow [live setup](../data/LIVE_SETUP.md).
2. **Corpus/model owner:** verify embedding runtime/assets and publish the reviewed
   UniBE/ARTORG/DCB snapshot. Deliver profile/snapshot/build/config IDs and coverage.
3. **Backend operator (you can do this):** configure private runtime bindings,
   matching embedding assets, storage and checkpoints; start API + worker.
4. **Frontend/backend owners:** test one public permitted company case through
   clarification, review and actual PDF against that runtime.
5. **Team:** measure quality and deployment claims, then complete the separate
   submission report/video. Optional output features do not block this first run.

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
