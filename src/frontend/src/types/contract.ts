// Frontend ↔ backend data contract. The mock API serves these shapes from
// fixtures; the real backend should return the same shapes.
// Output design (D10): a short list of reasons why Bern fits the company, each
// backed by Bern entries and their source passages, plus a search trace
// (message → ontology terms → source entries) shown as a Sankey.

/** Board stage. "On hold" is a separate flag; a closed case carries an outcome. */
export type CaseStatus = 'researching' | 'in_review' | 'pitch_sent' | 'closed';
export type CaseOutcome = 'visit' | 'no_interest';

export type Institution = 'UniBE' | 'ARTORG' | 'DCB' | 'Other';
export type Selection = 'kept' | 'rejected' | 'none';

export interface CaseSummary {
  id: string;
  companyLabel: string;
  oneLineNeed: string;
  status: CaseStatus;
  /** Set when status is "closed". */
  outcome?: CaseOutcome;
  onHold?: boolean;
  createdAt: string;
  updatedAt: string;
  keptCount: number;
}

/** One entry extracted from a public URL. Every statement cites one or more of these. */
export interface Evidence {
  id: string;
  /** Stable citation number shown as [n]. */
  n: number;
  /** Short entry name, e.g. "SPN-005 pilot study". */
  label: string;
  url: string;
  title: string;
  institution: Institution;
  fetchedAt: string;
  sourceDate?: string;
  /** Literal passage from the page. */
  excerpt: string;
  /** Part of the excerpt that carries the claim. */
  highlight?: string;
  /** One line: why this matters for the company. */
  relevance: string;
  origin?: 'corpus' | 'web';
  reviewStatus?: 'curated' | 'unreviewed';
}

export interface CitedText {
  text: string;
  evidenceIds: string[];
}

/** A Bern unit, project or person backing a reason. */
export interface ReasonEntry {
  id: string;
  name: string;
  /** Role or function exactly as the source states it (people only). */
  role?: string;
  institution: Institution;
  /** Organisational hierarchy, top-down, e.g. ["University of Bern", "DBMR", "Bally Lab"]. */
  unitPath?: string[];
  /** Fields of expertise stated by the sources (short tags). */
  expertise?: string[];
  evidenceIds: string[];
}

/** How "Why Bern" elements are grouped in the UI. */
export type ReasonCategory = 'people' | 'groups' | 'projects' | 'infrastructure' | 'ideas';

/** One clear way in which Bern is good for this company. */
export interface Reason {
  id: string;
  /**
   * people: an expert (headline = name, entries[0] = the person);
   * groups: labs, units, centres; projects: projects and studies;
   * infrastructure: facilities and services; ideas: possible adjacent applications.
   */
  category: ReasonCategory;
  headline: string;
  line: CitedText;
  entries: ReasonEntry[];
  /** "idea" = possible adjacent application that needs expert validation. */
  kind: 'direct' | 'idea';
  /** Set when the reason confirms a lead the operator suggested. */
  fromLead?: boolean;
  /**
   * Required result fields (challenge success criterion 4) that the sources do
   * not state, e.g. "Named contact", "Projects". Shown as "Not stated in sources".
   */
  missingFields?: string[];
  selection: Selection;
}

/** Search trace for the Sankey: message phrases → ontology terms → source entries (evidence ids). */
export interface SearchTrace {
  inputs: { id: string; label: string }[];
  terms: { id: string; label: string }[];
  /** term → evidence links; input → term links. */
  links: { source: string; target: string; value: number }[];
}

/**
 * A past case that resembles the current one. `score` (0–100) measures how
 * similar the company needs and matched topics are. It is not a probability
 * of success (see case_similarity_score in OPERATIONS_PLAN.md).
 */
export interface SimilarCase {
  caseId: string;
  companyLabel: string;
  score: number;
  /** What the two cases have in common, e.g. "Wearable sensing". */
  shared: string[];
  status: CaseStatus;
  outcome?: CaseOutcome;
}

export interface Coverage {
  snapshotDate: string;
  institutions: Institution[];
  /** Short notes, e.g. "No named contacts on the retrieved pages." */
  limitations: string[];
  resultKind: 'ok' | 'partial' | 'no_match' | 'out_of_scope' | 'source_failure';
}

export interface BriefRevision {
  id: string;
  version: number;
  parentId?: string;
  createdAt: string;
  changeNote: string;
  /** Reasons added or changed in this version (highlighted in the UI). */
  changedReasonIds: string[];
  /** Short description of the company, derived from the operator's message. */
  company?: { summary: string; facts: string[] };
  reasons: Reason[];
  openQuestions: string[];
  /** Earlier agency cases that resemble this one, best first. Empty when none qualify. */
  similarCases?: SimilarCase[];
  trace: SearchTrace;
  coverage: Coverage;
  /** Shown instead of reasons for no_match / out_of_scope. */
  emptyMessage?: string;
  resultHash?: string;
  packId?: string;
  packHash?: string;
}

export interface FollowUpQuestion {
  id: string;
  question: string;
  choices: string[];
  answer?: string;
}

export interface DialogueTurn {
  id: string;
  role: 'operator' | 'agent';
  text: string;
  createdAt: string;
  revisionId?: string;
  followUp?: FollowUpQuestion;
}

export interface CaseDetail {
  case: CaseSummary;
  revisions: BriefRevision[];
  currentRevisionId?: string;
  turns: DialogueTurn[];
  evidence: Record<string, Evidence>;
  revision?: number;
  inputId?: string;
  selectionHash?: string;
  currentRun?: CaseRun;
}

export interface CaseRun {
  run_id: string;
  input_id: string;
  status: 'queued' | 'running' | 'waiting_for_input' | 'succeeded' | 'failed' | 'cancelled' | 'superseded';
  stage?: RunStage;
  error_code?: string;
}

export type RunStage = 'interpreting' | 'searching' | 'validating' | 'drafting' | 'done';

/** Retained HTTP action-item resource; no standalone action screen. */
export interface ActionItem {
  id: string;
  caseId: string;
  question: string;
  /** Colleague role to ask, e.g. "Account owner". */
  askRole: string;
  status: 'open' | 'asked' | 'done';
  /** Optional note with the colleague's answer. */
  answer?: string;
}
