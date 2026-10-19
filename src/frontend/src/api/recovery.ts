import type { CaseDetail } from '../types/contract';

const messages: Record<string, string> = {
  authentication_required: 'Your access token was rejected. Reconnect with a valid token.',
  service_unavailable: 'A required backend service is unavailable. Check the worker and server configuration.',
  storage_unavailable: 'The database or artifact store is unavailable.',
  stale_revision: 'This case changed. Reload it before trying again.',
  conflict: 'The case changed or this action is not allowed in its current state. Reload and try again.',
  invalid_model_output: 'The model could not produce a valid result. Retry the failed step.',
  evidence_rejected: 'The evidence or draft failed validation. No unsupported report was published.',
  budget_exceeded: 'The run budget expired. Retry the report if evidence is ready, or start research again.',
};

export function failureMessage(code?: string): string {
  return code && Object.prototype.hasOwnProperty.call(messages, code) ? messages[code] : 'The request could not be completed. Please try again.';
}

export function canReusePack(detail: Pick<CaseDetail, 'currentRun' | 'inputId'>): boolean {
  const run = detail.currentRun;
  return run?.status === 'failed' && !!run.pack_id && run.input_id === detail.inputId;
}

/** A failed run may also use HTTP 409; only revision/state conflicts refresh editing context. */
export function isStateConflict(error: unknown): boolean {
  if (!error || typeof error !== 'object') return false;
  const value = error as {status?: number; code?: string};
  return value.status === 409 && ['stale_revision', 'conflict'].includes(value.code ?? '');
}

export function recoveryAction(detail: Pick<CaseDetail, 'currentRun' | 'inputId'>) {
  const status = detail.currentRun?.status;
  if (status === 'queued' || status === 'running') return 'observe';
  if (status === 'waiting_for_input') return 'clarify';
  if (status === 'failed') return canReusePack(detail) ? 'report' : 'research';
  return 'reload';
}
