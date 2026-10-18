# Frontend — screens, data contract and mock-to-backend handoff

**18 October 2026 · Status: implemented on seeded mock data in `src/frontend/`.
Not connected to the backend. No retrieval, model or evaluation results are claimed.**
Decisions: D12–D14 in [DECISIONS_AND_OPEN_QUESTIONS.md](../project/DECISIONS_AND_OPEN_QUESTIONS.md).
Backend integration: map `NavigatorApi` onto the draft routes in
[FRONTEND_BACKEND_API.md](FRONTEND_BACKEND_API.md) (not done yet).

## Design rule

**As little text as possible.** The operator is a non-specialist who reviews
results quickly (E04, E12, E14). The output is a short list of clear reasons why
Bern fits the company. Details and sources appear only on click.

## Run

```text
cd src/frontend
npm install
npm run dev        # http://localhost:5173
npm run build      # typecheck + static bundle in dist/
```

Stack: Vite, React 18, TypeScript, Tailwind CSS 4, React Router, d3-sankey, lucide
icons, self-hosted Inter. No external requests at runtime, so it fits the
air-gapped target in [ARCHITECTURE.md](ARCHITECTURE.md). Source links open live
pages only when clicked.

## Screens

Top navigation bar: logo, *My desk*, *My cases*, *Action items* (with an open-items badge),
a *Demo* menu (explanation + *Reset demo data*), *New case*. Labels collapse to icons
below 768 px.

| Route | Screen |
| --- | --- |
| `/` | **My desk.** Greeting, a slim *Start a new case* banner, then two cards: *My cases* (count, status bar, *Continue: last opened case*, 3 latest, link to board) and *Action items* (top open questions with inline Done checkboxes) |
| `/cases` | **My cases board.** 4 columns: To research · In review · Pitch sent · Closed (with Visit / No interest outcome). *On hold* is a flag shown as a badge. Move cards by drag-and-drop or the card's ⋯ menu (Move to, Closed · outcome, Put on hold); every move shows a toast with Undo. Search box |
| `/actions` | **Action items.** Grouped by case: Done checkbox, *Mark asked* (shows "Awaiting answer"), answer note once done, and *+ Add question* (question + colleague role) per open case. Open / Done tabs |
| `/cases/new` | **Composer.** One text box, a "Public information only" note, a Ctrl+Enter hint, and example chips that never overwrite her text without asking (E03, E28) |
| `/cases/:id` | **Workspace.** Results in the centre. Header: company name, status, outcome/hold badges, compact version menu (v2 ▾), Export. A sticky jump bar links to the sections present. Chat on the right, collapsible (remembered), and an overlay drawer below 1100 px |

### Usability rules (D15)

- Every action gives feedback (toast), and destructive or moving actions offer **Undo**.
- Everything clickable is a real button or link, with a visible keyboard focus ring.
- Text is at least 12 px and colours meet WCAG AA contrast (axe-core: 0 violations).
- Demo state is kept in `localStorage` per browser; *Reset demo data* restores the seed.
- Each page sets its own tab title.

### Results (the output)

1. **Company card:** one-sentence description from her message, plus 3–4 fact chips.
   Then the **"Why Bern"** heading with institution dots.
2. **Categorized "Why Bern" elements**, in four sections: **People** (experts and
   key contacts: initials avatar, name, role exactly as the source states it, why
   they fit, source-page link; no emails or phone numbers), **Research groups**,
   **Projects & studies**, and **Ideas to explore**. Empty sections are hidden.
   Groups and projects share one running number. Each non-people card has a one-line headline, one plain sentence
   with citation chips `[n]`, and the Bern entries behind it (institution dot +
   name). Badges appear only when relevant: *Your lead ✓* (her suggestion was
   confirmed, E29) and *Idea · to validate* (adjacent application, E10). Each card
   has **✓ Keep** and **Hide** text buttons (Hide shows a toast with Undo and leaves a
   "hidden · Show again" line). The chevron or a click on the card expands the
   literal source quotes with the supporting span highlighted, plus page links.
3. **Open questions / limitations** as small pills on one line.
4. **Similar cases** (only when some exist): earlier agency cases with a 0–100
   similarity score and bar, shared aspects as chips, and their status. Clicking
   one opens that case. The score measures how similar the needs and topics are,
   not a chance of success. A real case-similarity method and data are still
   missing (OPERATIONS_PLAN `case_similarity_score`); the mock values are illustrative.
5. **"How I searched"** (collapsed by default): a Sankey of *her words → ontology
   terms searched → source entries*, where each entry is extracted from one URL and
   coloured by institution. Clicking an entry opens its quote.

The evidence drawer (a right-hand panel) shows the quote with highlight, one relevance
line, *Open page*, institution and retrieval date. Esc closes it and returns focus. Empty results show a single
"Out of scope" or "No reliable match" card.

### Chat and versions

Agent replies are one or two lines. Follow-up questions come with answer buttons.
Each change creates a version (v1, v2, …) in the header menu. Changed reasons
flash and scroll into view. Suggestion chips are derived from the case (e.g.
*Exclude <first idea>*, *Focus on <first group>*). The mock understands *exclude …*
(any topic), *focus on …*, *make it shorter* (top 2 per section), contact/availability
questions (it answers that pages don't say), and *explain simpler*. Anything else is
acknowledged without changing the brief.

### Export

Uses only the ✓ kept reasons. The mock downloads a Markdown outline with sources;
PowerPoint rendering with the partner template is backend work.

## Data contract

Defined in `src/frontend/src/types/contract.ts`:

| Type | Purpose |
| --- | --- |
| `CaseSummary` | Cases row: id, companyLabel, oneLineNeed, `status` researching / in_review / pitch_sent / closed, optional `outcome` visit / no_interest, `onHold`, timestamps, keptCount |
| `CaseDetail` | summary, `revisions[]`, `currentRevisionId`, `turns[]`, `evidence` map |
| `ActionItem` | id, caseId, question, askRole (colleague role), status open / asked / done, optional `answer` |
| `SimilarCase` | caseId, companyLabel, score 0–100, shared[], status, optional outcome |
| `BriefRevision` | `company` (summary, facts[]), `reasons[]`, `similarCases[]`, `openQuestions[]`, `trace`, `coverage`, `changeNote`, `changedReasonIds`, optional `emptyMessage` |
| `Reason` | `category` people / groups / projects / ideas, headline (a person's name for people), `line` (`CitedText`), `entries[]` (name, optional `role`, institution, evidenceIds), `kind` direct/idea, `fromLead`, selection |
| `Evidence` | one entry extracted from one URL: short `label`, literal `excerpt` + `highlight`, url, title, institution, dates, one-line `relevance`, citation number `n` |
| `SearchTrace` | `inputs` (her phrases), `terms` (ontology terms), `links` input→term and term→evidence id, with weights |
| `DialogueTurn` | chat turn, optional `followUp` with choices |
| `Coverage` | snapshot date, institutions, short limitations, `resultKind` |

API (`src/frontend/src/api/index.ts`): `listCases`, `getCase`, `createCase`,
`runCase`, `sendMessage`, `answerFollowUp`, `setSelection`, `setStatus`,
`setCurrentRevision`, `exportDeck`, `getLastOpened`, `setCaseFlags` (onHold / outcome),
`listActionItems`, `setActionStatus` (with optional answer), `addActionItem`,
`subscribe` (change notifications) and, mock only, `resetDemo`; long calls report `RunStage`. To connect the
backend, implement `NavigatorApi` over HTTP and swap it in `api/index.ts`.

## Demo data

`src/frontend/src/mocks/`. Company names are synthetic. Evidence excerpts were
captured on 18 Oct 2026 via a web-fetch tool from the pilot pages in
[PILOT_SCOPE.md](../challenge/PILOT_SCOPE.md); check them against the live pages
before presenting them as exact quotes. People (Lia Bally, Stavroula
Mougiakakou, and the DCB professors Witthauer, Koch, Garcia) are named only as
their source pages state them: the Bally Lab team page, the ARTORG AIHN page, and
the DCB professorships release of 10 Apr 2026 (German, via pressetext). The Sankey
input→term mappings are hand-written for the demo, not model output.

| Case | Shows |
| --- | --- |
| GlucoWave | 6 reasons → v2 without nutrition; menstrual-cycle lead confirmed by DCB |
| Pumpline Medical | Follow-up question; answering adds a reason (v2) |
| Grain trader | Out of scope |
| Six smaller cases | Board variety (incl. outcomes and on hold); each opens to a short brief built only from the evidence above (Alpine Bioprint is a no-match) |

## Known gaps

- The Sankey can crowd labels when there are many terms; long entry names are truncated with a tooltip.
- Demo persistence is per browser (`localStorage`); there is no shared or server state.
- Narrow layouts are supported down to about 768 px; there is no phone layout.
- The pitch-only field map / "add field" showcase is not built.
