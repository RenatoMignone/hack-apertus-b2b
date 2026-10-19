# Partner-provided material

This directory is the canonical location for the three original partner files.
Application configuration, ingestion and container packaging reference these paths.

**Received and inspected:** 18 October 2026, following the user's message that
the partner material is now in `docs/`. Preserve the three original files.
Inspection was read-only: workbook and presentation XML, plus logo image viewing.
No PowerPoint rendering/native-app check or source-site crawl was performed.

## UniBE discovery workbook

[unibe_sous_domaines_publics_etendus.xlsx](unibe_sous_domaines_publics_etendus.xlsx)
has two sheets:

- `Sous-domaines UniBE`, range `A1:C43`: headers `Sous-domaine`, `Description`,
  `URL`, followed by **42 populated entries**. Of these, 41 are UniBE-domain
  entries and one is DCB (`dcberne.com`, row 43).
- `Notes`, range `A1:B8`: describes best-effort public web discovery dated
  **4 September 2026**, warns that entries may be old/redirected, and explicitly
  does not guarantee exhaustive DNS coverage.

**Count discrepancy:** `Notes!B5` says 71 subdomains, while the supplied data
sheet contains 42 entries. Use the actual rows; retain the original note and
flag the mismatch rather than inventing 29 missing records.

Use column C URLs as discovery candidates. Column A sometimes omits `www.`
present in column C; validate redirects/aliases rather than concatenating host
labels into URLs. Log workbook hash, sheet, row and original values when importing.
Validate the parsed hostname, not substring membership in `unibe.ch`.

Pilot-relevant entries include medicine (row 5), BCPM (21), DBMR (22), ARTORG
(33) and DCB (43). These are discovery leads, not claims that all their pages
match diabetes technology. Topic-relevant linked units can be added through
discovery. DCB is a separate host despite appearing in a UniBE inventory.
Astronomy/geology and other unrelated entries should not outrank healthcare
content merely because they are in the workbook.

**Resolved context conflict:** earlier user guidance said no official inventory
existed. A partner-supplied best-effort discovery workbook is now available and
is the initial map. Its own provenance does not establish an authoritative,
complete university DNS inventory. There is no longer a missing-file dependency.
Robots, access restrictions, relevance and live reachability still need checks.

SHA-256: `9A98F3631C01BB8A16C222B7958363492277A97C038FEA565843AC5619E65B8C`.

## PowerPoint template

[powerpoint_template.pptx](powerpoint_template.pptx) contains **19 example slides**,
**15 slide layouts**, and a **16:9** slide size (12,192,000 × 6,858,000 EMU).
The examples cover titles, sections, agenda, content, text/image arrangements,
tables, charts, a color palette and a closing contact slide.

Use this supplied design as the export baseline, selecting suitable layouts for
the concise company deck. Nineteen example slides do not mandate a 19-slide
output. Preserve theme/master/layout behavior and editable content. The template
is an example deck, not evidence for company profiles, economic figures or
contacts. Its visual fit must be rendered and checked when implementing export.

Observed placeholders/instructions to replace or remove in generated copies:

- German headings, lorem ipsum and example chart/table data.
- Template instructions, including image-replacement notes and bullet-level
  guidance; follow the paragraph-level style without exporting its instruction slide.
- Repeated `Klassifizierung: intern / vertraulich / geheim` footer text. This is
  template text, not a classification of the supplied material or final output.
  Use an actual agreed output label if needed, otherwise omit it.
- Presenter/unit placeholders, fake contact details, document IDs and fixed
  dates/page numbers. Do not populate contacts without supplied or public evidence.

English is the output baseline even though the source template is German.
Keep citations/limitations with claims, and use source notes or an appendix
without shrinking content below readable template sizes.

SHA-256: `A2F5E50FF7B986FE6A5A2F38654BF5459142EA9285E844E12AA9392F20F7A262`.

## English agency logo

[Logo_SF_BE_EN.png](Logo_SF_BE_EN.png) is an **838 × 269 pixel** image bearing
the English Bern Economic Development Agency wordmark and red graphic.
Use the supplied original, preserving proportions and legibility. Do not redraw,
stretch or infer additional branding rules. N1 explicitly restricts this logo and the PowerPoint template to use for this
challenge; see [the supplied source snapshot](../sources/NOTION_CHALLENGE_2026-10-18.md).
Do not reuse them for unrelated projects or assume broader redistribution rights.

SHA-256: `FDE725FE9D25F858003DA6256F89F6420CE23C4BEB3B6C230764507EC87BDFB9`.

## Use in the application

The workbook seeds controlled public-source discovery; it is not source evidence.
The slide template and English logo are challenge-only output assets. Preserve
original bytes. [Rich outputs](../data/RICH_OUTPUTS.md) describes backend template
rendering; [delivery](../judges/DELIVERY.md) covers final submission artifacts.
