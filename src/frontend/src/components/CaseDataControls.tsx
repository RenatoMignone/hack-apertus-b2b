import { useEffect, useRef, useState } from 'react';
import { api } from '../api';
import type { BusinessContext, CaseDetail, RunStage } from '../types/contract';

/** Explicit operator input; never populate business figures from model text. */
export default function CaseDataControls({ detail, busy, onBusy, onChange, onStage, onConflict }: {
  detail: CaseDetail; busy: boolean; onBusy: (busy: boolean) => void;
  onChange: (detail: CaseDetail) => void; onConflict: (error: unknown) => Promise<void>; onStage: (stage: RunStage) => void;
}) {
  const alive = useRef(true);
  const pending = useRef(false);
  useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);
  const [confirmed, setConfirmed] = useState(false);
  const [plansConfirmed, setPlansConfirmed] = useState(false);
  const [error, setError] = useState('');
  const context = detail.businessContext;
  const [jobs, setJobs] = useState(context?.planned_jobs?.toString() ?? '');
  const [amount, setAmount] = useState(context?.investment_amount ?? '');
  const [currency, setCurrency] = useState(context?.investment_currency ?? '');
  const [timeline, setTimeline] = useState(context?.timeline ?? '');
  const result = detail.revisions.find((r) => r.id === detail.currentRevisionId);
  const reviewed = !!result?.resultHash && result.reasons.some((r) => r.selection === 'kept')
    && result.reasons.every((r) => r.selection !== 'none');
  const perform = async (task: () => Promise<CaseDetail>) => {
    if (pending.current) return;
    pending.current = true; setError(''); onBusy(true);
    try { const value = await task(); if (alive.current) onChange(value); }
    catch (e) { if (alive.current) { setError(e instanceof Error ? e.message : 'The update failed.'); await onConflict(e); } }
    finally { pending.current = false; if (alive.current) onBusy(false); }
  };
  if (!detail.memory?.available && !detail.businessContextAvailable) return null;
  const savePlans = () => {
    if (jobs && (!/^\d+$/.test(jobs) || Number(jobs) > 1000000)) { setError('Enter whole planned jobs from 0 to 1,000,000.'); return; }
    if ((amount && !/^(?:\d+)(?:\.\d{1,2})?$/.test(amount)) || (!!amount !== !!currency)) {
      setError('Enter a non-negative investment amount with up to two decimals and its currency, or leave both empty.'); return;
    }
    if (currency && !/^[A-Z]{3}$/.test(currency)) { setError('Enter an explicit three-letter currency code.'); return; }
    const values: BusinessContext = { planned_jobs: jobs ? Number(jobs) : null,
      investment_amount: amount || null, investment_currency: currency || null, timeline: timeline.trim() || null };
    void perform(() => api.setBusinessContext!(detail.case.id, values, (stage) => { if (alive.current) onStage(stage); }, detail.revision));
  };
  return <details className="my-4 rounded-xl border border-line bg-white p-4">
    <summary className="cursor-pointer text-sm font-medium">Company plans and case comparison</summary>
    {error && <p role="alert" className="mt-3 text-sm text-brand">{error}</p>}
    {detail.businessContextAvailable && api.setBusinessContext && <fieldset disabled={busy} className="mt-4 space-y-3">
      <legend className="text-sm font-medium">Manually entered company plans</legend>
      <p className="text-xs text-muted">Use permitted information only. These plans are attributed to you and do not establish actual economic impact. Saving starts new research and requires a new report review. Blank fields remain unknown.</p>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="text-sm">Planned jobs<input className="mt-1 block w-full rounded border border-line p-2" inputMode="numeric" value={jobs} onChange={(e) => setJobs(e.target.value)} /></label>
        <label className="text-sm">Planned investment<input className="mt-1 block w-full rounded border border-line p-2" inputMode="decimal" value={amount} onChange={(e) => setAmount(e.target.value)} /></label>
        <label className="text-sm">Investment currency<input className="mt-1 block w-full rounded border border-line p-2" maxLength={3} placeholder="CHF" value={currency} onChange={(e) => setCurrency(e.target.value.toUpperCase())} /></label>
        <label className="text-sm">Planned timeline<input className="mt-1 block w-full rounded border border-line p-2" maxLength={500} value={timeline} onChange={(e) => setTimeline(e.target.value)} /></label>
      </div>
      <label className="flex gap-2 text-sm"><input type="checkbox" checked={plansConfirmed} onChange={(e) => setPlansConfirmed(e.target.checked)} />I confirm these are permitted, manually entered plans.</label>
      <button className="rounded bg-ink px-3 py-2 text-sm text-white disabled:opacity-50" disabled={!plansConfirmed || busy} onClick={savePlans}>Save plans and research again</button>
    </fieldset>}
    {detail.memory?.available && api.setCaseMemory && <fieldset disabled={busy} className="mt-4 space-y-3 border-t border-line pt-4">
      <legend className="text-sm font-medium">Your case comparison history</legend>
      <p className="text-xs text-muted">Only you can retrieve these cases. Similarity compares company needs, not the likelihood of success. Fictional/test cases must stay excluded.</p>
      {detail.memory.eligible ? <button className="text-sm text-brand underline" onClick={() => void perform(() => api.setCaseMemory!(detail.case.id, false))}>Remove from my comparison history</button> : <>
        <label className="flex gap-2 text-sm"><input type="checkbox" checked={confirmed} onChange={(e) => setConfirmed(e.target.checked)} />This is a real, non-synthetic case with permitted context for comparison.</label>
        <button className="rounded border border-line px-3 py-2 text-sm disabled:opacity-50" disabled={!confirmed || !reviewed || busy}
          onClick={() => void perform(() => api.setCaseMemory!(detail.case.id, true, { resultId: result!.id, resultHash: result!.resultHash! }))}>Add reviewed case to my history</button>
        {!reviewed && <p className="text-xs text-muted">Review every reason and keep at least one first.</p>}
      </>}
    </fieldset>}
  </details>;
}
