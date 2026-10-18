# Research & Expertise Navigator — supplied challenge brief

**Sources B1 and N1:** initial challenge text and the complete Notion page text
pasted by the user on 18 October 2026. N1 confirms the initial requirements and
adds the supporting filenames and challenge-only branding restriction; see the
[dated source snapshot](sources/NOTION_CHALLENGE_2026-10-18.md). This is a
structured capture, not independent live-page verification. Workshop
clarifications are separate in
[RECORDING_INSIGHTS.md](RECORDING_INSIGHTS.md).

**Partner:** Bern Economic Development Agency.

**Domain:** Research & Innovation.

**Guide:** [Bern Economic Development Agency challenge](https://hackapertus.notion.site/bern-economic-development-agency).

## 1. Context, problem and objective

Finding expertise often requires knowing where to search before knowing what to
search for. Research information is scattered across faculty websites, institute
pages, research groups, centres, researcher profiles and project descriptions.
The searcher's language can differ substantially from scientific terminology:
“glucose sensors” may be described as continuous glucose monitoring, biosensing,
metabolic monitoring, wearable sensing or CGM.

Institutions produce valuable information about people, expertise, research
activities, technologies, infrastructure and services, distributed across
heterogeneous public websites and platforms.

**Objective:** create an AI-powered navigator that aggregates these public
sources into a unified, semantically searchable knowledge resource, accessible
through one natural-language and keyword-based search interface.

## 2. Datasets and supporting material

Treat these as **one distributed information ecosystem**:

1. **University of Bern web ecosystem:** public `unibe.ch` subdomains covering
   faculties, institutes, departments, research centres, laboratories, services
   and platforms. The supplied inventory is intended as the initial discovery map.
2. **ARTORG Center for Biomedical Engineering Research:** website and associated
   research, team and project pages.
3. **Diabetes Center Berne:** website and associated research, expertise, team,
   project and service pages.

Design for easy addition of institutional websites and data sources later.
The Notion page names these supporting materials [N1]:

| Listed file | Purpose | Local status |
| --- | --- | --- |
| `unibe_sous_domaines_publics_etendus.xlsx` | Initial public UniBE subdomain discovery map | Filename supplied; workbook contents/download URL not supplied or inspected |
| `powerpoint_template.pptx` | Challenge presentation template | Filename supplied; file not available locally or inspected |
| `Logo_SF_BE_EN.png` | Challenge logo | Filename supplied; file not available locally or inspected |

**Use the PowerPoint template and logo only for this challenge.** This explicit
restriction is not a general reuse/license grant. The presentation template is
separate from the required repository/technical-report template and does not
establish a mandatory automatic teaser-export feature. Obtain the actual
workbook before claiming a configured or validated UniBE discovery map.

## 3. Technology and infrastructure

- No specified programming-language or framework restrictions.
- **Apertus 8B or 70B, v1.5**:
  [8B model](https://huggingface.co/swiss-ai/Apertus-v1.5-8B),
  [70B model](https://huggingface.co/swiss-ai/Apertus-v1.5-70B).
- Development and deployment must happen entirely **outside the Canton of
  Bern's ICT infrastructure**. Local setups such as Docker, independent
  infrastructure and Swiss cloud are examples.
- Solutions must be self-contained and run fully air-gapped **or** on independent
  cloud instances, with no connection to internal cantonal networks.

These are deployability constraints; the brief does not mandate Docker or a
particular retrieval, database, ontology, agent or frontend implementation.

## 4. Expected outputs and success criteria

Deliver an **end-to-end prototype**:

Public web sources → content extraction → semantic enrichment → structured
knowledge → natural-language search → source-backed results.

Each query should return **structured, traceable results**, including, where
the source provides the information:

- relevant people and contact persons;
- their functions and affiliations;
- departments, institutes and research groups;
- fields of expertise;
- related projects or activities;
- relevant infrastructure or services;
- a short explanation of why each result matches;
- direct links to the original source pages.

Every result must remain connected to its source and verifiable.

| Success criterion | Supplied target |
| --- | --- |
| Finds the right people | At least 80% of expected experts/units appear in the top 10 results |
| Handles different wording | Synonym and lay-term queries find the same experts as the site's terminology |
| Every result is traceable | 100% link to a public page supporting the claim; no invented people, roles or projects |
| Structured results | Required fields are filled where source information exists |
| Covers all three sources | UniBE, ARTORG and Diabetes Center Berne |
| Easy to extend | Add an institutional website by configuration or a short documented step, without rewriting the pipeline |

Challenge evaluation dimensions: **purposeful use of AI; technical rigour;
value, cost and scalability; sovereign deployability; implementation feasibility**.
The local submission template additionally lists **pitch and presentation** for
the main jury; see [EVENT_AND_SUBMISSION.md](EVENT_AND_SUBMISSION.md).

## 5. Ethics, legal and publication requirements

- **Transparency and traceability:** avoid unverified or hallucinated output.
  Results, summaries and explanations must be traceable to verifiable public
  source URLs.
- **Fair and unbiased representation:** objective discoverability across
  research groups, institutes and researchers regardless of size or prominence.
- **Accuracy and reliability:** clearly state when reliable, verifiable or
  sufficient information is unavailable.
- Comply with the **Swiss Federal Act on Data Protection (nDSG)** and **GDPR where
  applicable**. This records the brief's requirements; it is not a legal analysis.
- Use **public web content only**. Source-page copyright remains with the
  originating institutions.
- Outputs are published as **Open Commons**, referring to Terms & Conditions §6.
  Keep this wording distinct from the template's Apache-2.0 code license and
  CC-BY-4.0 report label; see the source and rights questions in
  [DATA_AND_PROVENANCE.md](DATA_AND_PROVENANCE.md).
