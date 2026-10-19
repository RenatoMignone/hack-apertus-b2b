import type { NavigatorApi } from './index';
import type { ActionItem, BriefRevision, CaseDetail, CaseRun, CaseSummary, RunStage } from '../types/contract';

/** Backend resources retained even though their old standalone screens were removed. */
interface HttpNavigatorApi extends NavigatorApi {
  getLastOpened(): Promise<CaseSummary | null>;
  listActionItems(): Promise<ActionItem[]>;
  setActionStatus(id: string, status: ActionItem['status'], answer?: string): Promise<ActionItem[]>;
  addActionItem(caseId: string, question: string, askRole: string): Promise<ActionItem[]>;
}

type Fetch = typeof fetch;
type Accepted = { case_id: string; input_id: string; run_id?: string; status_url?: string };
type Operation = { status: string; download_url?: string; error_code?: string };
const messages: Record<string, string> = {
  authentication_required: 'Your access token was rejected. Disconnect and reconnect with a valid token.',
  service_unavailable: 'A required backend service is unavailable. Check the worker and server configuration.',
  storage_unavailable: 'The database or artifact store is unavailable.',
  stale_revision: 'This case changed. Reload it before trying again.',
  conflict: 'The case changed or this action is not allowed in its current state. Reload and try again.',
  invalid_model_output: 'The model could not produce a valid result. You can retry the research.',
  evidence_rejected: 'The evidence or draft failed validation. No unsupported report was published.',
  budget_exceeded: 'The research budget expired. You can start a new run.',
};

export class ApiError extends Error {
  status: number;
  code: string;
  constructor(status: number, code: string) {
    super(messages[code] ?? 'The request could not be completed. Please try again.');
    this.status = status;
    this.code = code;
  }
}

export function createHttpApi({ baseUrl = '', token, fetcher = fetch,
  pause = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms)),
  pollInterval = 1200, maxPolls = 750,
}: { baseUrl?: string; token: () => string; fetcher?: Fetch; pause?: (ms: number) => Promise<void>;
  pollInterval?: number; maxPolls?: number }): HttpNavigatorApi {
  const listeners = new Set<() => void>();
  let lastOpened: string | undefined;
  const base = baseUrl.replace(/\/$/, '');
  const emit = () => listeners.forEach((listener) => listener());
  const path = (id: string) => `/api/v1/cases/${encodeURIComponent(id)}`;
  const current = (detail: CaseDetail): BriefRevision => {
    const result = detail.revisions.find((r) => r.id === detail.currentRevisionId);
    if (!result?.resultHash) throw new Error('No current report is ready.');
    return result;
  };

  async function request<T>(url: string, method = 'GET', body?: unknown, blob = false): Promise<T> {
    // Server-returned paths stay on the configured API origin, including downloads.
    if (!url.startsWith('/api/v1/') || url.includes('://') || url.includes('\\')) throw new Error('Invalid API path.');
    const credential = token();
    if (!credential) throw new ApiError(401, 'authentication_required');
    const headers: Record<string, string> = { Authorization: `Bearer ${credential}` };
    if (method !== 'GET') headers['Idempotency-Key'] = crypto.randomUUID();
    if (body !== undefined) headers['Content-Type'] = 'application/json';
    // Retry transport failures once with the SAME idempotency key; never retry a conflict.
    for (let attempt = 0; attempt < 2; attempt++) {
      const controller = new AbortController();
      // Live-corpus capture can exceed a short read timeout. Mutations retain
      // their idempotency key if a lost response requires a transport retry.
      const timeout = setTimeout(() => controller.abort(), method === 'GET' ? 30000 : 120000);
      try {
        const response = await fetcher(base + url, { method, headers, credentials: 'omit',
          redirect: 'error', cache: 'no-store', signal: controller.signal,
          body: body === undefined ? undefined : JSON.stringify(body) });
        if (!response.ok) {
          const payload = await response.json().catch(() => ({}));
          throw new ApiError(response.status, payload.error?.code ?? 'service_unavailable');
        }
        return (blob ? await response.blob() : await response.json()) as T;
      } catch (error) {
        if (error instanceof ApiError) throw error;
        if (attempt) throw new Error('Cannot reach the backend. Check your connection and reload; submitted work may still be running.');
        await pause(300);
      } finally { clearTimeout(timeout); }
    }
    throw new Error('Cannot reach the backend.');
  }

  async function getCase(id: string): Promise<CaseDetail | null> {
    try {
      const detail = await request<CaseDetail>(path(id));
      lastOpened = id;
      return detail;
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) return null;
      throw error;
    }
  }
  async function requireCase(id: string) {
    const detail = await getCase(id);
    if (!detail || detail.revision === undefined || !detail.inputId) throw new Error('Case is unavailable.');
    return detail;
  }
  async function poll(caseId: string, url: string, onStage: (stage: RunStage) => void) {
    for (let n = 0; n < maxPolls; n++) {
      const run = await request<CaseRun>(url);
      if (run.stage) onStage(run.stage);
      if (run.status === 'succeeded' || run.status === 'waiting_for_input') {
        onStage('done'); emit();
        return requireCase(caseId);
      }
      if (['failed', 'cancelled', 'superseded'].includes(run.status)) {
        emit();
        throw new ApiError(409, run.error_code ?? 'conflict');
      }
      await pause(pollInterval);
    }
    throw new Error('Research is still running. Reopen this case to resume progress updates.');
  }
  async function patch(caseId: string, values: object) {
    const detail = await requireCase(caseId);
    await request(path(caseId), 'PATCH', { expected_revision: detail.revision, ...values });
    emit(); return requireCase(caseId);
  }
  const api: HttpNavigatorApi = {
    async listCases() {
      const cases: CaseSummary[] = [];
      for (let offset = 0; offset < 10000; offset += 100) {
        const page = await request<CaseSummary[]>(`/api/v1/cases?limit=100&offset=${offset}`);
        cases.push(...page);
        if (page.length < 100) break;
      }
      return cases.sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
    },
    getCase,
    async getLastOpened() { return lastOpened ? (await getCase(lastOpened))?.case ?? null : null; },
    async createCase(prompt) {
      const created = await request<Accepted>('/api/v1/cases', 'POST', { prompt, run: true });
      emit(); return requireCase(created.case_id);
    },
    async runCase(caseId, onStage) {
      const detail = await requireCase(caseId);
      const run = detail.currentRun;
      if (run && ['queued', 'running', 'waiting_for_input'].includes(run.status)) {
        return poll(caseId, `${path(caseId)}/runs/${run.run_id}`, onStage);
      }
      if (run?.status === 'failed' && run.pack_id && run.input_id === detail.inputId) {
        const started = await request<Accepted>(`${path(caseId)}/reports`, 'POST', {
          pack_id: run.pack_id, expected_revision: detail.revision,
          instruction: 'Create a concise cited draft from the existing evidence pack. Preserve caveats and avoid unsupported implications.',
        });
        if (!started.status_url) throw new Error('The server did not return a report run.');
        return poll(caseId, started.status_url, onStage);
      }
      const started = await request<Accepted>(`${path(caseId)}/runs`, 'POST', { input_id: detail.inputId });
      if (!started.status_url) throw new Error('The server did not return a run.');
      return poll(caseId, started.status_url, onStage);
    },
    async sendMessage(caseId, text, onStage, kind = 'focus') {
      const detail = await requireCase(caseId);
      if (detail.currentRun?.status === 'waiting_for_input') throw new Error('Answer the clarification question before sending a new request.');
      const started = await request<Accepted>(`${path(caseId)}/messages`, 'POST', {
        text, kind, expected_revision: detail.revision });
      if (!started.status_url) throw new Error('The server did not return a run.');
      return poll(caseId, started.status_url, onStage);
    },
    async answerFollowUp(caseId, turnId, answer, onStage) {
      const detail = await requireCase(caseId);
      const question = detail.turns.find((turn) => turn.id === turnId)?.followUp;
      if (!detail.currentRun || !question) throw new Error('This clarification is no longer available.');
      const accepted = await request<Accepted>(`${path(caseId)}/runs/${detail.currentRun.run_id}/answers`, 'POST', {
        input_id: detail.inputId, question_id: question.id, answer });
      if (!accepted.status_url) throw new Error('The server did not return a run.');
      return poll(caseId, accepted.status_url, onStage);
    },
    async setSelection(caseId, reasonId, selection, expected) {
      const detail = await requireCase(caseId), result = current(detail);
      if (!expected || expected.resultId !== result.id || expected.resultHash !== result.resultHash) {
        throw new ApiError(409, 'stale_revision');
      }
      await request(`${path(caseId)}/reports/${result.id}/reasons/${encodeURIComponent(reasonId)}/selection`, 'PUT',
        { selection, expected_result_hash: result.resultHash });
      emit(); return requireCase(caseId);
    },
    setStatus: (caseId, status) => patch(caseId, { status }),
    setCurrentRevision: (caseId, revisionId) => patch(caseId, { current_revision_id: revisionId }),
    setCaseFlags: (caseId, flags) => patch(caseId, {
      ...('onHold' in flags ? { on_hold: flags.onHold ?? false } : {}),
      ...('outcome' in flags ? { outcome: flags.outcome ?? null } : {}),
    }),
    async exportDeck(caseId, expected) {
      const detail = await requireCase(caseId), result = current(detail);
      if (!expected || expected.resultId !== result.id || expected.resultHash !== result.resultHash) {
        throw new ApiError(409, 'stale_revision');
      }
      if (!detail.selectionHash || !result.reasons.length || result.reasons.some((r) => r.selection === 'none')
          || !result.reasons.some((r) => r.selection === 'kept')) {
        throw new Error('Review every reason and keep at least one before exporting.');
      }
      const report = `${path(caseId)}/reports/${result.id}`;
      const review = await request<{ review_id: string }>(`${report}/reviews`, 'POST', { decision: 'accepted',
        expected_result_hash: result.resultHash, expected_selection_hash: detail.selectionHash });
      const queued = await request<{ status_url: string }>(`${path(caseId)}/exports`, 'POST', {
        result_id: result.id, review_id: review.review_id, expected_result_hash: result.resultHash,
        expected_selection_hash: detail.selectionHash, format: 'pdf' });
      for (let n = 0; n < maxPolls; n++) {
        const operation = await request<Operation>(queued.status_url);
        if (operation.status === 'failed') throw new ApiError(409, operation.error_code ?? 'service_unavailable');
        if (operation.status === 'committed' && operation.download_url) {
          const blob = await request<Blob>(operation.download_url, 'GET', undefined, true);
          if (!blob.type.startsWith('application/pdf')) throw new Error('The server did not return a PDF.');
          return { filename: `bern-report-${result.id}.pdf`, blob };
        }
        await pause(pollInterval);
      }
      throw new Error('PDF rendering is still pending. Try exporting again shortly.');
    },
    async listActionItems() { return request<ActionItem[]>('/api/v1/action-items'); },
    async setActionStatus(id, status, answer) {
      await request(`/api/v1/action-items/${encodeURIComponent(id)}`, 'PATCH', { status, ...(answer !== undefined ? { answer } : {}) });
      emit(); return api.listActionItems();
    },
    async addActionItem(caseId, question, askRole) {
      await request('/api/v1/action-items', 'POST', { case_id: caseId, question, ask_role: askRole });
      emit(); return api.listActionItems();
    },
    async resetDemo() { throw new Error('Demo reset is unavailable in HTTP mode.'); },
    subscribe(listener) { listeners.add(listener); return () => listeners.delete(listener); },
  };
  return api;
}
