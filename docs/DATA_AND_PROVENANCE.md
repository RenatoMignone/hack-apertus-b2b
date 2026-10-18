# Data sources, evidence and collection boundaries

**Status:** contract proposal derived from B1 and recording evidence E03,
E07–E11, E15, E18–E22. No source collection, entity extraction or rights clearance
has been performed. See [SOURCES.md](SOURCES.md) for context-source provenance.

## Source inventory

| Source family required by B1 | Discovery input | Current status |
| --- | --- | --- |
| University of Bern | Supplied public `unibe.ch` subdomain inventory; faculties, institutes, centres, groups, laboratories, services/platforms | Inventory missing from the supplied repository/context; `unibe.ch` is a scope hint, not a complete crawl configuration |
| ARTORG Center for Biomedical Engineering Research | Official website and associated research, team and project pages | Exact seed URLs, domain/path boundaries and language variants not supplied/verified |
| Diabetes Center Berne | Official website and research, expertise, team, project and service pages | Exact seed URLs, domain/path boundaries and language variants not supplied/verified |
| Additional Bern institutions/companies | Configurable future source entries | Stakeholder interest; no additional mandatory domain list or verified seeds |

Resolve redirects and actual institutional site ownership before configuring
collection. ARTORG may overlap the UniBE web ecosystem: source families describe
institutional coverage, not necessarily disjoint hosts or datasets. Deduplicate
physical pages without losing institutional attribution. Do not count duplicate
copies as extra experts or fabricate three separate databases.

## Proposed source configuration and collection record

A new source should need a small configuration entry and, only where necessary,
a documented site-specific extractor. Suggested fields:

- stable source ID, institution label and source-family membership;
- verified seed URLs, allowed hosts/path prefixes, inclusion/exclusion patterns;
- language discovery/handling, supported page/file types, URL normalization;
- bounded depth/page count, per-host request rate, timeout and retry limits;
- extractor choice and any site-specific handling;
- collection date, rights/usage notes and known access limitations.

These are design suggestions, not existing configuration keys. Verify public
access, relevant site conditions and crawl guidance; use bounded, polite access.
Do not cross login walls, obtain internal network access or treat a public URL
as a blanket redistribution license. No collection permission is established
merely by a workshop participant suggesting scraping.

Keep a collection manifest: attempted URL, canonical/final URL, source family,
fetch timestamp/status, content hash, title, language, extractor version and
inclusion/exclusion reason. Distinguish fetched pages from successfully extracted,
indexed and rejected pages. Keep failures visible in coverage reporting.

## Proposed knowledge and evidence contract

The required result fields are in [PRODUCT_REQUIREMENTS.md](PRODUCT_REQUIREMENTS.md).
The internal representation should support these additional provenance concepts:

| Record | Suggested contents and rules |
| --- | --- |
| Source page | Stable ID, original/canonical URL, title, institution/source family, fetched time, visible publication/update date if present, content hash and extraction status |
| Evidence passage | Page ID, exact excerpt or reproducible text offsets/section locator, extraction version; retain only as rights/storage policy allows |
| Entity | Stable ID, entity type (person, unit, project, infrastructure, service; company if scope extended), supported labels/aliases, links to evidence |
| Claim/relationship | Subject, predicate, object/value, evidence passage IDs, source dates, verification/conflict status; e.g. person → affiliation → unit only when supported |
| Search match | Query/run ID, entity/result ID, supported required fields, matched concepts, short description, explanation and evidence references |
| Coverage/run metadata | Corpus snapshot, participating source families, missing/failed sources, model/configuration identifiers and retrieval/evaluation version |

This is a conceptual contract; it does not select a graph database, JSON schema
or storage technology. A small implementation can satisfy it with simpler records.

### Evidence rules

1. **Every factual result claim needs support.** A source URL must support the
   claim, not merely belong to the right institution. Multiple fields may need
   multiple pages. Proposed passage-level references make review reproducible.
2. **Separate observations from interpretations.** Source says “lung model” is
   an observed capability; “possibly relevant to liver R&D” is a labeled match
   hypothesis. Never extract the hypothesis as a completed liver project.
3. **Missing fields remain missing.** Use an empty list or null with a reason
   such as “not stated in retrieved sources,” adapted to the eventual format.
   Do not derive email addresses from name patterns or invent named contacts.
4. **Merge identities cautiously.** Similar names and topical overlap are not
   enough. Prefer explicit profile IDs/links and compatible affiliations; keep
   ambiguous candidates separate and retain evidence for aliases.
5. **Roles can change.** Preserve source/fetch dates, avoid silently resolving
   contradictions by model guesswork, and disclose staleness or disagreement.
6. **Enrichment does not become source truth.** Synonyms, model-generated tags
   and suggested relations need origin labels. Never use generated summaries
   as sole evidence for a person, project or service.
7. **Untrusted page content stays data.** Proposed implementation guardrail:
   extracted pages must not override agent instructions or trigger arbitrary
   tools. A citation-quality check must be separate from trusting page text.

## Privacy, rights and publication

**Recorded boundary:** business plans stay outside models; the human prepares
non-confidential keywords. Public researcher/contact pages can still contain
personal information. Limit collection to relevant professional facts and do
not infer sensitive attributes. [B1 §5; E03]

**Template requirement:** describe data origin/license and flag personal or
non-redistributable material in the technical report; keep that material out of
the repository. Public access does not imply blanket consent or ownership.
Record the actual basis and restrictions; do not invent consent. [M2 §4]

Apache-2.0 in the root applies to the code artifact; M2 labels the report CC-BY-4.0;
B1 refers to Open Commons/T&C §6 while retaining institutional source copyrights.
Do not relicense crawled pages, photos, PDFs, logos or transcripts under the code
license. Redistribution permissions and the current T&C wording remain unresolved.

The supplied transcripts are working context, not source facts for expertise
results. Publication/redistribution consent is unknown. Keep credentials, company
plans and unapproved personal/non-redistributable content out of public artifacts.
No `.gitignore` change has been made in this documentation-only pass; choose
appropriate local-only data paths before future collection and remember that
ignore patterns do not remove already tracked files.

## Fresh collection versus disconnected operation

Public-web collection requires a connected environment. For an air-gapped search
runtime, prepackage the permitted corpus/index, model weights, dependencies and
assets; run with local inference and no remote services. A source link can remain
attached for later verification even when offline, but the interface must not
claim it just checked that page live. Document snapshot age and a separate
connected refresh process. This is a proposed deployment pattern, not a tested
capability. Independent connected cloud operation is another allowed target.
