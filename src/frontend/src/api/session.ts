// Operator access token only. Provider/database credentials never enter this app.
// Deliberately memory-only: refresh requires reconnecting, server jobs keep running.
let token = '';
let formats: string[] = [];
export const accessToken = () => token;
export const serverFormats = () => [...formats];
export const setAccessToken = (value: string) => { token = value; if (!value) formats = []; };
export function setCapabilities(value: unknown) {
  const data = value as { schema_version?: string; frontend_transport?: string; formats?: unknown };
  if (!data || data.schema_version !== '1' || data.frontend_transport !== 'polling' ||
      !Array.isArray(data.formats) || !data.formats.every((format) => typeof format === 'string')) {
    throw new Error('This backend does not expose the supported Navigator API.');
  }
  formats = [...data.formats];
}
