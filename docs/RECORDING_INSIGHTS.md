# Findings from the recorded discussions

**Reviewed: all four supplied transcripts, 18 October 2026.** These are
timestamped paraphrases, not audio-verified quotations. The [inventory](recordings/README.md)
defines T01–T04 and speaker caveats. Each entry separates what was said from
its product implication. Requirements from the written brief still apply.

## Business need and current practice

### E01 — Primary user and job

**Stakeholder:** [T01 00:00–02:14](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.56.37.mp4.txt);
[T02 04:35–05:23 and 14:05–14:13](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.04.mp4.txt).
The user is a business developer with law/economics rather than medical
expertise. They need scientific information to explain why a particular company
should establish or develop its activities in Bern. They cannot know every
discipline's search vocabulary.

**Implication:** design for a non-specialist doing company-specific research;
use clear explanations of the problem solved and why the capability matters.

### E02 — Incoming material is descriptive, not a standard question

**Stakeholder:** [T02 07:42–09:03 and 10:49–12:54](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.04.mp4.txt);
[T03 00:00–01:31](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.21.mp4.txt);
[T04 00:00–00:50](recordings/WhatsApp%20Audio%202026-10-18%20at%2011.04.13.mp4.txt).
Input can be an A4/one-page company summary: activities, founders/background,
employees, turnover, products, projects/services and goals. There is no standard
form or standard question; sometimes the description is only a medtech company
producing insulin pumps. Business plans are often generic and investor-facing.

**Implication:** short keywords and a public/synthetic plain-language description
are useful inputs. A required detailed technical questionnaire or document upload
would add assumptions. No authentic sample company document was supplied.

### E03 — Confidential business plans stay out of models

**Stakeholder:** [T02 14:13–15:05](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.04.mp4.txt);
[T03 00:55–01:31](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.21.mp4.txt).
The business model/plan can describe approximately five-year intentions and
investment plans. It is confidential and cannot be put into a model. The
business developer derives a few keywords for prompting. The hackathon uses
public resources.

**Implication:** document a human step for non-confidential query preparation.
Hosting locally does not itself override this stakeholder instruction. Private
document ingestion is outside the current prototype scope.

### E04 — Existing search and manual relevance review

**Stakeholder:** [T02 00:00–00:22 and 02:12–02:51](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.04.mp4.txt);
[T03 13:30–14:47](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.21.mp4.txt).
The business developer already searches with their own keywords and uses
Claude/OpenAI and self-configured agents. Some answers are relevant and some
are not; they expect to continue reviewing matches. They need time savings
and useful breadth, with enough precision to assess each item quickly.

**Implication:** compare against keyword/manual practice and show inspectable
matches. No baseline completion time or quantified savings was given.

### E05 — Lead origin, triage and company types

**Stakeholder:** [T02 06:21–07:38](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.04.mp4.txt);
[T03 07:48–09:23, 14:50–16:56 and 17:56–20:15](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.21.mp4.txt).
Switzerland Global Enterprise and agents abroad scout potential companies;
companies may also approach directly. Companies can come from anywhere and
include multinationals, family businesses and startups. Existing staff perform
due diligence and initial sector-fit triage. At this stage the company is an
existing contact, expects information and may choose which cantons to visit.

**Implication:** the current task starts after lead identification. Automated
scouting, company registration checks and cold outreach are not the core need.

### E06 — Business volume and concurrent cases

**Stakeholder:** [T03 07:27–07:47](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.21.mp4.txt).
Approximately **300 cases per year**, sometimes multiple in progress at once.

**Implication:** case separation could be useful later. This is not a query-count,
medical-only caseload, concurrency target or enterprise load benchmark.

## Scope and useful matches

### E07 — Bern geography and medical prototype focus

**Stakeholder:** [T01 01:05–02:14](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.56.37.mp4.txt);
[T02 09:22–10:47 and 16:34–16:46](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.04.mp4.txt);
[T03 01:32–02:24 and 03:33–03:59](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.21.mp4.txt).
The agency handles many sectors, but this prototype is **life sciences / medicine**
and **Canton of Bern**. Other regions' expertise does not solve this local need.
The stakeholder permits starting with one medical field, such as diabetes or
oncology, if needed to demonstrate a scalable approach.

**Implication:** medical subdomain selection remains a team decision. The written
brief's UniBE/ARTORG/Diabetes Center Berne coverage still applies.

### E08 — Vocabulary expansion and related concepts

**Stakeholder:** [T01 01:36–02:14](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.56.37.mp4.txt);
[T02 00:22–01:10 and 04:41–05:03](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.04.mp4.txt).
Someone saying diabetes may miss glucose monitoring, medtech devices,
biosensors, insulin/pumping and related research directions such as women and
diabetes. The stakeholder mentions semantics and ontology as ways to bridge
their words and site terminology.

**Implication:** semantic discovery is central. A specific ontology standard,
knowledge graph or vector database is not prescribed. Related topics are not
all synonyms and must not be treated as equivalent matches.

### E09 — People, units, research and practical capabilities

**Stakeholder:** [T02 01:13–02:11, 05:37–06:21, 07:20–07:38 and 12:49–13:34](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.04.mp4.txt);
[T03 12:43–13:30](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.21.mp4.txt).
Useful evidence includes experts/key opinion leaders, university divisions,
research breakthroughs or papers, development know-how, technologies, suppliers,
and possibly customers. Some companies prioritize R&D, others improvement of
an existing product through suppliers and university expertise.

**Implication:** person-only search is too narrow. Companies/suppliers are an
adjacent stakeholder interest; adding their sites must not substitute for the
three mandatory institutional sources. Do not assign “world-leading” status
without supporting evidence.

### E10 — Transferable technology and unexpected connections

**Stakeholder:** [T02 01:19–02:11 and 13:29–14:05](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.04.mp4.txt);
[T03 02:26–02:37](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.21.mp4.txt).
Examples include an existing drug-injection pump relevant to insulin delivery,
and lung organ-on-chip expertise potentially relevant to liver applications.
Useful ideas may concern a future R&D stage the company has not considered.

**Implication:** separate an evidenced capability from a **possible adjacent
application**. A similarity does not establish that a liver device exists or
that a technology is clinically suitable for a different use.

### E11 — Named examples are not a verified result dataset

**Stakeholder examples:** [T02 09:03–09:20 and 17:46–18:07](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.04.mp4.txt);
[T03 20:18–21:10](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.21.mp4.txt).
Ypsomed is mentioned as an insulin-pump company in the region. An EEG/epilepsy
no-match is explicitly hypothetical. Comments about Inselspital, local medtech
strength and industrial heritage describe the stakeholder's pitch context.

**Implication:** verify institutions, products, superlatives, geography and roles
against public pages before using them as application results or gold labels.
Do not label EEG/epilepsy a real absence of expertise in Bern.

## Output, review and downstream use

### E12 — Short plain-language descriptions plus sources

**Stakeholder:** [T02 05:08–05:23](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.04.mp4.txt);
[T03 14:07–14:47 and 24:08–24:39](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.21.mp4.txt).
A useful result is a few lines or a paragraph explaining what a unit/project
does and the problem it solves, followed by the source link. Bare links force
the reader to spend too much time; long technical reports are also unsuitable.

**Implication:** pair concise descriptions and match reasons with structured
fields and direct evidence. Do not replace the required fields with only prose.

### E13 — Company-facing teaser and decision

**Stakeholder:** [T03 02:38–03:32, 04:22–05:18 and 08:56–09:23](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.21.mp4.txt);
[T04 00:50–01:02](recordings/WhatsApp%20Audio%202026-10-18%20at%2011.04.13.mp4.txt).
The downstream output is a scientific-evidence-backed commercial teaser, often
a PDF of **five to ten pages maximum**; PowerPoint is also mentioned. One or two
interesting points should attract a busy CEO/C-level reader to visit Bern and
consider locating/expanding activities there.

**Implication:** export can support the workflow, but automated PDF generation is
not separately made mandatory in the written track brief. This teaser is distinct
from the hackathon technical report and pitch deck.

### E14 — Flexible selection rather than a fixed report formula

**Stakeholder:** [T02 12:49–13:24](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.04.mp4.txt);
[T03 12:25–14:47](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.21.mp4.txt).
There is no standard response-section allocation because company needs vary.
The user manually judges which items fit. They want condensed, precise and
understandable information rather than an exhaustive fifty-page output.

**Implication:** a structured result contract can coexist with flexible pitch
composition. A saved shortlist or keep/reject control is a proposal, not a
recorded requirement for a specific UI.

### E15 — Traceability and honest no-match behavior

**Stakeholder:** [T02 17:30–18:20](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.04.mp4.txt);
[T03 06:15–06:28, 09:43–09:55 and 16:56–17:54](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.21.mp4.txt).
The stakeholder accepts that nothing relevant may be found, says not to invent
competencies, and will not oversell. Others reinforce checking claims against
references. The written brief is stricter than conversational “mostly”:
**all** results, summaries and explanations must be traceable.

**Implication:** say that no reliable match was found **in the searched sources**;
limited collection cannot prove that Bern has no such expertise.

### E16 — Expert availability remains a human matter

**Stakeholder:** [T03 05:24–06:02 and 10:36–12:09](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.21.mp4.txt).
The agency arranges meetings after the pitch. A recognized expert may be busy
or unwilling to meet; staff make calls/send messages to discuss the opportunity.
The stakeholder says this availability issue need not be solved in the challenge.

**Implication:** discoverability does not establish collaboration readiness.
Do not promise meetings or automate outreach as part of this scope.

### E17 — Relationship maintenance is outside the challenge

**Stakeholder:** [T03 21:10–22:26](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.21.mp4.txt).
The agency maintains the ecosystem and relationships after company arrival,
but explicitly says this is not the aim of the challenge. The immediate goal
is information that prompts a C-level decision to visit and assess Bern.

**Implication:** avoid expanding the prototype into a CRM or network-management
system before the research-to-match flow works.

## Data access, implementation freedom and evaluation

### E18 — Sources are scattered websites, not a delivered database

**Stakeholder / technical discussion:** [T02 03:15–04:34](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.04.mp4.txt);
[T03 02:38–03:32 and 22:27–23:27](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.21.mp4.txt).
The supplied “dataset” is described as resources/URLs; no ready-to-use API,
prepared corpus or evaluation dataset is offered in the discussion. Access,
preprocessing and architecture are part of the technical challenge.

**Implication:** acquiring and validating the source inventory is a real first
step. “No API” describes what was provided, not proof no institution exposes
any public API anywhere.

### E19 — Prefetching and live tools are alternative suggestions

**Technical speaker suggestions:** [T02 03:15–04:34 and 09:59–10:16](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.04.mp4.txt);
[T03 22:39–23:27](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.21.mp4.txt).
Options discussed include collecting in advance and searching a database, or
giving a model tools to traverse resources. A maintained database has upkeep;
the solution should make future expansion feasible. The approach is left free.

**Implication:** do not record a mandatory live agent, graph, vector store,
fine-tune or pre-crawl architecture. Compare choices against traceability,
reproducibility and independent/offline deployment.

### E20 — Evaluation needs to be constructed

**Technical discussion:** [T02 03:57–04:34](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.04.mp4.txt);
[T03 23:27–23:49](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.21.mp4.txt).
No ready evaluation dataset is available. A synthetic example set or pilot
evaluation is suggested.

**Implication:** distinguish the written brief's numerical targets from the
missing labeled cases. Synthetic queries still require evidence-checked real
expected matches; a model's unsupported answer is not ground truth.

### E21 — Public and private usage would need different governance

**Technical suggestions:** [T02 15:05–15:27 and 18:49–19:21](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.04.mp4.txt).
Participants discuss internal/external users, masking and access protection if
private data were ever added, and suggest addressing this in the technical report.

**Implication:** future governance can be discussed as a limitation/extension.
It is not authorization to obtain confidential data or a requirement to build
authentication now. Public-source prototype users/access control remain open.

### E22 — Additional company sources are an extension

**Discussion:** [T02 08:24–09:20](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.04.mp4.txt);
[T03 22:27–24:39](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.21.mp4.txt).
Participants ask about scraping company information; the stakeholder values
companies/suppliers and insists that links alone are insufficient. No exact
additional domain list or concrete collection permissions are established.

**Implication:** keep expansion configurable and Bern-relevant. Confirm extra
source scope and rights when adding them; preserve mandatory institution coverage.

### E23 — Branding assets were offered but not delivered here

**Stakeholder:** [T03 06:29–07:26](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.57.21.mp4.txt);
[T04 01:04–01:13](recordings/WhatsApp%20Audio%202026-10-18%20at%2011.04.13.mp4.txt).
After clarifying a branding question, the stakeholder offers a PNG logo and
discusses email/Discord sharing. The follow-up mentions Discord or Notion but
does not clearly establish which materials would appear there.

**Later source update (N1, 18 October):** the user-supplied Notion page text
lists `powerpoint_template.pptx` and `Logo_SF_BE_EN.png`, explicitly for this
challenge only. See the [source snapshot](sources/NOTION_CHALLENGE_2026-10-18.md).
This establishes the asset names and page reference, but the files themselves
have not arrived or been inspected. Colors and export layout remain unverified;
do not infer permission to use client company assets or general reuse rights.

## General event remarks and transcript limitations

### E24 — Combining models was discussed in another track's Q&A

**General event remark:** [T01 07:58–08:19](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.56.37.mp4.txt).
In the archive challenge's OCR discussion, a speaker encourages useful Apertus
use and combining components, with open-weight models preferred where possible.

**Implication:** this is context about model combinations, not a requirement for
this track to use OCR, vision or auxiliary models. The navigator must still
use Apertus v1.5 and meet its own deployment constraints.

### E25 — Finals selection remark

**General event remark:** [T01 08:21–08:52](recordings/WhatsApp%20Audio%202026-10-18%20at%2010.56.37.mp4.txt).
The speaker describes two teams from each of three challenges reaching the
six-team finals, then three awards overall.

**Implication:** retain as a recorded event remark, subject to current organizer
instructions. It does not establish live pitch duration or scoring weights.

### E26 — Unclear wording and other-track content

**Transcript limitations:** T01 02:55–07:58 covers OpenParlData and archives;
T02 contains noise/ambiguous wording around 16:46–18:41; T03 includes terms such
as “encrypted” (01:32) and “organology” (01:32–02:24) without clear meaning.
T04 ends mid-sentence.

**Handling:** do not infer encryption requirements, a new medical subdomain,
permission to buy/paywall access, or facts from unfinished remarks. Preserve
the raw text and use only clearly supported interpretations. Other-track
datasets, handwriting/OCR tasks and parliamentary classifications are excluded.
