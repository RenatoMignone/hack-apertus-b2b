import { type ReactNode, useState } from 'react';
import { apiBaseUrl, apiMode } from '../api';
import { accessToken, setAccessToken, setCapabilities } from '../api/session';
import { Button } from './ui';

export default function ConnectionGate({ children }: { children: ReactNode }) {
  const [connected, setConnected] = useState(Boolean(accessToken()));
  const [value, setValue] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  if (apiMode === 'mock') return children;
  const connect = async () => {
    if (!value.trim() || busy) return;
    setBusy(true); setError('');
    try {
      const response = await fetch(apiBaseUrl.replace(/\/$/, '') + '/api/v1/capabilities', {
        headers: { Authorization: `Bearer ${value.trim()}` }, credentials: 'omit', redirect: 'error',
        signal: AbortSignal.timeout(15000), cache: 'no-store' });
      if (!response.ok) throw new Error(response.status === 401 ? 'Access token rejected.' : 'Backend unavailable. Check its configuration and database connection.');
      setCapabilities(await response.json());
      setAccessToken(value.trim()); setValue(''); setConnected(true);
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Cannot reach the backend.'); }
    finally { setBusy(false); }
  };
  if (connected) return <>
    {children}
    <button className="fixed bottom-2 left-2 z-40 rounded border border-line bg-white px-2 py-1 text-xs text-muted"
      onClick={() => { setAccessToken(''); setConnected(false); }}>Disconnect</button>
  </>;
  return <main className="flex h-full items-center justify-center bg-canvas p-6">
    <form className="w-full max-w-md rounded-2xl border border-line bg-white p-6 shadow-sm"
      onSubmit={(event) => { event.preventDefault(); void connect(); }}>
      <h1 className="text-xl font-semibold">Connect to Bern Navigator</h1>
      <p className="mt-2 text-sm text-muted">Enter the personal access token supplied by your backend administrator.</p>
      <label className="mt-5 block text-sm font-medium" htmlFor="access-token">Access token</label>
      <input id="access-token" type="password" autoComplete="off" value={value} onChange={(event) => setValue(event.target.value)}
        className="mt-1 w-full rounded-lg border border-line p-2" />
      <p className="mt-2 text-xs text-muted">The token stays in memory until you disconnect or reload.</p>
      {error && <p role="alert" className="mt-3 text-sm text-brand">{error}</p>}
      <div className="mt-5"><Button variant="primary" type="submit" disabled={busy || !value.trim()}>{busy ? 'Connecting…' : 'Connect'}</Button></div>
    </form>
  </main>;
}
