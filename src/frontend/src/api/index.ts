import type { BusinessContext, CaseOutcome, CaseDetail, CaseStatus, CaseSummary, RunStage, Selection } from '../types/contract';
import { mockApi } from './mockApi';
import { createHttpApi } from './httpApi';
import { accessToken } from './session';

export type ReportExpectation = { resultId: string; resultHash: string };
/** Browser transport; HTTP is the default, mock mode is an explicit demo choice. */
export interface NavigatorApi {
  listCases(): Promise<CaseSummary[]>;
  getCase(id: string): Promise<CaseDetail | null>;
  /** Creates a case from the operator's first message and runs the research. */
  createCase(prompt: string): Promise<CaseDetail>;
  runCase(caseId: string, onStage: (s: RunStage) => void, signal?: AbortSignal): Promise<CaseDetail>;
  sendMessage(caseId: string, text: string, onStage: (s: RunStage) => void, kind?: 'focus' | 'formatting'): Promise<CaseDetail>;
  answerFollowUp(caseId: string, turnId: string, answer: string, onStage: (s: RunStage) => void): Promise<CaseDetail>;
  setSelection(caseId: string, reasonId: string, selection: Selection, expected?: ReportExpectation): Promise<CaseDetail>;
  setCaseMemory?(caseId: string, eligible: boolean, expected?: ReportExpectation): Promise<CaseDetail>;
  setBusinessContext?(caseId: string, values: BusinessContext, onStage: (s: RunStage) => void, expectedRevision?: number): Promise<CaseDetail>;
  setStatus(caseId: string, status: CaseStatus): Promise<CaseDetail>;
  setCurrentRevision(caseId: string, revisionId: string): Promise<CaseDetail>;
  exportDeck(caseId: string, expected?: ReportExpectation, format?: 'pdf' | 'pptx'): Promise<{ filename: string; blob: Blob }>;
  /** Put a case on hold / take it off hold, or record the outcome of a closed case. */
  setCaseFlags(caseId: string, flags: { onHold?: boolean; outcome?: CaseOutcome }): Promise<CaseDetail>;
  /** Mock only: restore the seeded demo data. */
  resetDemo(): Promise<void>;
  /** Called after any change, so pages and the sidebar can refresh. Returns an unsubscribe function. */
  subscribe(listener: () => void): () => void;
}

export const apiMode = import.meta.env.VITE_API_MODE === 'mock' ? 'mock' : 'http';
export const apiBaseUrl: string = import.meta.env.VITE_API_BASE_URL ?? '';
export const api: NavigatorApi = apiMode === 'mock' ? mockApi : createHttpApi({ baseUrl: apiBaseUrl, token: accessToken });
