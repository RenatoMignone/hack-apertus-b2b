import type { ActionItem, BriefRevision, CaseDetail, CaseSummary, Coverage, Reason, SearchTrace } from '../types/contract';
import { EVIDENCE } from './evidence';

// Seeded demo cases. Company names are synthetic. Institutions, projects and
// excerpts come from public pages (see evidence.ts). No person names are used:
// the captured pages do not name contacts.

const coverage = (resultKind: Coverage['resultKind'], limitations: string[] = []): Coverage => ({
  snapshotDate: '18 Oct 2026',
  institutions: ['UniBE', 'ARTORG', 'DCB'],
  limitations,
  resultKind,
});

/** Removes trace links/terms/inputs that no longer lead to a kept evidence entry. */
export function pruneTrace(trace: SearchTrace, evidenceIds: Set<string>): SearchTrace {
  const termIds = new Set(trace.terms.map((t) => t.id));
  const termLinks = trace.links.filter((l) => termIds.has(l.source) && evidenceIds.has(l.target));
  const liveTerms = new Set(termLinks.map((l) => l.source));
  const inputLinks = trace.links.filter((l) => !termIds.has(l.source) && liveTerms.has(l.target));
  const liveInputs = new Set(inputLinks.map((l) => l.source));
  return {
    inputs: trace.inputs.filter((i) => liveInputs.has(i.id)),
    terms: trace.terms.filter((t) => liveTerms.has(t.id)),
    links: [...inputLinks, ...termLinks],
  };
}

export const reasonEvidence = (reasons: Reason[]) =>
  new Set(reasons.flatMap((r) => [...r.line.evidenceIds, ...r.entries.flatMap((e) => e.evidenceIds)]));

// ---------- Case A: wearable glucose sensor ----------

const PROMPT_A =
  'GlucoWave (demo) builds a needle-free wearable glucose sensor. They want partners for clinical studies and the ' +
  'algorithms behind it, and are considering a Swiss R&D site. Most early users are women. I think DCB did something ' +
  'on diabetes and the menstrual cycle.';

const reasonsA: Reason[] = [
  {
    id: 'rA-needlefree',
    headline: 'Needle-free glucose monitoring is already researched here',
    line: { text: 'DCB runs a pilot study on painless, needle-free monitoring.', evidenceIds: ['ev-dcb-spn005'] },
    entries: [{ id: 'eA-spn', name: 'SPN-005 pilot study', institution: 'DCB', evidenceIds: ['ev-dcb-spn005'] }],
    kind: 'direct',
    selection: 'none',
  },
  {
    id: 'rA-biomarkers',
    headline: 'Experts who validate digital biomarkers',
    line: { text: 'Bally Lab develops and evaluates new digital biomarkers.', evidenceIds: ['ev-bally-biomarkers'] },
    entries: [{ id: 'eA-bally', name: 'Bally Lab', institution: 'UniBE', evidenceIds: ['ev-bally-biomarkers', 'ev-bally-aid'] }],
    kind: 'direct',
    selection: 'none',
  },
  {
    id: 'rA-ai',
    headline: 'AI that turns readings into personalised care',
    line: { text: 'ARTORG builds AI for adaptive, personalised diabetes care.', evidenceIds: ['ev-adaptive-ai'] },
    entries: [{ id: 'eA-adm', name: 'Adaptive Diabetes Management', institution: 'ARTORG', evidenceIds: ['ev-adaptive-ai', 'ev-adaptive-proactive'] }],
    kind: 'direct',
    selection: 'none',
  },
  {
    id: 'rA-women',
    headline: 'Research on diabetes in women',
    line: { text: 'DCB studied how the menstrual cycle relates to insulin needs.', evidenceIds: ['ev-dcb-menstrual'] },
    entries: [{ id: 'eA-cycle', name: 'Menstrual Cycle Study', institution: 'DCB', evidenceIds: ['ev-dcb-menstrual'] }],
    kind: 'direct',
    fromLead: true,
    selection: 'none',
  },
  {
    id: 'rA-trial',
    headline: 'Clinical-trial experience with diabetes tools',
    line: { text: 'ARTORG’s GoCARB nutrition tool was validated in a clinical trial.', evidenceIds: ['ev-gocarb-trial'] },
    entries: [{ id: 'eA-gocarb', name: 'GoCARB', institution: 'ARTORG', evidenceIds: ['ev-gocarb-trial', 'ev-gocarb-project'] }],
    kind: 'direct',
    selection: 'none',
  },
  {
    id: 'rA-metabolite',
    headline: 'Future idea: sensing several metabolites at once',
    line: { text: 'Early-stage DCB chemistry for continuous multi-metabolite measurement.', evidenceIds: ['ev-dcb-porphyrin'] },
    entries: [{ id: 'eA-porph', name: 'Illuminating Personalized Medicine', institution: 'DCB', evidenceIds: ['ev-dcb-porphyrin'] }],
    kind: 'idea',
    selection: 'none',
  },
];

const traceA: SearchTrace = {
  inputs: [
    { id: 'in-sensor', label: 'glucose sensor' },
    { id: 'in-needle', label: 'needle-free' },
    { id: 'in-algo', label: 'algorithms' },
    { id: 'in-clinical', label: 'clinical studies' },
    { id: 'in-women', label: 'women' },
  ],
  terms: [
    { id: 't-cgm', label: 'continuous glucose monitoring' },
    { id: 't-noninv', label: 'non-invasive monitoring' },
    { id: 't-biomarker', label: 'digital biomarkers' },
    { id: 't-personal', label: 'personalised diabetes care' },
    { id: 't-validation', label: 'clinical validation' },
    { id: 't-cycle', label: 'menstrual cycle & diabetes' },
  ],
  links: [
    { source: 'in-sensor', target: 't-cgm', value: 2 },
    { source: 'in-sensor', target: 't-biomarker', value: 1 },
    { source: 'in-needle', target: 't-noninv', value: 2 },
    { source: 'in-algo', target: 't-personal', value: 2 },
    { source: 'in-clinical', target: 't-validation', value: 2 },
    { source: 'in-clinical', target: 't-biomarker', value: 1 },
    { source: 'in-women', target: 't-cycle', value: 1 },
    { source: 't-cgm', target: 'ev-dcb-spn005', value: 1 },
    { source: 't-cgm', target: 'ev-dcb-porphyrin', value: 1 },
    { source: 't-noninv', target: 'ev-dcb-spn005', value: 1 },
    { source: 't-noninv', target: 'ev-dcb-porphyrin', value: 1 },
    { source: 't-biomarker', target: 'ev-bally-biomarkers', value: 2 },
    { source: 't-personal', target: 'ev-adaptive-ai', value: 1 },
    { source: 't-personal', target: 'ev-adaptive-proactive', value: 1 },
    { source: 't-validation', target: 'ev-gocarb-trial', value: 1 },
    { source: 't-validation', target: 'ev-bally-aid', value: 1 },
    { source: 't-cycle', target: 'ev-dcb-menstrual', value: 1 },
  ],
};

const revA1: BriefRevision = {
  id: 'revA-1',
  version: 1,
  createdAt: '2026-10-18T14:05:00Z',
  changeNote: 'First version',
  changedReasonIds: [],
  company: {
    summary: 'Builds a needle-free wearable glucose sensor and is looking for a Swiss R&D base.',
    facts: ['Medtech', 'Wearable sensor', 'Users mostly women', 'Wants: clinical + algorithm partners'],
  },
  reasons: reasonsA,
  openQuestions: ['Which sensing method do they use?', 'Study partner, R&D site, or both?'],
  similarCases: [
    { caseId: 'case-d1', companyLabel: 'NordSense', score: 78, shared: ['Non-invasive sensing', 'Metabolite monitoring'], status: 'pitch_sent' },
    { caseId: 'case-d4', companyLabel: 'MedPatch', score: 61, shared: ['Wearable device', 'Clinical validation'], status: 'pitch_sent' },
    { caseId: 'case-d3', companyLabel: 'Diabeto App', score: 44, shared: ['Diabetes', 'Algorithms'], status: 'on_hold' },
  ],
  trace: traceA,
  coverage: coverage('ok', ['No named contacts on the retrieved pages.']),
};

const reasonsA2 = reasonsA.filter((r) => r.id !== 'rA-trial');
const revA2: BriefRevision = {
  ...revA1,
  id: 'revA-2',
  version: 2,
  parentId: 'revA-1',
  createdAt: '2026-10-18T14:12:00Z',
  changeNote: 'Removed nutrition',
  changedReasonIds: [],
  reasons: reasonsA2,
  trace: pruneTrace(traceA, reasonEvidence(reasonsA2)),
};

const caseA: CaseDetail = {
  case: {
    id: 'case-glucowave',
    companyLabel: 'GlucoWave',
    oneLineNeed: 'Needle-free glucose sensor: validation + algorithms',
    status: 'in_review',
    createdAt: '2026-10-18T14:00:00Z',
    updatedAt: '2026-10-18T14:12:00Z',
    keptCount: 0,
  },
  revisions: [revA1, revA2],
  currentRevisionId: 'revA-2',
  turns: [
    { id: 'tA-1', role: 'operator', text: PROMPT_A, createdAt: '2026-10-18T14:00:00Z' },
    { id: 'tA-2', role: 'agent', text: 'Found 6 reasons across UniBE, ARTORG and DCB. Your menstrual-cycle lead checks out.', createdAt: '2026-10-18T14:05:00Z', revisionId: 'revA-1' },
    { id: 'tA-3', role: 'operator', text: 'Drop the nutrition stuff, they don’t care about meals.', createdAt: '2026-10-18T14:11:00Z' },
    { id: 'tA-4', role: 'agent', text: 'Removed the nutrition reason.', createdAt: '2026-10-18T14:12:00Z', revisionId: 'revA-2' },
  ],
  evidence: EVIDENCE,
};

// ---------- Case B: insulin delivery, follow-up pending ----------

const PROMPT_B =
  'Pumpline Medical (demo), European insulin pump maker. Wants to add automated insulin delivery (closed loop) to its next pump and is looking at Bern for R&D.';

const reasonsB: Reason[] = [
  {
    id: 'rB-closedloop',
    headline: 'Closed-loop insulin delivery research',
    line: { text: 'Bally Lab works on closed-loop automated insulin delivery.', evidenceIds: ['ev-bally-aid'] },
    entries: [{ id: 'eB-bally', name: 'Bally Lab', institution: 'UniBE', evidenceIds: ['ev-bally-aid'] }],
    kind: 'direct',
    selection: 'none',
  },
  {
    id: 'rB-study',
    headline: 'An active automated-insulin-delivery study',
    line: { text: 'DCB studies therapies used alongside automated insulin delivery.', evidenceIds: ['ev-dcb-aidjunct'] },
    entries: [{ id: 'eB-junct', name: 'AID-JUNCT study', institution: 'DCB', evidenceIds: ['ev-dcb-aidjunct'] }],
    kind: 'direct',
    selection: 'none',
  },
  {
    id: 'rB-ai',
    headline: 'AI for personalised insulin decisions',
    line: { text: 'ARTORG builds AI for adaptive, personalised diabetes care.', evidenceIds: ['ev-adaptive-ai'] },
    entries: [{ id: 'eB-adm', name: 'Adaptive Diabetes Management', institution: 'ARTORG', evidenceIds: ['ev-adaptive-ai'] }],
    kind: 'idea',
    selection: 'none',
  },
];

export const NETWORK_REASON: Reason = {
  id: 'rB-network',
  headline: 'A 61-researcher diabetes-technology network',
  line: { text: '61 researchers work across the four DCB professorships.', evidenceIds: ['ev-dcb-network'] },
  entries: [{ id: 'eB-net', name: 'DCB research professorships', institution: 'DCB', evidenceIds: ['ev-dcb-network'] }],
  kind: 'direct',
  selection: 'none',
};

export const TRACE_B: SearchTrace = {
  inputs: [
    { id: 'in-pump', label: 'insulin pump' },
    { id: 'in-loop', label: 'closed loop' },
    { id: 'in-rnd', label: 'R&D' },
  ],
  terms: [
    { id: 't-aid', label: 'automated insulin delivery' },
    { id: 't-adjunct', label: 'adjunctive therapy' },
    { id: 't-personal', label: 'personalised diabetes care' },
    { id: 't-network', label: 'diabetes technology research' },
  ],
  links: [
    { source: 'in-pump', target: 't-aid', value: 2 },
    { source: 'in-loop', target: 't-aid', value: 2 },
    { source: 'in-loop', target: 't-adjunct', value: 1 },
    { source: 'in-rnd', target: 't-personal', value: 1 },
    { source: 'in-rnd', target: 't-network', value: 1 },
    { source: 't-aid', target: 'ev-bally-aid', value: 2 },
    { source: 't-aid', target: 'ev-dcb-aidjunct', value: 1 },
    { source: 't-adjunct', target: 'ev-dcb-aidjunct', value: 1 },
    { source: 't-personal', target: 'ev-adaptive-ai', value: 1 },
    { source: 't-network', target: 'ev-dcb-network', value: 1 },
  ],
};

const revB1: BriefRevision = {
  id: 'revB-1',
  version: 1,
  createdAt: '2026-10-18T13:20:00Z',
  changeNote: 'First version',
  changedReasonIds: [],
  company: {
    summary: 'European insulin pump maker adding automated (closed-loop) insulin delivery to its next pump.',
    facts: ['Medtech', 'Insulin pumps', 'Next-gen product', 'Wants: R&D in Bern'],
  },
  reasons: reasonsB,
  openQuestions: ['R&D partner or clinical validation?'],
  similarCases: [
    { caseId: 'case-d2', companyLabel: 'InsuTech Labs', score: 72, shared: ['Insulin delivery', 'R&D site'], status: 'closed_visit' },
    { caseId: 'case-d5', companyLabel: 'Kardia Systems', score: 38, shared: ['Diabetes device'], status: 'draft' },
  ],
  trace: pruneTrace(TRACE_B, reasonEvidence(reasonsB)),
  coverage: coverage('partial', ['Waiting for your answer in the chat.']),
};

const caseB: CaseDetail = {
  case: {
    id: 'case-pumpline',
    companyLabel: 'Pumpline Medical',
    oneLineNeed: 'Add closed-loop insulin delivery to next pump',
    status: 'researching',
    createdAt: '2026-10-18T13:15:00Z',
    updatedAt: '2026-10-18T13:21:00Z',
    keptCount: 0,
  },
  revisions: [revB1],
  currentRevisionId: 'revB-1',
  turns: [
    { id: 'tB-1', role: 'operator', text: PROMPT_B, createdAt: '2026-10-18T13:15:00Z' },
    {
      id: 'tB-2',
      role: 'agent',
      text: 'First draft ready. One question:',
      createdAt: '2026-10-18T13:21:00Z',
      revisionId: 'revB-1',
      followUp: { id: 'fB-1', question: 'R&D partner or clinical validation?', choices: ['R&D partner', 'Clinical validation', 'Both'] },
    },
  ],
  evidence: EVIDENCE,
};

// ---------- Case C: out of scope ----------

const PROMPT_C = 'Swiss grain trading firm (demo) looking for commodity-trading partners and logistics hubs in Bern.';

export const emptyRevision = (id: string, resultKind: Coverage['resultKind'], message: string): BriefRevision => ({
  id,
  version: 1,
  createdAt: '2026-10-18T12:00:00Z',
  changeNote: 'First version',
  changedReasonIds: [],
  reasons: [],
  openQuestions: [],
  trace: { inputs: [], terms: [], links: [] },
  coverage: coverage(resultKind),
  emptyMessage: message,
});

const caseC: CaseDetail = {
  case: {
    id: 'case-grain',
    companyLabel: 'Grain trader',
    oneLineNeed: 'Commodity trading partners',
    status: 'closed_no_interest',
    createdAt: '2026-10-18T12:00:00Z',
    updatedAt: '2026-10-18T12:01:00Z',
    keptCount: 0,
  },
  revisions: [emptyRevision('revC-1', 'out_of_scope', 'Outside life sciences. I only cover UniBE, ARTORG and DCB research.')],
  currentRevisionId: 'revC-1',
  turns: [
    { id: 'tC-1', role: 'operator', text: PROMPT_C, createdAt: '2026-10-18T12:00:00Z' },
    { id: 'tC-2', role: 'agent', text: 'Out of scope, so no matches rather than guesses.', createdAt: '2026-10-18T12:01:00Z', revisionId: 'revC-1' },
  ],
  evidence: EVIDENCE,
};

// ---------- List-only cases ----------

const listOnly = (id: string, companyLabel: string, oneLineNeed: string, status: CaseSummary['status'], updatedAt: string, keptCount: number): CaseDetail => ({
  case: { id, companyLabel, oneLineNeed, status, createdAt: updatedAt, updatedAt, keptCount },
  revisions: [],
  turns: [],
  evidence: EVIDENCE,
});

// ---------- Action items: questions for agency colleagues ----------

export const SEED_ACTIONS: ActionItem[] = [
  { id: 'a1', caseId: 'case-glucowave', question: 'Do we already know anyone at Diabetes Center Berne?', askRole: 'Life-sciences lead', status: 'open' },
  { id: 'a2', caseId: 'case-glucowave', question: 'Has SGE shared their timeline for a Swiss R&D site?', askRole: 'Account owner', status: 'asked' },
  { id: 'a3', caseId: 'case-glucowave', question: 'Which sensing method do they use?', askRole: 'Account owner', status: 'open' },
  { id: 'a4', caseId: 'case-pumpline', question: 'Do they already have a Swiss entity?', askRole: 'Account owner', status: 'open' },
  { id: 'a5', caseId: 'case-pumpline', question: 'Have we pitched closed-loop research to a pump maker before?', askRole: 'Life-sciences lead', status: 'open' },
  { id: 'a6', caseId: 'case-d1', question: 'Did the company reply to the pitch?', askRole: 'Account owner', status: 'done' },
  { id: 'a7', caseId: 'case-d4', question: 'Any update on the planned visit date?', askRole: 'Account owner', status: 'open' },
  { id: 'a8', caseId: 'case-d3', question: 'Is the project still funded?', askRole: 'Investment team', status: 'done' },
];

export const SEED_CASES: CaseDetail[] = [
  caseA,
  caseB,
  caseC,
  listOnly('case-d1', 'NordSense', 'Sweat-based metabolite sensing', 'pitch_sent', '2026-10-15T09:30:00Z', 6),
  listOnly('case-d2', 'InsuTech Labs', 'Insulin stability research', 'closed_visit', '2026-10-02T16:10:00Z', 8),
  listOnly('case-d3', 'Diabeto App', 'Clinical evidence for coaching app', 'on_hold', '2026-09-28T11:00:00Z', 3),
  listOnly('case-d4', 'MedPatch', 'Adhesive wearable patches', 'pitch_sent', '2026-10-11T14:45:00Z', 5),
  listOnly('case-d5', 'Kardia Systems', 'Remote monitoring: diabetes add-on', 'draft', '2026-10-17T08:20:00Z', 0),
  listOnly('case-d6', 'Alpine Bioprint', 'Tissue models', 'closed_no_interest', '2026-09-20T10:00:00Z', 0),
];
