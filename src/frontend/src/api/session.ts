// Operator access token only. Provider/database credentials never enter this app.
// Deliberately memory-only: refresh requires reconnecting, server jobs keep running.
let token = '';
let required = false, version = 0;
const listeners = new Set<() => void>();
export const authenticationRequired = () => required;
export const sessionVersion = () => version;
export function subscribeSession(listener: () => void) { listeners.add(listener); return () => { listeners.delete(listener); }; }
export function rejectAccess() { if (!required) { required = true; listeners.forEach(listener => listener()); } }
let formats: string[] = [];
export const accessToken = () => token;
export const serverFormats = () => [...formats];
export const setAccessToken = (value: string) => { token = value; required = false; version++; if (!value) formats = []; listeners.forEach(listener => listener()); };
export function setCapabilities(value: unknown) {
  const data = value as { schema_version?: string; frontend_transport?: string; formats?: unknown };
  if (!data || data.schema_version !== '1' || data.frontend_transport !== 'polling' ||
      !Array.isArray(data.formats) || !data.formats.every((format) => typeof format === 'string')) {
    throw new Error('This backend does not expose the supported Navigator API.');
  }
  formats = [...data.formats];
}
