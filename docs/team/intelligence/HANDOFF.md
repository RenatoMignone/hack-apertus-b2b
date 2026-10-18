# Intelligence/report lane handoff

**18 October 2026 · Lane B implemented; composition and real-case quality pending.**
Branch: `backend/intelligence`. Isolated worktree; no main merge, shared-host
migration or modifications to frontend/data/workflows/config/env/locks. Eric's
credentials/SSH and database were not needed or used for this lane.

## Exact upstream contracts

- A's contracts-only `77bf4f8` is integrated as cherry-pick `751b2b5`.
- A's additive PDF support fix `1216c23` is integrated as `6498464`.
  `PdfInput.claims` now resolves draft claim IDs to exact evidence IDs. No
  transitional citation resolver or independent shared DTO copy remains.
- On integration A should recognize those equivalent cherry-picks; do not
  replace its service file with a handwritten copy. Existing data/pipeline DTOs
  remain unchanged.

## Factories and v1 readiness

```python
from backend.evidence import create_reasoning_services
from backend.models.reasoning import ModelSettings
from backend.reports.rendering import create_pdf_renderer

# A's composition root supplies private configuration and authorized RunContext.
reasoning = create_reasoning_services(ModelSettings(
    base_url=settings.llm_base_url, model_name=settings.llm_name,
    api_key=settings.llm_api_key,
))
pdf_renderer = create_pdf_renderer()  # optional packaged logo_path override
```

The `settings.*` attributes above illustrate A's mapping, not an assertion that
the current shared Settings already contains them. B reads no environment file
in production. Extra injectable factory kwargs: `model` (explicit test/local
LangChain model), `transport` (HTTPX transport), `receipt` (safe telemetry callback),
`token_counter` (compatible chat-template counter when an input token limit is set).

| v1 method | Implementation | Input → output | Checks/errors |
| --- | --- | --- | --- |
| `interpret` | `backend.evidence.services.ApertusReasoningServices` | Full message + reviewed taxonomy + context → `CaseInterpretation` | Blocking ambiguity, taxonomy ID membership, original exclusions; unavailable/budget/invalid output |
| `extract` | Same service | Interpretation + `ResearchBundle` → `ExtractionBatch` | Local keys, known evidence, literal entity labels, no canonical-ID invention; one bounded repair |
| `assess` | Same service | `PersistedClaims` + remapped records → `EvidenceAssessment` | One exact statement/support assessment per claim; unsupported/contradicted remain distinct |
| `propose_pack` | Same service | Interpretation + claims/assessments/research → `ReportEvidencePack` proposal | Supported-only, supplied evidence membership, need fit, conditional arguments, unchanged source flags; A freezes |
| `draft` | Delegates to `reports.generation.draft_report` | Frozen pack + editorial instruction → `DraftRevision` | Claim-backed reasons, direct/idea, gaps, no fake trace/leads; `DraftEvidenceGap` routes back to research |
| `assess_draft` | `reports.validation.assess_draft` | Exact draft + pack → `DraftAssessment` | Code computes hash; independent semantic verdict; rejection is not silently rewritten |
| `PdfRenderer.render` | `reports.rendering.ReportLabPdfRenderer` | Authorized `PdfInput` → PDF bytes | Revalidate keys/claims/evidence, adjacent labels, only kept content/citations; deterministic and no model/network |

Use shared `ServiceUnavailable`, `BudgetExceeded`, `InvalidModelOutput` and
`EvidenceRejected`. `DraftEvidenceGap` is an `EvidenceRejected` subtype exposing
`gaps`; no new shared failure DTO is required. Cancellation propagates. Diagnostic
callbacks cannot block the case and receive only task/model/timing/token counts.

## A/C integration sequence

1. A persists input and interprets against C's reviewed/pinned taxonomy. The
   expected taxonomy projection is `{"concepts": [{"concept_id": "...", ...}]}`;
   `id` is also accepted. Unknown terms use no concept ID, not a fabricated one.
2. C supplies research and exact `EvidenceRecord`s. B extracts proposals; C
   persists/remaps local keys and support into canonical case-safe identities.
3. A refreshes C's evidence projection **after remapping**, then B assesses those
   exact canonical statements/support. Pass the same remapped records to pack
   proposal. An assessment for an earlier statement/support is rejected.
4. A records assessments, seals the case manifest and freezes the supported
   pack using its existing repositories. B's pack is only a proposal.
5. B drafts and assesses exact wording; A persists only a supported exact-hash
   draft. Wording changes require new assessment, focus changes require research.
6. After A's all-reviewed + one-kept/current-result/selection-hash gate and access
   recheck, pass draft + **supported pack claims** + authorized evidence to
   `PdfInput`. B cannot verify database approval/revocation from bytes alone.
7. A stores/registers the returned bytes and serves an authorized download.
   No artifact registration or persistence happens in B's renderer.

No autonomous search/tool loop is implemented here; A's LangGraph owns it. B's
tool interface only proposes allowlisted JSON-schema-validated calls. Offline
cannot contact hosted Keera; explicit local/loopback models require separate setup.

## Dependencies and verification

Proposals are in [requirements.in](../../../src/backend/models/reasoning/requirements.in).
A owns the merged lock/manifest. Tested on macOS arm64 / Python 3.13.16 with the
existing lock plus ReportLab 5.0.1, pypdf 6.21.1, pypdfium2 5.14.0 and
jsonschema 4.26.0. PDF verification packages need not be production dependencies.
No tokenizer, model weights, database service or renderer system binary installed.

```bash
PYTHONPATH=src .venv/bin/python -m pytest src/backend/tests/intelligence -q
PYTHONPATH=src .venv/bin/python -m pytest src/backend/tests -m 'not integration' -q
```

The final full non-database suite passed **70 tests, 27 deselected** in 0.91 s.
These include the existing unit suite, A's contracts and lane B's checks. Coverage:
malformed JSON/one repair, exact aliases, auth/rate/timeout/cancellation, offline,
thinking/tool restrictions and proposal schemas, negative/ambiguous intent,
local extraction keys, missing/contradicted claims, supported-only packs,
exact draft hash, missing-support gaps, invented leads/trace, PDF selection and
citation membership, byte determinism, Unicode, long pagination and XML escaping.

Actual sample PDFs were generated from fictional fixtures, reopened with pypdf,
rendered with PDFium and visually checked: one normal page and both pages of the
long multilingual fixture; no clipping/overlap. Generated files stay ignored under
`.local/intelligence/`; originals/template/logo remain unchanged. Invalid selections
and missing support are rejected. No live DB/SSH, full application run, real
retrieval quality or PDF artifact registration was tested by this lane.

## Live models and remaining gaps

[Measured comparison](MODEL_COMPARISON.md): authenticated Keera works, but the
tiny paired diagnostic shows no overall winner. 70B missed an explicit extraction
fact and rejected its own implied collaboration; 8B extracted useful content but
failed draft constraints. Both passed the three synthetic contradiction/support
labels. Keep the configured default; broader independently reviewed evaluation
and A's task-specific routing decision are needed. No automatic model switching.

Open integration work owned elsewhere: actual HTTP/LangGraph composition,
reviewed taxonomy/corpus, verified tokenizers/context limits, real role/scope
projections, model budget/usage persistence, authorized export registration and
frontend projection. B's source flags are not source certification. No PPTX,
economic calculations, charts, historical cases or confidential PDF ingestion.

If deploying as a wheel, A must package the supplied challenge-only logo and
inject `logo_path`; renderer imports ReportLab lazily and fails unavailable when
its library/font/logo is missing. No assets are fetched at runtime.

Canonical-doc integration requests: mark B's methods/renderer implemented in
module/processing/open-question docs while retaining live quality limitations;
record exact upstream contracts and the additional PDF claims mapping. Only the
integrator updates those shared documents, manifests and defaults.
