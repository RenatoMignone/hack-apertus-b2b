import { type ReactNode, useEffect, useState } from 'react';
import { Callout, Card, Spinner, TextField } from '@radix-ui/themes';
import { apiBaseUrl, apiMode } from '../api';
import { accessToken, setAccessToken, setCapabilities } from '../api/session';
import { Button } from './ui';

export default function ConnectionGate({ children }: { children: ReactNode }) {
  const [connected, setConnected] = useState(false);
  const [checking, setChecking] = useState(apiMode !== 'mock');
  const [value, setValue] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function probe(token: string, signal?: AbortSignal) {
    const response = await fetch(apiBaseUrl.replace(/\/$/, '') + '/api/v1/capabilities', {
      headers: token ? { Authorization: `Bearer ${token}` } : {}, credentials: 'omit', redirect: 'error',
      signal: signal ?? AbortSignal.timeout(15000), cache: 'no-store' });
    if (response.status === 401) return false;
    if (!response.ok) throw new Error('Backend unavailable. Check the API, SSH tunnel and runtime configuration.');
    const data = await response.json();
    setCapabilities(data);
    return true;
  }
  useEffect(() => {
    if (apiMode === 'mock') return;
    let alive = true;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    void probe(accessToken(), controller.signal).then((ok) => { if (alive) setConnected(ok); })
      .catch((reason) => { if (alive) setError(reason instanceof Error ? reason.message : 'Cannot reach the backend.'); })
      .finally(() => { if (alive) setChecking(false); });
    return () => { alive = false; clearTimeout(timeout); controller.abort(); };
  }, []);
  if (apiMode === 'mock' || connected) return children;
  const connect = async () => {
    if (busy) return;
    setBusy(true); setError('');
    try {
      const ok = await probe(value.trim());
      if (!ok) throw new Error('This server requires a personal access token.');
      setAccessToken(value.trim()); setValue(''); setConnected(true);
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Cannot reach the backend.'); }
    finally { setBusy(false); }
  };
  return <main className="flex min-h-full items-center justify-center bg-canvas p-6">
    <Card size="4" className="w-full max-w-md">
      <h1 className="text-2xl font-semibold tracking-tight">Bern Navigator</h1>
      {checking ? <div role="status" className="mt-5 flex items-center gap-3 text-muted"><Spinner /> Connecting to your workspace…</div> :
      <form onSubmit={(event) => { event.preventDefault(); void connect(); }}>
        <p className="mt-3 text-sm text-muted">Local testing connects automatically. A shared server may require your personal token.</p>
        <label className="mt-5 mb-2 block text-sm font-medium" htmlFor="access-token">Access token (shared server only)</label>
        <TextField.Root id="access-token" type="password" autoComplete="off" value={value} onChange={(event) => setValue(event.target.value)} />
        {error && <Callout.Root color="red" mt="4"><Callout.Text>{error}</Callout.Text></Callout.Root>}
        <div className="mt-5"><Button variant="primary" type="submit" disabled={busy}>{busy ? 'Connecting…' : 'Connect / retry'}</Button></div>
      </form>}
    </Card>
  </main>;
}
