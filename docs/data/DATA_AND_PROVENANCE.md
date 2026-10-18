# Data, evidence and provenance

**18 October 2026 · Evidence/rights policy; collection adapters implemented, published pilot corpus unverified.**
Start with the [visual pipeline](../architecture.html). The
[Phase 1 shared contract](../plans/INGESTION_PLAN.md#7-shared-contract-v1--owned-here-consumed-by-phase-2)
owns schemas/interfaces; this file owns evidence and rights rules.
[Three-page collection observations](../team/backbone/RESULTS.md) are a limited
source slice, not a published knowledge corpus or exhaustive coverage.
Physical storage/search/case/tracing contracts are routed through
[DATA_LAYER.md](DATA_LAYER.md): PostgreSQL + pgvector, artifact storage,
LangGraph PostgreSQL checkpoints and self-hosted Langfuse.

## Source inventory

| Family | Discovery input | Current evidence / limitation |
| --- | --- | --- |
| UniBE | Partner workbook, public links/sitemaps and medical/DBMR seeds | Workbook has 42 actual rows including DCB, despite Notes count of 71; not exhaustive DNS coverage |
| ARTORG | Research directory and associated team/project pages | Dated public-page observations in pilot scope; not a completed crawl |
| DCB | `https://www.dcberne.com/en/projects/` and associated public pages | Dated discovery observation; do not substitute a guessed research URL |
| Additional organizations | Partner references, then eligible public sources | Current pilot requires healthcare relevance and evidenced Canton of Bern activity; network membership alone is insufficient |
| Case company | Permitted typed clues plus attributable public pages or packaged evidence | Company identity must be resolved; user statements remain attributed until independently supported |
| Historical cases | Approved public/non-confidential records only | No dataset supplied; distinguish unavailable data from no similar case |

Use the [pilot scope](../challenge/PILOT_SCOPE.md) for exact dated seeds and the
[provided-material inventory](../provided_material/README.md) for original hashes,
workbook row details and template/logo handling. The workbook is a discovery map,
not a verified expertise or gold-label dataset. Branding and workshop transcripts
stay outside the research index.

One page can belong to multiple source families. Deduplicate physical pages
without losing institutional attribution or treating copies as corroboration.
English output is baseline; preserve DE/FR/IT source text where actually collected.
Translations are labeled derivations linked to original passages.

## Collection and lineage

The [collection specification](ingestion/INGESTION_SPEC.md) defines config-driven
hosts/paths, robots/access checks, safe requests, extraction and quality reporting.
The user authorizes relevant public robots-allowed collection without a blanket
manual-per-origin gate. Record actual restrictions/ambiguities; collection access
and redistribution rights are different questions.

Keep requested/final URLs, discovery provenance, fetch/source dates separately,
raw/body hashes, parser/configuration versions, language, title and status.
Distinguish attempted, fetched, extracted, enriched, indexed and rejected pages.
Evidence preserves literal text, version and section/page/Unicode offsets.
Claims, taxonomy mappings, translations and summaries have separate derivations.
Every case pins profile/taxonomy/snapshot/index versions and its case evidence
manifest. Indexes are rebuildable; source truth is not just a vector store.

## Evidence rules

1. **Support every factual claim.** A real URL is insufficient unless its
   passages support the specific role, capability or relationship. Facts may
   require multiple sources; exact quotes still require semantic review.
2. **Separate evidence and inference.** An evidenced lung model does not become
   an existing liver project. Suggested transfer and potential benefits remain
   labeled arguments with premises and prerequisites.
3. **Keep unknowns.** Missing roles, contacts, dates or outcomes stay null with
   reasons. Never derive email addresses or expert willingness from patterns.
4. **Resolve identity cautiously.** Prefer explicit links/IDs and compatible
   affiliations; similar names or topical overlap do not establish identity.
5. **Preserve dates/conflicts.** Do not resolve contradictory roles or stale
   source information by guessing. Retrieval failure is distinct from no-match.
6. **Generated text is not its own factual source.** Keep raw passages behind
   summaries; operator suggestions are research leads; reviewed selection does
   not bypass support checks or automatically update shared memory.
7. **Treat source content as untrusted data.** It cannot override application
   instructions, execute tools or change source/access policies.

## Intake, rights and publication

Current intake is manually typed permitted keywords/context after the human reads
confidential plans and one-pagers outside the application. Those PDFs cannot be
uploaded now, including to a local model. Future attachment support is disabled
pending explicit permission and revised handling/access/retention/deployment
requirements. A model cannot redact the forbidden document before receiving it.
Public linked research PDFs use a separate eligible collection path. [T05
00:48–01:22](../recordings/bern-navigator-followup-2026-10-18.txt).

Retain only relevant public professional information and record restrictions.
Do not infer sensitive attributes. The root code's Apache-2.0, report's CC-BY-4.0
and challenge's Open Commons wording do not relicense source pages, contacts,
photos, PDFs, branding or transcripts. Actual reuse/redistribution rights and
current event terms remain unresolved where not supplied.

The template/logo are **challenge-only**. Preserve originals; do not infer rights
to client-company assets. Transcripts are working context with unknown publication
consent. Keep secrets, confidential plans and unapproved personal/non-redistributable
material out of public artifacts; `.gitignore` does not remove tracked files.

## Disconnected runtime

Connected build/collection produces a permitted dated snapshot. The proposed
air-gapped runtime packages evidence/indexes, models, profile/taxonomy and all
assets locally. Do not claim live verification when offline; source URLs are
references for later checking. Dependency inventory and proof requirements live
in [ARCHITECTURE.md](../plans/ARCHITECTURE.md#target-architecture-mandatory).
