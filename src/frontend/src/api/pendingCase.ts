import type { CaseDetail } from '../types/contract';

// In memory only: no company prompt in the URL, browser storage or history.
const pending = new Map<string, { promise: Promise<CaseDetail>; prompt: string }>();
export function beginCase(prompt: string, create: (text: string) => Promise<CaseDetail>) {
  const id = crypto.randomUUID();
  const promise = Promise.resolve().then(() => create(prompt));
  void promise.catch(() => {}); // Route attaches its own error handler after navigation.
  pending.set(id, { promise, prompt });
  return id;
}
export const pendingCase = (id: string) => pending.get(id);
export const forgetPendingCase = (id: string) => { pending.delete(id); };
