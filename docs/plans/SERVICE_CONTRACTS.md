# Backend service interfaces

Exact signatures and DTO constraints live in
[`contracts/services.py`](../../src/backend/contracts/services.py),
[`pipeline.py`](../../src/backend/contracts/pipeline.py) and
[`data.py`](../../src/backend/contracts/data.py). This guide explains their roles.
Factories inject implementations; no SQL or provider-specific objects cross ports.

## Run and evidence records

`RunContext` carries authorized access, case/input/run and snapshot/profile/
taxonomy/build IDs, embedding hash, deployment mode and time/token/tool/round
budgets. The application creates it; neither the model nor browser can broaden it.
`EvidenceRecord` carries exact stored source text, offsets, hashes, URL, dates,
identity, origin and review status. `ResearchBundle` combines hits, evidence,
existing entity projections and limitations. Text is untrusted data.

`ExtractionBatch` proposes local entity/claim keys and evidence IDs. Persistence
resolves canonical IDs and authorized case-scoped support. `PersistedClaims` are
proposals until assessed. `EvidenceAssessment` assesses exact statement/support
sets; unsupported claims stay outside the supported pack. `WebResearchResult`
contains normalized fetched sources and explicit status/limitations, not snippets.

## Ports

| Port | Operations |
| --- | --- |
| `ReasoningServices` | `interpret`, `revise_queries`, `extract`, `assess`, `propose_pack`, `draft`, `assess_draft` |
| `BackboneServices` | `taxonomy`, `retrieve`, `register_research`, `persist_extraction`, `read_evidence` |
| `WebResearchTools` | `discover`, `fetch` |
| `PdfRenderer` | `render` from an authorized `PdfInput` |

Calls are async and typed. Synchronous repository work stays behind adapters,
without blocking the event loop or moving live connections between threads.
Known errors have safe stable codes (`ServiceUnavailable`, `BudgetExceeded`,
`InvalidModelOutput`, `EvidenceRejected`, `StaleRevision`). Cancellation propagates.
Empty retrieval is a valid result; infrastructure failure is not no-match.

## Composition

The graph interprets, retrieves/researches, registers/deduplicates sources,
extracts, persists canonical claims/support, reloads exact evidence, assesses,
freezes a pack, drafts and assesses wording. Fixed model tasks have bounded repair;
agentic loops belong to LangGraph. Canonical corpus evidence mirrored into owned
case scope retains original derivation IDs and source review status. New web
material remains unreviewed. Reads authorize historical packs; writes require
an active input/run.

`PdfInput` includes exact revision/review hashes, kept keys, the draft,
interpretation, supported claims and evidence. Claims map claim IDs to evidence
IDs; the renderer must never guess citation identity. The application constructs
this input after the review gate. Rendering performs no research or inference.
Recorded `EvidenceHit.query_matches` and reranker windows produce observed search
lineage in pack coverage; model drafts cannot invent or overwrite that trace.
