export type ObservationStatus = 'connected' | 'reconnecting' | 'disconnected' | 'authentication_required';
const states = new Map<string, ObservationStatus>();
const listeners = new Set<() => void>();
export const observationStatus = (id: string) => states.get(id) ?? 'connected';
export function publishObservation(id: string, status: ObservationStatus) {
  if (states.get(id) === status) return;
  states.set(id, status); listeners.forEach(listener => listener());
}
export function subscribeObservation(listener: () => void) {
  listeners.add(listener); return () => { listeners.delete(listener); };
}
