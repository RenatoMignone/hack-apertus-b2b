# Selected pilot — Diabetes technology in Bern

**Decision date:** 18 October 2026. **Authority:** user delegated medical-slice
selection and evaluation design to the agent. **Status:** selected documentation
scope based on public-page investigation; no corpus, benchmark or matches built.

## Selected focus and rationale

Focus on **diabetes technology**, with glucose monitoring, automated insulin
delivery and supporting digital/AI tools as the core demonstration. Nutrition
estimation and clinical/translational validation are adjacent capabilities when
sources support them. This provides concrete company needs, meaningful synonym
tests and research-to-product connections across all three required families.

The choice is an inference from these first-party sources, inspected through
web retrieval on 18 October 2026:

- **UniBE beyond ARTORG:** the [DBMR Bally Lab](https://www.dbmr.unibe.ch/research/research_programs/bally_lab/index_eng.html)
  describes automated insulin delivery, physiological modeling and wearable
  digital biomarkers. This is a distinct UniBE research entry point, rather
  than counting ARTORG twice as the entire university contribution.
- **ARTORG:** the [research directory](https://www.artorg.unibe.ch/research/index_eng.html)
  links engineering groups and associated diabetes/sensor expertise. Its
  [Intelligent Nutrition page](https://www.artorg.unibe.ch/research/aihn/research_activities/intelligent_nutrition/index_eng.html)
  describes meal carbohydrate estimation and a diabetes-related validation
  example. Its [Adaptive Diabetes Management page](https://www.artorg.unibe.ch/research/aihn/research_activities/adaptive_diabetes_management/index_eng.html)
  supplies another topic-specific discovery seed.
- **DCB:** its [research page](https://www.dcberne.com/en/projects/) exposes
  glucose-monitoring and automated-delivery-related project entries. Its
  [10 April 2026 announcement](https://www.dcberne.com/en/four-dcb-professorships-advance-research-in-diabetes-technology/)
  describes its diabetes-technology research network.

These observations establish discovery relevance, not expertise availability,
clinical performance or willingness to partner. Team/person claims must be
checked against current profile evidence during ingestion. Page inspection is
not a production crawl, robots audit or redistribution permission grant.

## Initial discovery seeds

Use the exact pages linked above, plus the institutional landing pages
[UniBE](https://www.unibe.ch/), [ARTORG](https://www.artorg.unibe.ch/) and
[DCB](https://www.dcberne.com/en/). DCB's observed research path is `/en/projects/`;
do not invent `/en/research/` as a working seed.

**Later material received, 18 October:** a
[partner-supplied discovery workbook](../provided_material/README.md) is now
available, superseding the missing-file assumption. Its own Notes describe a
best-effort inventory, not exhaustive DNS coverage. Use its 42 actual entries
(41 UniBE-domain entries plus DCB), not the inconsistent Notes count of 71.
Start with medicine/DBMR/ARTORG/DCB candidates, then extend through public
links/sitemaps, retaining origin, source row, scope decision and fetch status.
Within the authorized UniBE ecosystem,
validate the exact `unibe.ch` domain or subdomain suffix, then apply each origin's
robots/access rules and topic/geography relevance. Never accept lookalike suffixes.
External sites still require relevance/ownership checks and their own policies.

The user's permission to collect robots-allowed public pages replaces a blanket
requirement for separate human approval of every source. Check robots and known
published access restrictions automatically where possible; review actual
ambiguities/blocks. Public availability does not establish redistribution rights.
No bulk collection is authorized by this documentation update alone.

## Coverage, expansion and languages

Collect useful public websites first: units, teams, capabilities, facilities,
services and project pages. Public linked PDFs are secondary; additional formats
can be added when they contain relevant information and have a verified parser.
There is no user-imposed fixed page cap, but engineering quotas, relevance
priorities and explicit coverage reporting remain necessary. Discovery breadth
must not be reported as exhaustive university coverage.

Start with partner-provided institutional/company references already captured
in this repository. Add healthcare-related organizations only with evidence of
a location or operation in the Canton of Bern. A DCB competition participant or
partner is not automatically Bern-based. International companies may still be
case subjects; they do not become Bern ecosystem suppliers without evidence.

**Language decision:** English interface, interpretation, results and slides
are the required baseline. Preserve source text in its original language. Support
German/French/Italian source ingestion and query interpretation where feasible,
with English explanations and cross-language retrieval checks. Localized output
in those languages is desirable, not an initial acceptance gate. Do not claim
Italian source coverage unless relevant Italian material is actually collected.
Translations are labeled derivations and retain original evidence references.

## Starter scenarios and partner inputs

Use these synthetic needs for initial engineering, then incorporate the public
or appropriately anonymized examples the user says the partner can provide:

1. A glucose-sensor company seeking Bern expertise for monitoring R&D.
2. An insulin-delivery company seeking control/algorithm research and validation.
3. A digital diabetes company seeking nutrition-estimation capabilities.
4. Equivalent lay/scientific wording and German/French/Italian variants of the
   same intent, judged against the same verified expected entities.
5. Ambiguous sensing terms, explicit exclusions, and a deliberately unrepresented
   capability in a fixed snapshot, with honest abstention/coverage reporting.

No partner examples or expected sets have been received yet. Availability is
confirmed, delivery pending. Ask for permitted need text, expected typed
experts/units, supporting sources and reviewer notes when assembling the pilot.
This does not establish the availability of a historical-case corpus.

## Evaluation decision

Use an internally defined **macro Recall@10 >= 0.80** as the primary positive-query
acceptance rule. This operationalizes the brief under the user's delegation;
it is not claimed as an organizer-issued aggregation formula.

Each independently reviewed intent has a gold set of typed entity IDs: person
or unit. Return up to ten unique typed entities in a shared ranked list. A
person cannot substitute for their unit, or vice versa; duplicate profiles and
repeated evidence do not create additional hits. Report person-only and
unit-only recall diagnostics separately when the relevant gold subsets exist.

For intent `i` and variant `v`, calculate:

```text
recall(i,v) = |gold(i) intersect top10(i,v)| / |gold(i)|
intent_recall(i) = mean of recall(i,v) across its frozen wording variants
primary_macro = mean of intent_recall(i) across positive intents
```

Report every variant score and micro recall as secondary diagnostics. The
English-only primary run is mandatory; report multilingual extension results
separately, using the same intent grouping within each declared language suite.
This prevents adding many easy paraphrases from overweighting an intent. Freeze
the query suites, source snapshot and gold sets before the reported evaluation.

Gold sets exceeding 12 entities cannot reach 80% within ten results. Retain and
report such cases and attainable bounds; do not remove expected entities after
seeing rankings. Form narrower, meaningful questions before freezing the suite
where needed, and identify broad discovery queries separately.

Negative/unrepresented intents are excluded from recall division and assessed
for honest abstention. Report complete factual-claim support and required-family
coverage as separate gates: a good aggregate recall does not excuse fabricated
claims or a missing institution. Empty gold-type subsets are not scored as 100%.

## Freshness and deferred inputs

**Proposed refresh policy:** build a dated initial snapshot; before the final
demo, conditionally refresh mutable profiles/projects and selected evidence as
access and time permit. Display retrieval dates and source dates separately.
Treat inaccessible updates as stale/unknown, not freshly verified. No continuous
refresh schedule or freshness SLA has been promised by the user.

The user will provide inference access details and deployment/hardware choices
before development. Keep adapters/deployment configurable until then. PowerPoint
export is in scope; the [partner logo and template](../provided_material/README.md)
have now arrived and form the export baseline. Partner example needs/expected
entities and historical-case data remain absent from the supplied files.
