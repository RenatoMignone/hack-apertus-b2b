# Product requirements and scope

**Status:** requirements extracted; no product has been implemented. B1 refers
to the [supplied challenge brief](CHALLENGE_BRIEF.md), confirmed by the complete
[Notion text N1](../sources/NOTION_CHALLENGE_2026-10-18.md). E01–E30 refer to
[recording evidence](../recordings/RECORDING_INSIGHTS.md). Proposed checks below are internal
acceptance guidance, not additional organizer rules.

## Users, needs and desired outcome

The primary operator is a **Bern economic-development business developer** who
does not have specialist medical knowledge. They need to identify credible,
company-relevant expertise quickly and understand what each match contributes.
The downstream audience is a company CEO/C-level decision-maker considering
a visit and business activities in Bern. Experts and institutional units are
potential matches, not assumed application operators. [E01–E05, E13, E16]

The useful outcome is a reviewed set of factual, readable reasons why Bern's
research ecosystem could help this company. Search supports that judgment;
staff remain responsible for relevance selection and external communications.

| Need | Evidence | Product consequence |
| --- | --- | --- |
| Search without knowing scientific vocabulary | E01, E08 | Accept ordinary language and keywords; bridge site terminology |
| Spend less time scanning fragmented pages | E04, E12, E18 | Consolidate concise matches with inspectable evidence |
| Find relevant capabilities beyond a person directory | E09–E10 | Include units, projects, infrastructure and services |
| Judge whether an item actually fits a company's goals | E04, E14 | Explain relevance in plain language and show uncertainty |
| Prepare a scientifically credible teaser | E12–E15 | Make selected evidence reusable with its sources attached |
| Avoid overselling or exposing confidential plans | E03, E15 | Public evidence, non-confidential query inputs and abstention |

## Required baseline

| ID | Requirement and origin | Proposed observable acceptance condition |
| --- | --- | --- |
| R01 | One natural-language and keyword search interface (B1 §1) | A short keyword query and a plain-language request can retrieve structured matches through the same interface |
| R02 | End-to-end public-source processing, extraction, enrichment and structured knowledge (B1 §4) | A demonstrated result can be traced through collection/extraction to the indexed evidence used to retrieve it |
| R03 | UniBE, ARTORG and Diabetes Center Berne as one ecosystem (B1 §2/§4) | A source-coverage manifest and evidence-backed examples cover all three; a query can combine relevant matches across them |
| R04 | At least 80% of expected experts/units in top 10 (B1 §4) | Evaluate against independently checked expected sets; report per-query and aggregate recall with the protocol in EVALUATION.md |
| R05 | Synonym and lay-term resilience (B1 §1/§4, E08) | Equivalent-intent terminology variants retrieve the expected experts, with related-but-different concepts assessed separately |
| R06 | Source-supported results and explanations; no invented people/roles/projects (B1 §4/§5, E15) | Every displayed factual claim has supporting public evidence; a URL that does not support the claim fails the check |
| R07 | Complete structured result fields where provided by sources (B1 §4) | Expose the fields listed below; missing source information stays explicitly unavailable rather than guessed |
| R08 | Reliable no-match/insufficient-evidence response (B1 §5, E15) | Unsupported and out-of-scope requests return a limitation tied to searched coverage; never a fabricated match |
| R09 | Easy addition of institutional sites (B1 §2/§4) | Demonstrate a new configured site or short documented addition without rewriting the pipeline |
| R10 | Purposeful Apertus v1.5 8B/70B use (B1 §3, M1) | Document actual model/version, role, prompts, serving setup and a meaningful observed contribution |
| R11 | Outside cantonal ICT; self-contained air-gapped or independent cloud operation (B1 §3, M2) | Document selected target and dependencies; verify whichever deployment capability is claimed |
| R12 | Public data, privacy and source copyright boundaries (B1 §5, E03) | No confidential company-plan ingestion; source rights and any personal/non-redistributable content recorded separately from code licensing |
| R13 | Fair discoverability (B1 §5) | Audit source/group coverage and prominence effects; document omissions and retrieval bias rather than assuming a fair ranking |
| R14 | Preserve organizer layout and model environment names (M1/M2) | Required root files and `src/` remain in place; future run instructions use the template interface |
| R15 | Use the supplied PowerPoint template and logo only for this challenge (N1, Supporting Materials) | If acquired/used, `powerpoint_template.pptx` and `Logo_SF_BE_EN.png` remain within that purpose; broader reuse is not assumed |

## Required result information

Every result should expose these fields **where the source provides them**:

| Field | Interpretation |
| --- | --- |
| Person/contact | Relevant named researcher or contact; a unit-only result may have no named contact |
| Function and affiliation | Supported role(s) and institution(s); do not assume professor/PI status |
| Unit | Department, institute, centre or research group, retaining the relevant hierarchy |
| Expertise | Supported fields/capabilities, with understandable wording |
| Projects/activities | Related work actually evidenced on the source pages |
| Infrastructure/services | Relevant facilities or offered services if documented |
| Reason for match | A short explanation tied to the user's intent and evidence |
| Source links | Direct public pages supporting the presented claims |

The brief does not require every result to be a person or every source to
contain every field. Suggested missing-value behavior and claim-level evidence
are described in [DATA_AND_PROVENANCE.md](../data/DATA_AND_PROVENANCE.md).

## Stakeholder expectations beyond the formal baseline

| ID | Expectation | Priority interpretation |
| --- | --- | --- |
| S01 | Condensed, jargon-light descriptions, more than bare links (E12, E14) | Important usability condition for the core search results |
| S02 | Human assessment of relevance remains part of work (E04, E14) | Support inspection and selection; no specific keep/reject UI was mandated |
| S03 | Discover useful adjacent capabilities and future R&D directions (E10) | Valuable when labeled as a possible connection and grounded in actual capabilities |
| S04 | Company-facing PDF/PowerPoint teaser, often 5–10 pages maximum (E13) | User selected automatic PowerPoint export; partner template and English logo now supplied in provided_material/ |
| S05 | Suppliers/companies can strengthen the case (E09, E22) | Extension after core institutional source coverage; exact sites are unconfirmed |
| S06 | Multiple cases sometimes run concurrently, about 300/year overall (E06) | Context for future workflow; no required case-management feature or load target |

## Scope boundaries

**Current user architecture/input requirements, 18 October:** manual text intake
(keywords, context, public company facts and operator leads), domain-independent
core with configurable/rebuildable RAG, and a grounded main
[visual architecture reference](../architecture.html). Future confidential PDF
intake remains disabled pending explicit permission and revised handling rules.
The [architecture contract](../plans/ARCHITECTURE.md) owns components, deployment
targets and lifecycle dependencies. These extend the product design, not the
organizer's official criteria.

**Additional user requirements, 18 October:** the operator can issue natural-
language instructions to modify/refocus existing results/reports, and the agent
can ask follow-up questions. Preserve revision history, answered context,
supporting evidence and export consistency. Implement these through the dialogue
and memory handoffs in the paired plans; the supplied T05 transcript reinforces
the terminology bridge and public-only input boundary.

**Confirmed focus:** medical/life-science expertise in Bern and all three
institutional source families. Under user-delegated selection, the pilot is
**diabetes technology**, especially glucose monitoring, automated insulin delivery
and supporting digital tools. Evidence and boundaries are in
[PILOT_SCOPE.md](PILOT_SCOPE.md). English UI/results/slides are the baseline;
German/French/Italian source/query support is desirable. Additional ecosystem
organizations must be healthcare-related with evidenced Canton of Bern activity.

**Outside current scope:** confidential document uploads, lead scouting and due
diligence, automatic outreach or meeting scheduling, CRM/relationship maintenance,
promises that experts are available, and generic medical advice. The first five
boundaries follow E03/E05/E16/E17; keeping generic medical advice outside scope is
a product interpretation of the regional expertise-search objective.

**Not prescribed:** programming language, frontend, database, ontology technology,
knowledge graph, embedding model, live browsing, fine-tuning, Docker, authentication,
or a fixed teaser template. English-first response language is now selected.
Decide remaining technologies based on evidence and the
team's remaining time; record choices in
[DECISIONS_AND_OPEN_QUESTIONS.md](../project/DECISIONS_AND_OPEN_QUESTIONS.md).
