# Demo script: one case, every feature

**Status:** proposal, 18–19 October 2026. Clicked through in mock mode on
`ui-polish`, then again after merging into `main`: steps 1–9, keep, and the
export dialog with its review gate. The PDF/PPTX files themselves were not opened.
The live backend is not used here (see "What runs where").

Use this for the live pitch and for the ≤ 2-minute video. For how the video and
the clickable HTML walkthrough are built, see the
[walkthrough playbook](DEMO_WALKTHROUGH_PLAYBOOK.md).

## The story in one sentence

A business developer with no medical background types what a company does, in
everyday words, and within seconds gets a short list of source-backed reasons
why Bern fits: people, groups, projects and services from **UniBE, ARTORG and DCB**.
They refine it in plain language, keep what is relevant and export a company-facing
brief. Nothing is invented: missing information is shown as missing.

**Hero company:** GlucoWave (synthetic), maker of a needle-free "blood-sugar
patch". Every Bern entity shown comes from a public page captured on 18 Oct 2026
([evidence.ts](../../src/frontend/src/mocks/evidence.ts)).

## What runs where (say it honestly)

| Part | Shown in the demo | Truthful claim |
| --- | --- | --- |
| UI, workflow, export | Frontend in **mock mode** (`VITE_API_MODE=mock`), served locally, no network calls | "This is the real interface, on recorded results from real public pages." |
| Search, Apertus, PostgreSQL | Not live in this demo | On `main`: FastAPI + LangGraph worker + PostgreSQL/pgvector, Apertus v1.5 70B via the Keera endpoint; backend test suite passing on **synthetic** data (count and date in [STATUS.md](STATUS.md)). No published corpus yet, so no measured recall. |
| Air-gapped deployment | Architecture slide only | Designed and partly checked; a full network-disabled run has **not** been done. |

The Demo badge in the top bar already says "Synthetic companies, real public
sources. Not connected to the live agent yet."

## Pre-flight (5 minutes before)

1. Start the frontend in **mock mode** (HTTP is the default on `main`):
   PowerShell `$env:VITE_API_MODE='mock'; npm --prefix src/frontend run dev`.
   Open the printed localhost URL in Chrome. The top bar must show the **Demo**
   badge, not *Connected*. Use the full window, zoom 100 %.
2. **Demo → Reset demo data.** The board (**My cases**, `/cases`) must show *In review: 0 / No cases*.
3. Close other tabs and notifications. Keep the chat panel open.
4. Do a dry run of steps 1–7 once, then reset again.
5. Optional: a recorded walkthrough as a backup, in case the laptop or projector fails.

### Rules that keep it reliable

The mock agent recognises fixed patterns, not free language. On stage:

- Start the hero with the **Glucose sensor** example button. Do not retype it.
- In chat, type exactly the scripted lines below. Other phrases may get
  "Brief unchanged".
- Do not let judges type freely in the mock. A plain "diabetes" query, or an
  unfamiliar topic, returns *No reliable match*. If someone asks, show the
  contrast cases instead and explain that live search runs on the backend.
- Do not click *Make it shorter* during the main run: it also drops the Ideas section.

## Run sheet

| # | Do | Say (short) | What it proves |
| --- | --- | --- | --- |
| 0 | **My desk** (`/`): point at *Next steps* (Pumpline's open question, outcomes to record). Click **My cases**: the board, In review empty | "Our user is a business developer. About 300 company cases a year. Her desk shows what's waiting on her; this is her board." | Case workflow fits their process (E06) |
| 1 | **New case** → **Glucose sensor** example. Point at the lock note. → **Ctrl+Enter** | "She types what she knows, in everyday words: a blood-sugar patch. Public information only; confidential business plans never go in." | One natural-language input (R01); confidentiality boundary (R12, E03, E28) |
| 2 | Run stages play (interpreting → searching → validating → drafting) | "It interprets, searches the three institutions, checks every claim against its source, then drafts." | Pipeline steps; validation before output (R06) |
| 3 | Results appear. Point at the company card, then *Why Bern* with the three institution dots | "Four people and eight groups, projects and services, across UniBE, ARTORG and DCB." | All three sources as one ecosystem (R03) |
| 4 | **People:** Lilian Witthauer card. Point at the role, the unit breadcrumb, *Not stated in sources: Contact details* and *Source page* | "Roles exactly as the page states them. What the page does not say, we say is missing; we don't guess." | Structured fields where sources give them; no invention (R06, R07) |
| 5 | Scroll to **Projects:** *Research on diabetes in women*, **Your lead ✓**. Click citation chip `[10]` → evidence drawer with the highlighted quote → **Esc** | "Her hunch about DCB was right, and here is the exact sentence on DCB's page that proves it." | Traceable claim to a public URL (R06, E12, E15) |
| 6 | **Ideas to explore:** *Idea · to validate* card | "Ideas are labelled as ideas: an adjacent possibility, not a claim that it fits." | Evidence vs adjacent application (E10) |
| 7 | **How I searched** (expand). Hover *blood-sugar patch* | "She said blood-sugar patch. It searched continuous glucose monitoring and non-invasive monitoring: the vocabulary she doesn't have." | Lay-term → scientific bridge (R05, E08, E27) |
| 8 | Chat: the agent asked *Study partner, R&D site, or both?* → click **Both** | "When something matters, it asks instead of assuming." → v2 adds DCB's 61-researcher network, highlighted | Clarification + versioned revision (E29) |
| 9 | Chat, type: `Drop the nutrition study, they don't care about meals` → Enter | "She pushes back in plain words." → v3, GoCARB removed. Open the version menu: v1, v2, v3 | Natural-language refinement with history (E29) |
| 10 | **✓ Keep** Witthauer, Bally, *Needle-free glucose monitoring*, *Research on diabetes in women*, *Access to clinical research facilities*. **Hide** the other 7 (export stays locked until every item is kept or hidden) | "She decides what goes to the company; the tool doesn't. Nothing leaves without her review." | Human relevance judgement and review gate (E04, E14) |
| 11 | **Export (5)** → show the dialog → **PDF brief** (or **PowerPoint**) and open the file | "A short company-facing brief in the agency's template, every claim with its source in the appendix. Nothing leaves the laptop." | Teaser for the CEO (E13); offline export |
| 12 | **My cases** tab (`/cases`): GlucoWave in *In review* → ⋯ → move to **Pitch sent**. Optional: **My desk** now lists *Record the outcome · GlucoWave* | "And back on her board." | End-to-end workflow |

### Contrast cases (15–20 s, after step 12)

| Open | Shows | Say |
| --- | --- | --- |
| **Grain trader** (Closed) | *Out of scope* card | "Outside life sciences: it says so instead of forcing a match." |
| **Alpine Bioprint** (Closed) | *No reliable match* card | "No reliable evidence in the indexed pages: no matches rather than guesses. This is about our indexed sources, not proof Bern has no such expertise." |
| Optional: **Pumpline Medical** | A different company, with its own follow-up question pending | "The same flow works for an insulin-pump maker." |

### Close (architecture slide, not the app)

Show [architecture.html](../architecture.html): public pages → extraction →
PostgreSQL + pgvector hybrid search → Apertus on a Swiss endpoint → evidence pack
checked before any text is written → this UI. Name what is measured and what is
not (see "What runs where").

## Timing

- **Video (≤ 2:00):** steps 1, 3, 5, 7, 8, 9, 11, one contrast case. Cut the run
  stages to about 2 s.
- **Live pitch:** the full run sheet takes about 3:30 at a calm pace. The live pitch
  duration is still **unknown**
  ([event and submission](EVENT_AND_SUBMISSION.md)); trim from steps 4, 6 and 12 first.

## Do not say

- "It found …" about recall or accuracy: no retrieval quality has been measured.
- "Runs fully air-gapped": not tested.
- "The expert is available / will meet you": the brief only lists possible introductions.
- "Real company": GlucoWave and every other company on the board are synthetic.

## Prepared answers

- **Is this live?** "The interface and export are real; the results are recorded
  from real public pages. The live pipeline runs on our backend; we haven't
  published the full corpus yet, so we don't claim accuracy numbers."
- **Where do the quotes come from?** "Public UniBE, ARTORG and DCB pages, captured
  18 October; each card links to its page."
- **What about confidential documents?** "Not accepted by design: the agency told
  us business plans must never go into a model, local or not."
- **Can I type my own query?** In the mock: no, see the reliability rules. Offer
  the contrast cases.

## Seed data behind this script

- Hero prompt, first draft and follow-up: `HERO_PROMPT`, `HERO_REVISION`,
  `HERO_FOLLOW_UP` in [cases.ts](../../src/frontend/src/mocks/cases.ts). The hero is
  **not** on the board at start; the presenter creates it in step 1.
- Mock behaviour (routing, follow-up, exclusion): [mockApi.ts](../../src/frontend/src/api/mockApi.ts).
- Demo state is per browser (`localStorage` key `bern-navigator-demo-v7`).
  **Reset demo data** restores the seed.
