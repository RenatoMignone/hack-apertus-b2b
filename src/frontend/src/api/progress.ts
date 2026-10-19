import type { CaseRun } from '../types/contract';

const runs = new Map<string, CaseRun>();
const listeners = new Set<() => void>();
export const runProgress = (id: string) => runs.get(id);
export function publishProgress(id: string, value: CaseRun) {
  runs.set(id, value);
  listeners.forEach((listener) => listener());
}
export function subscribeProgress(listener: () => void) {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}
/** Slow unchanged-state polling, reset immediately on actual progress. */
export function nextPollDelay(base: number, unchanged: number) {
  return Math.min(5000, base * (1 + unchanged * 0.5));
}
