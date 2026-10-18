# Notion challenge text — supplied snapshot

**Source ID:** N1. **Captured:** 18 October 2026.
**Page:** <https://hackapertus.notion.site/bern-economic-development-agency>.
**Method:** complete page text pasted by the user after direct retrieval was
blocked. The text below preserves that supplied content; attachment names are
not attachment downloads. No workbook, presentation or logo bytes were supplied
or inspected. This is a dated capture, not a live-page verification.

## Changes to the existing context

The product, model, infrastructure, deliverable, success and ethics requirements
agree with the initial brief B1. New explicit details are the **Research &
Innovation** domain, three supporting filenames, and the instruction to use the
PowerPoint template and logo **only for this challenge**. The asset contents,
download URLs and any broader redistribution permissions remain unverified.
This presentation template supplements the repository template; it does not
replace the root technical report or change its page limit. Its listing does
not make automatic company-teaser export a mandatory prototype feature.

## Supplied page content

# Bern Economic Development Agency

# Research & Expertise Navigator

## 🎯 Challenge Overview

**Domain:** Research & Innovation

### → Context & Background

Today, finding expertise often requires knowing where to search before knowing what to search for. Information may be located on a faculty website, an institute page, a research group profile, a centre's website, an individual researcher page or a project description. On top of that, the terminology used by the person searching may differ significantly from the terminology used on the source website. Someone looking for expertise in "glucose sensors", for example, may miss relevant information described as continuous glucose monitoring, biosensing, metabolic monitoring, wearable sensing or CGM. The challenge is therefore to transform this fragmented web landscape into a unified and semantically searchable knowledge resource.

### → Problem Description

Research institutions generate a considerable amount of valuable information about their people, expertise, research activities, technologies, infrastructures and services. However, this information is distributed across a large and heterogeneous landscape of institutional websites and platforms.

### → Primary Objective

Create an AI-powered **Research & Expertise Navigator** that aggregates these distributed public sources and makes their content accessible through a single natural-language and keyword-based search interface.

---

## 🔧 Resources, Tools & Support

### → Datasets

For the prototype, the system would use three complementary sets of public data sources, treated as **one distributed information ecosystem** rather than separate databases:

1. **University of Bern web ecosystem** — based on the provided inventory of public unibe.ch subdomains (faculties, institutes, departments, research centres, laboratories, services and platforms).
2. **ARTORG Center for Biomedical Engineering Research** — website and its associated research, team and project pages.
3. **Diabetes Center Berne** — website and its associated research, expertise, team, project and service pages.

The architecture should also be designed so that additional institutional websites and data sources can be added easily later.

### → Supporting Materials

A supplied inventory of public University of Bern (unibe.ch) subdomains, serving as the initial discovery map for the UniBE ecosystem.

unibe_sous_domaines_publics_etendus.xlsx

The powerpoint template and logo (**please use them ONLY for the need of this challenge**):

powerpoint_template.pptx

Logo_SF_BE_EN.png

---

## 💻 Technical Preferences

|  |  |
| --- | --- |
| **Preferred languages / frameworks** | Not specified — no restriction implied |
| **Recommended platforms** | **External environments only** — development and deployment must happen entirely outside the Canton of Bern's ICT infrastructure. Use local setups (e.g. Docker) or independent / Swiss Cloud infrastructure. Solutions must be self-contained and run **fully air-gapped** or on independent cloud instances, with no connection to internal cantonal networks. |
| **Specific AI models** | Apertus 8B or 70B (v1.5) |
| **Model sources** | huggingface.co/swiss-ai/Apertus-v1.5-8B<br>huggingface.co/swiss-ai/Apertus-v1.5-70B |

---

## 📦 Deliverables & Judging

### → Expected outputs

An **end-to-end prototype**: public web sources → content extraction → semantic enrichment → structured knowledge → natural-language search → source-backed results.

Rather than only a textual answer, each query should return **structured, traceable results**:

- relevant people and contact persons;
- their functions and affiliations;
- departments / institutes / research groups;
- fields of expertise;
- related projects or activities;
- relevant infrastructure or services;
- a short explanation of why each result matches;
- direct links to the original source pages.

Every result stays connected to its source and can be verified.

### → Success criteria

1. **Finds the right people:** at least 80% of expected experts/units appear in the top 10 results.
2. **Handles different wording:** synonym and lay-term queries (e.g. "glucose sensors" vs. "CGM", "biosensing") find the same experts as the site's own terminology.
3. **Every result is traceable:** 100% of results link to a public source page that supports the claim; no invented people, roles or projects.
4. **Structured results:** each result fills the required fields (person, role/affiliation, unit, expertise, projects, infrastructure/services, reason for match, source link) where the source provides them.
5. **Covers all three sources:** UniBE, ARTORG and Diabetes Center Berne.
6. **Easy to extend:** a new institutional website can be added via configuration or a short documented step, without rewriting the pipeline.

### → Evaluation criteria

- Purposeful use of AI
- Technical rigour
- Value, cost & scalability
- Sovereign deployability
- Implementation feasibility

---

## ⚖️ Ethics & Compliance

### → Ethical guidelines

- **Transparency & traceability:** AI outputs must avoid unverified or hallucinated information. Every result, summary and explanation must be fully traceable and back-linked to the verifiable public source URL (e.g. UniBE, ARTORG).
- **Fair & unbiased representation:** the search must ensure fair, objective discoverability across all research groups, institutes and individual researchers, regardless of institutional size or prominence.
- **Accuracy & reliability:** the system must clearly say when no reliable, verifiable or sufficient source information is available to answer a query.

### → Legal & compliance

Comply with the **Swiss Federal Act on Data Protection (nDSG)** and **GDPR** where applicable. Only public web content is used; the copyright of source pages stays with the original institutions. Outputs are published as **Open Commons** *(see Terms & Conditions, §6)*.
