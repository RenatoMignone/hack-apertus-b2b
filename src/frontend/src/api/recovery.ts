import type { CaseDetail } from '../types/contract';

const messages: Record<string, string> = {
  authentication_required: 'Your access token was rejected. Disconnect and reconnect with a valid token.',
  service_unavailable: 'A required backend service is unavailable. Check the worker and server configuration.',
  storage_unavailable: 'The database or artifact store is unavailable.',
  stale_revision: 'This case changed. Reload it before trying again.',
  conflict: 'The case changed or this action is not allowed in its current state. Reload and try again.',
  invalid_model_output: 'The model could not produce a valid result. Retry the failed step.',
  evidence_rejected: 'The evidence or draft failed validation. No unsupported report was published.',
  budget_exceeded: 'The run budget expired. Retry the report if evidence is ready, or start research again.',
};

export function failureMessage(code?: string): string {
  return code && messages[code] || 'The request could not be completed. Please try again.';
}

export function canReusePack(detail: Pick<CaseDetail, 'currentRun' | 'inputId'>): boolean {
  const run = detail.currentRun;
  return run?.status === 'failed' && !!run.pack_id && run.input_id === detail.inputId;
}
