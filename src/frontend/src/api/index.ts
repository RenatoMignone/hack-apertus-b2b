import type { ActionItem, CaseDetail, CaseStatus, CaseSummary, RunStage, Selection } from '../types/contract';
import { mockApi } from './mockApi';

/** Everything the UI needs from the backend. Swap mockApi for an HTTP client when the brain is ready. */
export interface NavigatorApi {
  listCases(): Promise<CaseSummary[]>;
  getCase(id: string): Promise<CaseDetail | null>;
  /** Creates a case from the operator's first message and runs the research. */
  createCase(prompt: string): Promise<CaseDetail>;
  runCase(caseId: string, onStage: (s: RunStage) => void): Promise<CaseDetail>;
  sendMessage(caseId: string, text: string, onStage: (s: RunStage) => void): Promise<CaseDetail>;
  answerFollowUp(caseId: string, turnId: string, answer: string, onStage: (s: RunStage) => void): Promise<CaseDetail>;
  setSelection(caseId: string, reasonId: string, selection: Selection): Promise<CaseDetail>;
  setStatus(caseId: string, status: CaseStatus): Promise<CaseDetail>;
  setCurrentRevision(caseId: string, revisionId: string): Promise<CaseDetail>;
  exportDeck(caseId: string): Promise<{ filename: string; blob: Blob }>;
  listActionItems(): Promise<ActionItem[]>;
  setActionStatus(id: string, status: ActionItem['status']): Promise<ActionItem[]>;
  /** Called after any change, so pages and the sidebar can refresh. Returns an unsubscribe function. */
  subscribe(listener: () => void): () => void;
}

export const api: NavigatorApi = mockApi;
