import type { BriefRevision, CaseDetail, CaseOutcome, CaseStatus, Coverage, Institution, Reason, SearchTrace } from '../types/contract';
import { EVIDENCE } from './evidence';

// Seeded demo cases. Company names are synthetic. Institutions, projects, people
// and excerpts come from public pages (see evidence.ts); people are named only
// as their source pages state them.

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

// ---------- Hero case: HelioSense, wearable glucose sensor ----------
// Fictional company from the demo fixture (HelioSense case brief). Not on the board
// at start: the presenter creates it live from the composer's "HelioSense" example
// (see docs/project/DEMO_SCRIPT.md). The prompt uses everyday words ("measures
// blood sugar continuously") so the search trace shows the bridge to scientific
// terms such as continuous glucose monitoring.

export const HERO_PROMPT =
  'HelioSense is a fictional early-stage Swiss medtech building a wearable that measures blood sugar continuously, ' +
  'without finger pricks. No validated prototype or clinical data yet. They want an early, non-clinical R&D partner in Bern ' +
  'for the sensor, for making sense of the readings and for device testing, and want to know what clinical research access exists for later.';

/** The agent's one clarification question for the hero case. */
export const HERO_FOLLOW_UP = { question: 'Early R&D only, or clinical studies later too?', choices: ['Early R&D only', 'Clinical studies later too'] };

// Unit paths, expertise and missing fields only restate what the captured pages
// say; anything a page does not state is listed in missingFields.
const DCB_PATH = ['Diabetes Center Berne'];
const BALLY_PATH = ['University of Bern', 'Department for BioMedical Research (DBMR)', 'Bally Lab'];
const AIHN_PATH = ['University of Bern', 'ARTORG Center', 'AI in Health and Nutrition (AIHN)'];

const reasonsA: Reason[] = [
  {
    id: 'pA-witthauer',
    category: 'people',
    headline: 'Prof. Dr. Lilian Witthauer',
    line: { text: 'Holds DCB’s sensor-technology professorship, the core of HelioSense’s wearable.', evidenceIds: ['ev-dcb-profs-a'] },
    entries: [{ id: 'eA-witt', name: 'Prof. Dr. Lilian Witthauer', role: 'DCB professorship · Sensortechnologie', institution: 'DCB', unitPath: [...DCB_PATH, 'DCB professorships'], expertise: ['Sensor technology'], evidenceIds: ['ev-dcb-profs-a'] }],
    missingFields: ['Contact details', 'Projects'],
    kind: 'direct',
    selection: 'none',
  },
  {
    id: 'pA-koch',
    category: 'people',
    headline: 'Prof. Dr. Lisa Koch',
    line: { text: 'Holds DCB’s data-science and machine-learning professorship, relevant to making sense of the sensor readings.', evidenceIds: ['ev-dcb-profs-a'] },
    entries: [{ id: 'eA-koch', name: 'Prof. Dr. Lisa Koch', role: 'DCB professorship · Data Science und Machine Learning', institution: 'DCB', unitPath: [...DCB_PATH, 'DCB professorships'], expertise: ['Data science', 'Machine learning'], evidenceIds: ['ev-dcb-profs-a'] }],
    missingFields: ['Contact details', 'Projects'],
    kind: 'direct',
    selection: 'none',
  },
  {
    id: 'pA-bally',
    category: 'people',
    headline: 'Dr. med. Dr. phil. Lia Bally',
    line: { text: 'Leads the lab that evaluates digital biomarkers.', evidenceIds: ['ev-bally-team', 'ev-bally-biomarkers'] },
    entries: [{ id: 'eA-lbally', name: 'Dr. med. Dr. phil. Lia Bally', role: 'Group Leader, Bally Lab (DBMR)', institution: 'UniBE', unitPath: BALLY_PATH, expertise: ['Digital biomarkers', 'Automated insulin delivery'], evidenceIds: ['ev-bally-team'] }],
    missingFields: ['Contact details'],
    kind: 'direct',
    selection: 'none',
  },
  {
    id: 'pA-mougiakakou',
    category: 'people',
    headline: 'Prof. Dr. Stavroula Mougiakakou',
    line: { text: 'Contact for ARTORG’s AI-in-health group working on personalised diabetes management.', evidenceIds: ['ev-aihn-contact'] },
    entries: [{ id: 'eA-moug', name: 'Prof. Dr. Stavroula Mougiakakou', role: 'Contact, AI in Health and Nutrition (ARTORG)', institution: 'ARTORG', unitPath: AIHN_PATH, expertise: ['AI for personalised diagnosis and management'], evidenceIds: ['ev-aihn-contact'] }],
    missingFields: ['Formal role (the page lists her as contact only)'],
    kind: 'direct',
    selection: 'none',
  },
  {
    id: 'rA-needlefree',
    category: 'projects',
    headline: 'Needle-free glucose monitoring is already researched here',
    line: { text: 'DCB runs a pilot study on painless, needle-free monitoring.', evidenceIds: ['ev-dcb-spn005'] },
    entries: [{ id: 'eA-spn', name: 'SPN-005 pilot study', institution: 'DCB', unitPath: [...DCB_PATH, 'Projects'], expertise: ['Needle-free glucose monitoring'], evidenceIds: ['ev-dcb-spn005'] }],
    missingFields: ['Project lead', 'Status and results'],
    kind: 'direct',
    selection: 'none',
  },
  {
    id: 'rA-biomarkers',
    category: 'groups',
    headline: 'Experts who validate digital biomarkers',
    line: { text: 'Bally Lab develops and evaluates new digital biomarkers.', evidenceIds: ['ev-bally-biomarkers'] },
    entries: [{ id: 'eA-bally', name: 'Bally Lab', institution: 'UniBE', unitPath: BALLY_PATH, expertise: ['Digital biomarkers', 'Closed-loop insulin delivery', 'Individualized therapy'], evidenceIds: ['ev-bally-biomarkers', 'ev-bally-aid'] }],
    missingFields: [],
    kind: 'direct',
    selection: 'none',
  },
  {
    id: 'rA-ai',
    category: 'groups',
    headline: 'AI that turns readings into personalised care',
    line: { text: 'ARTORG builds AI for adaptive, personalised diabetes care.', evidenceIds: ['ev-adaptive-ai'] },
    entries: [{ id: 'eA-adm', name: 'Adaptive Diabetes Management', institution: 'ARTORG', unitPath: [...AIHN_PATH, 'Adaptive Diabetes Management'], expertise: ['AI for diabetes care', 'Personalised care'], evidenceIds: ['ev-adaptive-ai', 'ev-adaptive-proactive'] }],
    missingFields: ['Named contact', 'Projects'],
    kind: 'direct',
    selection: 'none',
  },
  {
    id: 'rA-moonwalk',
    category: 'projects',
    headline: 'Glucose data combined with wearable motion data',
    line: { text: 'DCB studies how glucose values relate to motion patterns during sleep.', evidenceIds: ['ev-dcb-moonwalk'] },
    entries: [{ id: 'eA-moon', name: 'Moonwalk Project', institution: 'DCB', unitPath: [...DCB_PATH, 'Projects'], expertise: ['Glucose values', 'Motion patterns'], evidenceIds: ['ev-dcb-moonwalk'] }],
    missingFields: ['Project lead', 'Status and results'],
    kind: 'direct',
    selection: 'none',
  },
  {
    id: 'rA-trial',
    category: 'projects',
    headline: 'Clinical-trial experience with diabetes tools',
    line: { text: 'ARTORG’s GoCARB nutrition tool was validated in a clinical trial.', evidenceIds: ['ev-gocarb-trial'] },
    entries: [{ id: 'eA-gocarb', name: 'GoCARB', institution: 'ARTORG', unitPath: [...AIHN_PATH, 'Intelligent Nutrition'], expertise: ['Carbohydrate estimation', 'Clinical validation'], evidenceIds: ['ev-gocarb-trial', 'ev-gocarb-project'] }],
    missingFields: ['Named contact'],
    kind: 'direct',
    selection: 'none',
  },
  {
    id: 'iA-clinical',
    category: 'infrastructure',
    headline: 'Access to clinical research facilities, for later',
    line: { text: 'DCB states it provides access to clinical research facilities for diabetes technology.', evidenceIds: ['ev-dcb-clinical'] },
    entries: [{ id: 'eA-clin', name: 'DCB clinical research access', institution: 'DCB', unitPath: DCB_PATH, expertise: ['Clinical research'], evidenceIds: ['ev-dcb-clinical'] }],
    missingFields: ['Access conditions for companies', 'Costs'],
    kind: 'direct',
    selection: 'none',
  },
  {
    id: 'iA-cores',
    category: 'infrastructure',
    headline: 'Shared lab core facilities',
    line: { text: 'DBMR core facilities provide genomics, live-cell imaging and proteomics services.', evidenceIds: ['ev-dbmr-cores'] },
    entries: [{ id: 'eA-cores', name: 'DBMR Core Facilities', institution: 'UniBE', unitPath: ['University of Bern', 'Department for BioMedical Research (DBMR)', 'Core Facilities'], expertise: ['Genomics', 'Live cell imaging', 'Proteomics'], evidenceIds: ['ev-dbmr-cores'] }],
    missingFields: ['Access for external companies', 'Costs'],
    kind: 'direct',
    selection: 'none',
  },
  {
    id: 'rA-metabolite',
    category: 'ideas',
    headline: 'Future idea: sensing several metabolites at once',
    line: { text: 'Early-stage DCB chemistry for continuous multi-metabolite measurement.', evidenceIds: ['ev-dcb-porphyrin'] },
    entries: [{ id: 'eA-porph', name: 'Illuminating Personalized Medicine', institution: 'DCB', unitPath: [...DCB_PATH, 'Projects'], expertise: ['Multi-metabolite sensing'], evidenceIds: ['ev-dcb-porphyrin'] }],
    missingFields: ['Project lead', 'Status'],
    kind: 'idea',
    selection: 'none',
  },
];

const traceA: SearchTrace = {
  inputs: [
    { id: 'in-sensor', label: 'measures blood sugar continuously' },
    { id: 'in-needle', label: 'without finger pricks' },
    { id: 'in-algo', label: 'making sense of the readings' },
    { id: 'in-clinical', label: 'device testing' },
  ],
  terms: [
    { id: 't-cgm', label: 'continuous glucose monitoring' },
    { id: 't-noninv', label: 'non-invasive monitoring' },
    { id: 't-biomarker', label: 'digital biomarkers' },
    { id: 't-personal', label: 'personalised diabetes care' },
    { id: 't-validation', label: 'clinical validation' },
    { id: 't-wearable', label: 'wearable sensor data' },
  ],
  links: [
    { source: 'in-sensor', target: 't-cgm', value: 2 },
    { source: 'in-sensor', target: 't-wearable', value: 1 },
    { source: 'in-needle', target: 't-noninv', value: 2 },
    { source: 'in-algo', target: 't-personal', value: 2 },
    { source: 'in-algo', target: 't-wearable', value: 1 },
    { source: 'in-clinical', target: 't-validation', value: 2 },
    { source: 'in-clinical', target: 't-biomarker', value: 1 },
    { source: 't-cgm', target: 'ev-dcb-spn005', value: 1 },
    { source: 't-cgm', target: 'ev-dcb-porphyrin', value: 1 },
    { source: 't-noninv', target: 'ev-dcb-spn005', value: 1 },
    { source: 't-noninv', target: 'ev-dcb-porphyrin', value: 1 },
    { source: 't-biomarker', target: 'ev-bally-biomarkers', value: 2 },
    { source: 't-personal', target: 'ev-adaptive-ai', value: 1 },
    { source: 't-personal', target: 'ev-adaptive-proactive', value: 1 },
    { source: 't-validation', target: 'ev-gocarb-trial', value: 1 },
    { source: 't-validation', target: 'ev-bally-aid', value: 1 },
    { source: 't-wearable', target: 'ev-dcb-moonwalk', value: 1 },
    { source: 't-cgm', target: 'ev-dcb-profs-a', value: 1 },
    { source: 't-personal', target: 'ev-aihn-contact', value: 1 },
    { source: 't-validation', target: 'ev-dcb-clinical', value: 1 },
    { source: 't-biomarker', target: 'ev-dbmr-cores', value: 1 },
    { source: 't-biomarker', target: 'ev-bally-team', value: 1 },
  ],
};

/** First draft for the hero case, served by the mock when the hero prompt runs. */
export const HERO_REVISION: BriefRevision = {
  id: 'revA-1',
  version: 1,
  createdAt: '2026-10-19T14:05:00Z',
  changeNote: 'First version',
  changedReasonIds: [],
  company: {
    summary: 'Fictional early-stage Swiss medtech building a wearable for continuous glucose monitoring without finger pricks.',
    facts: ['Fictional demo company', 'Medtech', 'Wearable sensor', 'No validated prototype yet', 'Wants: early, non-clinical R&D partner'],
  },
  reasons: reasonsA,
  openQuestions: ['Which sensing method do they use?', HERO_FOLLOW_UP.question],
  similarCases: [
    { caseId: 'case-d1', companyLabel: 'NordSense', score: 78, shared: ['Non-invasive sensing', 'Metabolite monitoring'], status: 'pitch_sent' },
    { caseId: 'case-d4', companyLabel: 'MedPatch', score: 61, shared: ['Wearable device', 'Clinical validation'], status: 'pitch_sent' },
    { caseId: 'case-d3', companyLabel: 'Diabeto App', score: 44, shared: ['Diabetes', 'Algorithms'], status: 'researching' },
  ],
  trace: traceA,
  coverage: coverage('partial', [
    'Waiting for your answer in the chat.',
    'Contact details: public profile pages only.',
    'HelioSense is a fictional scenario; only the Bern facts come from public pages.',
  ]),
};

// ---------- Case B: insulin delivery, follow-up pending ----------

const PROMPT_B =
  'Pumpline Medical (demo), European insulin pump maker. Wants to add automated insulin delivery (closed loop) to its next pump and is looking at Bern for R&D.';

const reasonsB: Reason[] = [
  {
    id: 'pB-garcia',
    category: 'people',
    headline: 'Prof. Dr. José Garcia',
    line: { text: 'Holds DCB’s professorship for automated insulin therapy, exactly Pumpline’s next step.', evidenceIds: ['ev-dcb-profs-b'] },
    entries: [{ id: 'eB-garcia', name: 'Prof. Dr. José Garcia', role: 'DCB professorship · automatisierte Insulintherapie', institution: 'DCB', unitPath: [...DCB_PATH, 'DCB professorships'], expertise: ['Automated insulin therapy'], evidenceIds: ['ev-dcb-profs-b'] }],
    missingFields: ['Contact details', 'Projects'],
    kind: 'direct',
    selection: 'none',
  },
  {
    id: 'pB-bally',
    category: 'people',
    headline: 'Dr. med. Dr. phil. Lia Bally',
    line: { text: 'Leads the lab working on closed-loop insulin delivery in hospitals.', evidenceIds: ['ev-bally-team', 'ev-bally-aid'] },
    entries: [{ id: 'eB-lbally', name: 'Dr. med. Dr. phil. Lia Bally', role: 'Group Leader, Bally Lab (DBMR)', institution: 'UniBE', unitPath: BALLY_PATH, expertise: ['Automated insulin delivery', 'Digital biomarkers'], evidenceIds: ['ev-bally-team'] }],
    missingFields: ['Contact details'],
    kind: 'direct',
    selection: 'none',
  },
  {
    id: 'rB-closedloop',
    category: 'groups',
    headline: 'Closed-loop insulin delivery research',
    line: { text: 'Bally Lab works on closed-loop automated insulin delivery.', evidenceIds: ['ev-bally-aid'] },
    entries: [{ id: 'eB-bally', name: 'Bally Lab', institution: 'UniBE', unitPath: BALLY_PATH, expertise: ['Closed-loop insulin delivery', 'Hospital setting'], evidenceIds: ['ev-bally-aid'] }],
    missingFields: [],
    kind: 'direct',
    selection: 'none',
  },
  {
    id: 'rB-study',
    category: 'projects',
    headline: 'An active automated-insulin-delivery study',
    line: { text: 'DCB studies therapies used alongside automated insulin delivery.', evidenceIds: ['ev-dcb-aidjunct'] },
    entries: [{ id: 'eB-junct', name: 'AID-JUNCT study', institution: 'DCB', unitPath: [...DCB_PATH, 'Projects'], expertise: ['Automated insulin delivery', 'Adjunctive therapy'], evidenceIds: ['ev-dcb-aidjunct'] }],
    missingFields: ['Project lead', 'Status and results'],
    kind: 'direct',
    selection: 'none',
  },
  {
    id: 'iB-clinical',
    category: 'infrastructure',
    headline: 'Access to clinical research facilities',
    line: { text: 'DCB states it provides access to clinical research facilities for diabetes technology.', evidenceIds: ['ev-dcb-clinical'] },
    entries: [{ id: 'eB-clin', name: 'DCB clinical research access', institution: 'DCB', unitPath: DCB_PATH, expertise: ['Clinical research'], evidenceIds: ['ev-dcb-clinical'] }],
    missingFields: ['Access conditions for companies', 'Costs'],
    kind: 'direct',
    selection: 'none',
  },
  {
    id: 'rB-ai',
    category: 'ideas',
    headline: 'AI for personalised insulin decisions',
    line: { text: 'ARTORG builds AI for adaptive, personalised diabetes care.', evidenceIds: ['ev-adaptive-ai'] },
    entries: [{ id: 'eB-adm', name: 'Adaptive Diabetes Management', institution: 'ARTORG', unitPath: [...AIHN_PATH, 'Adaptive Diabetes Management'], expertise: ['AI for diabetes care'], evidenceIds: ['ev-adaptive-ai'] }],
    missingFields: ['Named contact'],
    kind: 'idea',
    selection: 'none',
  },
];

export const NETWORK_REASON: Reason = {
  id: 'rB-network',
    category: 'groups',
  headline: 'A 61-researcher diabetes-technology network',
  line: { text: '61 researchers work across the four DCB professorships.', evidenceIds: ['ev-dcb-network'] },
  entries: [{ id: 'eB-net', name: 'DCB research professorships', institution: 'DCB', evidenceIds: ['ev-dcb-network'] }],
  kind: 'direct',
  selection: 'none',
};

/** Adds the search path to NETWORK_REASON's evidence after a "clinical" follow-up answer. */
export function withNetworkTrace(trace: SearchTrace): SearchTrace {
  if (trace.links.some((l) => l.target === 'ev-dcb-network')) return trace;
  const from = trace.inputs.find((i) => /clinic|r&d/i.test(i.label)) ?? trace.inputs[0];
  const term = { id: 't-network', label: 'diabetes technology research' };
  return {
    inputs: trace.inputs,
    terms: trace.terms.some((t) => t.id === term.id) ? trace.terms : [...trace.terms, term],
    links: [
      ...trace.links,
      ...(from && !trace.links.some((l) => l.source === from.id && l.target === term.id) ? [{ source: from.id, target: term.id, value: 1 }] : []),
      { source: term.id, target: 'ev-dcb-network', value: 1 },
    ],
  };
}

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
    { source: 't-aid', target: 'ev-dcb-profs-b', value: 1 },
    { source: 't-aid', target: 'ev-bally-team', value: 1 },
    { source: 't-network', target: 'ev-dcb-clinical', value: 1 },
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
    { caseId: 'case-d2', companyLabel: 'InsuTech Labs', score: 72, shared: ['Insulin delivery', 'R&D site'], status: 'closed', outcome: 'visit' },
    { caseId: 'case-d5', companyLabel: 'Kardia Systems', score: 38, shared: ['Diabetes device'], status: 'researching' },
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
      text: 'First draft ready. One question: R&D partner or clinical validation?',
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
    status: 'closed',
    outcome: 'no_interest',
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

// ---------- Smaller seeded cases ----------
// Short briefs built only from the evidence above, so every case opens to
// something real. Kept items are pre-selected to match the board's ✓ counts.

type Mini = [category: Reason['category'], headline: string, line: string, entry: string, institution: Institution, evidence: string[], role?: string];

function miniCase(
  id: string,
  companyLabel: string,
  oneLineNeed: string,
  status: CaseStatus,
  updatedAt: string,
  keep: number,
  facts: string[],
  items: Mini[],
  opts: { outcome?: CaseOutcome; onHold?: boolean } = {},
): CaseDetail {
  const reasons: Reason[] = items.map(([category, headline, line, entry, institution, evidence, role], i) => ({
    id: `${id}-r${i}`,
    category,
    headline,
    line: { text: line, evidenceIds: evidence },
    entries: [{ id: `${id}-e${i}`, name: entry, role, institution, evidenceIds: evidence }],
    kind: category === 'ideas' ? 'idea' : 'direct',
    selection: i < keep ? 'kept' : 'none',
  }));
  const evIds = [...reasonEvidence(reasons)];
  const revId = `${id}-rev1`;
  return {
    case: { id, companyLabel, oneLineNeed, status, ...opts, createdAt: updatedAt, updatedAt, keptCount: Math.min(keep, reasons.length) },
    revisions: [
      reasons.length
        ? {
            id: revId,
            version: 1,
            createdAt: updatedAt,
            changeNote: 'First version',
            changedReasonIds: [],
            company: { summary: oneLineNeed + '.', facts },
            reasons,
            openQuestions: [],
            trace: {
              inputs: [{ id: 'in-1', label: oneLineNeed.toLowerCase().split(/[:,]/)[0] }],
              terms: [{ id: 't-1', label: facts[1]?.toLowerCase() ?? 'diabetes technology' }],
              links: [{ source: 'in-1', target: 't-1', value: evIds.length }, ...evIds.map((e) => ({ source: 't-1', target: e, value: 1 }))],
            },
            coverage: coverage('ok'),
          }
        : emptyRevision(revId, 'no_match', 'No reliable match for this topic in the indexed UniBE, ARTORG and DCB pages.'),
    ],
    currentRevisionId: revId,
    turns: [{ id: `${id}-t1`, role: 'operator', text: `${companyLabel}: ${oneLineNeed}.`, createdAt: updatedAt }],
    evidence: EVIDENCE,
  };
}

const W: Mini = ['people', 'Prof. Dr. Lilian Witthauer', 'Holds DCB’s sensor-technology professorship.', 'Prof. Dr. Lilian Witthauer', 'DCB', ['ev-dcb-profs-a'], 'DCB professorship · Sensortechnologie'];
const K: Mini = ['people', 'Prof. Dr. Lisa Koch', 'Holds DCB’s data-science and machine-learning professorship.', 'Prof. Dr. Lisa Koch', 'DCB', ['ev-dcb-profs-a'], 'DCB professorship · Data Science und Machine Learning'];
const G: Mini = ['people', 'Prof. Dr. José Garcia', 'Holds DCB’s professorship for automated insulin therapy.', 'Prof. Dr. José Garcia', 'DCB', ['ev-dcb-profs-b'], 'DCB professorship · automatisierte Insulintherapie'];

export const SEED_CASES: CaseDetail[] = [
  caseB,
  caseC,
  miniCase('case-d1', 'NordSense', 'Sweat-based metabolite sensing', 'pitch_sent', '2026-10-15T09:30:00Z', 2, ['Medtech', 'metabolite sensing'], [
    W,
    ['ideas', 'Sensing several metabolites at once', 'Early-stage DCB chemistry for continuous multi-metabolite measurement.', 'Illuminating Personalized Medicine', 'DCB', ['ev-dcb-porphyrin']],
    ['projects', 'Needle-free monitoring research', 'DCB runs a pilot study on painless, needle-free monitoring.', 'SPN-005 pilot study', 'DCB', ['ev-dcb-spn005']],
  ]),
  miniCase('case-d2', 'InsuTech Labs', 'Insulin delivery research partners', 'closed', '2026-10-02T16:10:00Z', 2, ['Medtech', 'insulin delivery'], [
    G,
    ['projects', 'An active automated-insulin-delivery study', 'DCB studies therapies used alongside automated insulin delivery.', 'AID-JUNCT study', 'DCB', ['ev-dcb-aidjunct']],
    ['groups', 'Closed-loop insulin delivery research', 'Bally Lab works on closed-loop automated insulin delivery.', 'Bally Lab', 'UniBE', ['ev-bally-aid']],
  ], { outcome: 'visit' }),
  miniCase('case-d3', 'Diabeto App', 'Clinical evidence for a coaching app', 'researching', '2026-09-28T11:00:00Z', 1, ['Digital health', 'personalised diabetes care'], [
    K,
    ['groups', 'AI for personalised diabetes care', 'ARTORG builds AI for adaptive, personalised diabetes care.', 'Adaptive Diabetes Management', 'ARTORG', ['ev-adaptive-ai']],
  ], { onHold: true }),
  miniCase('case-d4', 'MedPatch', 'Adhesive wearable patches', 'pitch_sent', '2026-10-11T14:45:00Z', 2, ['Medtech', 'wearable sensing'], [
    W,
    ['groups', 'Experts who validate digital biomarkers', 'Bally Lab develops and evaluates new digital biomarkers.', 'Bally Lab', 'UniBE', ['ev-bally-biomarkers']],
    ['projects', 'Glucose and movement during sleep', 'DCB studies how glucose values relate to motion during sleep.', 'Moonwalk Project', 'DCB', ['ev-dcb-moonwalk']],
  ]),
  miniCase('case-d5', 'Kardia Systems', 'Remote monitoring: diabetes add-on', 'researching', '2026-10-17T08:20:00Z', 0, ['Digital health', 'remote monitoring'], [
    ['groups', 'AI for personalised diabetes care', 'ARTORG builds AI for adaptive, personalised diabetes care.', 'Adaptive Diabetes Management', 'ARTORG', ['ev-adaptive-ai']],
    ['projects', 'Glucose and movement during sleep', 'DCB studies how glucose values relate to motion during sleep.', 'Moonwalk Project', 'DCB', ['ev-dcb-moonwalk']],
  ]),
  miniCase('case-d6', 'Alpine Bioprint', 'Tissue models', 'closed', '2026-09-20T10:00:00Z', 0, ['Biotech'], [], { outcome: 'no_interest' }),
];
