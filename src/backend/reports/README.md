# Report generation, assessment and PDF

Implemented lane B entry points:

| Module | Responsibility |
| --- | --- |
| `generation.draft_report` | Pack-only cited reasons, adjacent labels and preserved gaps; no browsing or new facts |
| `validation.assess_draft` | Mechanical claim/label/trace checks then separate semantic assessment; code computes exact draft hash |
| `rendering.create_pdf_renderer` | Async deterministic PDF bytes from A's authorized `PdfInput`, supported claims, kept keys and evidence |

The writer cannot invent retrieval trace or mark a lead when none was supplied.
`DraftEvidenceGap` is an `EvidenceRejected` subtype with `gaps` for A's next
research step. Explicit no-match drafts need no model call. A remains responsible
for freeze/persistence, all-reviewed + one-kept approval and exact result/selection
hash/revocation checks before calling the renderer. Editorial choices are not
truth approval.

PDF imports ReportLab lazily, embeds its packaged Vera fonts and uses the supplied
challenge-only English logo without modification. No network/inference/retrieval.
Export includes an attributed company introduction, Bern objectives and needs
from the frozen interpretation, followed by kept reasons and exact passages.
The worker supplies `PdfInput.interpretation`; legacy direct renderer callers
may omit it. Sources retain
dates, public URLs, origin/review flags and caveats. Invalid/unmapped kept claims
or missing support are rejected. Identical input produces identical bytes.
Missing library/logo/font is unavailable. The packaged logo must remain accessible
or A must inject `logo_path` when deploying an installed wheel.

Actual one-page and two-page multilingual fixtures were rendered and visually
inspected. PPTX and charts/economic calculations remain later work.
See [integration](../../../docs/team/INTEGRATION.md) for current wiring/dependencies
and [original handoff](../../../docs/team/intelligence/HANDOFF.md) for provenance
and model comparison limitations.
