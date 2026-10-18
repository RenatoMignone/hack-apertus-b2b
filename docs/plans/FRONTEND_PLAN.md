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

Top navigation bar: logo, *My desk*, *My cases*, *Action items* (with an open-items badge), *New case*.

| Route | Screen |
| --- | --- |
| `/` | **My desk.** Greeting and three cards: *New case* (opens the composer); *My cases* (count, stacked status bar, 3 latest, link to the board); *Action items* (open count, top 3 questions, link) |
| `/cases` | **My cases board.** Kanban with one column per status; drag a card to change its status (the status pill on the card is the keyboard fallback) |
| `/actions` | **Action items.** Questions to ask agency colleagues, grouped by case, each with "Ask: role" and Asked / Done toggles; Open and Done tabs |
| `/cases/new` | **Composer.** One text box plus three example chips. Text only, public info only (E03, E28) |
| `/cases/:id` | **Workspace.** Results in the centre, chat on the right. Header: status, version menu, Export |

### Results (the output)

1. **Company card:** one-sentence description from her message, plus 3–4 fact chips.
   Then the **"Why Bern"** heading with institution dots.
2. **Reason cards**, numbered. Each card has a one-line headline, one plain sentence
   with citation chips `[n]`, and the Bern entries behind it (institution dot +
   name). Badges appear only when relevant: *Your lead ✓* (her suggestion was
   confirmed, E29) and *Idea · to validate* (adjacent application, E10). Each card
   has ✓ keep and ✕ not relevant controls. **Click** a card to expand the literal
   source quotes with the supporting span highlighted, plus page links.
3. **Open questions / limitations** as small pills on one line.
4. **"How I searched"** (collapsed by default): a Sankey of *her words → ontology
   terms searched → source entries*, where each entry is extracted from one URL and
   coloured by institution. Clicking an entry opens its quote.

The evidence drawer (over the chat) shows the quote with highlight, one relevance
line, *Open page*, institution and retrieval date. Empty results show a single
"Out of scope" or "No reliable match" card.

### Chat and versions

Agent replies are one or two lines. Follow-up questions come with answer buttons.
Each change creates a version (v1, v2, …) in the header menu. Changed reasons
flash and scroll into view. The mock understands *exclude …*, *focus on …*, *make it
shorter*, contact/availability questions (it answers that pages don't say), and
*explain simpler*. Anything else is acknowledged without changing the brief.

### Export

Uses only the ✓ kept reasons. The mock downloads a Markdown outline with sources;
PowerPoint rendering with the partner template is backend work.

## Data contract

Defined in `src/frontend/src/types/contract.ts`:

| Type | Purpose |
| --- | --- |
| `CaseSummary` | Cases row: id, companyLabel, oneLineNeed, status, timestamps, keptCount |
| `CaseDetail` | summary, `revisions[]`, `currentRevisionId`, `turns[]`, `evidence` map |
| `ActionItem` | id, caseId, question, askRole (colleague role), status open / asked / done |
| `BriefRevision` | `company` (summary, facts[]), `reasons[]`, `openQuestions[]`, `trace`, `coverage`, `changeNote`, `changedReasonIds`, optional `emptyMessage` |
| `Reason` | headline, `line` (`CitedText`), `entries[]` (name, institution, evidenceIds), `kind` direct/idea, `fromLead`, selection |
| `Evidence` | one entry extracted from one URL: short `label`, literal `excerpt` + `highlight`, url, title, institution, dates, one-line `relevance`, citation number `n` |
| `SearchTrace` | `inputs` (her phrases), `terms` (ontology terms), `links` input→term and term→evidence id, with weights |
| `DialogueTurn` | chat turn, optional `followUp` with choices |
| `Coverage` | snapshot date, institutions, short limitations, `resultKind` |

API (`src/frontend/src/api/index.ts`): `listCases`, `getCase`, `createCase`,
`runCase`, `sendMessage`, `answerFollowUp`, `setSelection`, `setStatus`,
`setCurrentRevision`, `exportDeck`, `listActionItems`, `setActionStatus`,
`subscribe` (change notifications); long calls report `RunStage`. To connect the
backend, implement `NavigatorApi` over HTTP and swap it in `api/index.ts`.

## Demo data

`src/frontend/src/mocks/`. Company names are synthetic. Evidence excerpts were
captured on 18 Oct 2026 via a web-fetch tool from the pilot pages in
[PILOT_SCOPE.md](../challenge/PILOT_SCOPE.md); check them against the live pages
before presenting them as exact quotes. No person names are used. The Sankey
input→term mappings are hand-written for the demo, not model output.

| Case | Shows |
| --- | --- |
| GlucoWave | 6 reasons → v2 without nutrition; menstrual-cycle lead confirmed by DCB |
| Pumpline Medical | Follow-up question; answering adds a reason (v2) |
| Grain trader | Out of scope |
| Six list-only cases | Status variety on the Cases page |

## Known gaps

- The Sankey can crowd labels when there are many terms; long entry names are truncated with a tooltip.
- No persistence: the mock store resets on reload.
- The pitch-only field map / "add field" showcase is not built.
