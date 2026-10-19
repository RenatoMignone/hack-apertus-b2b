# Manual company plans and reviewed PowerPoint

Optional manual plans and reviewed PPTX require migration `0010_rich_outputs`,
`RUNTIME_RICH_OUTPUTS_ENABLED=true` and supplied template assets. Capability
responses determine browser availability; code presence alone is not activation.

## Manual data, v1

`PUT /api/v1/cases/{id}/business-context` accepts an Idempotency-Key and:

```json
{"expected_revision":1,"permitted_context_confirmed":true,"values":{"planned_jobs":5,"investment_amount":"100000.00","investment_currency":"CHF","timeline":"2027, tentative"}}
```

All four fields are optional; null/absent means unknown, zero is explicit zero.
Jobs must be a nonnegative whole number. Investment needs a nonnegative decimal
amount and explicit three-letter currency code together; no currency inference or
conversion. Timeline preserves the operator's wording and uncertainty. This is a
full replacement; `{}` clears the plans. Only permitted context is allowed.

The frontend provides manual inputs and explicit confirmation. There is **no
model extraction or suggestion**. Values stay outside reasoning/draft prompts;
code inserts them as attributed company plans into the draft view, PDF and PPTX.
They do not establish actual jobs, induced effects, GDP/tax impact or a forecast.

`cases.business_contexts` stores immutable values, input ID, operator ID and date.
Saving creates a new input revision, supersedes active old runs, invalidates old
exports and queues research. Focus edits copy existing manual context; formatting
reuses the same frozen pack. The graph freezes exact values into pack coverage,
whose hash binds the resulting draft and review. Old revisions retain their plans.
No input/report update modifies the public corpus or taxonomy.

## Export

Case detail advertises `businessContextAvailable` and `exportFormats`. The
capabilities endpoint advertises provisioned server formats. The browser shows
connected PPTX only when advertised and uses authenticated server export/download;
HTTP never falls back to browser/demo export.

The existing POST `/cases/{id}/exports` accepts `format:pdf|pptx` (PDF default).
Both require all reasons reviewed, one kept, exact result/selection hashes and an
accepted review. Worker rechecks before rendering and registration; download
revalidates current result, selections, evidence access and artifact hash. Cache
identity includes format. PPTX MIME/filename are preserved through download.

`reports/rendering/pptx.py` copies the partner's title/content slide, master,
layouts, dimensions, themes and logo bytes. It replaces editable text, numbers
slides, adds exact source passages/URLs with native hyperlinks, preserves caveats
and pages long content instead of truncating. Example slides/contacts and
unreachable package parts are removed. Deterministic ZIP metadata makes identical
input/template produce identical bytes. No new runtime dependency/network/model
is introduced. At most 200 slides and the existing bounded export payload apply.
Template assets must be packaged or set `RUNTIME_PPTX_TEMPLATE_PATH`; the container
copies them. Update renderer/template version settings when their contents change.

Verification: synthetic unit/integration checks cover kept-only rendering, exact
citations, determinism, template assets, manual validation, input revisioning,
PDF/PPTX separation and stale downloads. A seven-slide fixture rendered in actual
LibreOffice and was visually inspected; the artifact preview could not render the
template's EMF logo, while LibreOffice rendered the preserved logo correctly.
An isolated HTTP browser run saved plans and completed reviewed PPTX export.
This is not a real company/model-quality or target deployment acceptance result.
