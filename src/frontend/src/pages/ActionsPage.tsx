import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Check, Send } from 'lucide-react';
import { api } from '../api';
import { useLive } from '../api/useLive';
import type { ActionItem } from '../types/contract';

export default function ActionsPage() {
  const items = useLive(() => api.listActionItems()) ?? [];
  const cases = useLive(() => api.listCases()) ?? [];
  const [tab, setTab] = useState<'open' | 'done'>('open');

  const shown = items.filter((a) => (tab === 'done' ? a.status === 'done' : a.status !== 'done'));
  const caseIds = [...new Set(shown.map((a) => a.caseId))];
  const name = (id: string) => cases.find((c) => c.id === id)?.companyLabel ?? 'Case';
  const set = (a: ActionItem, status: ActionItem['status']) => api.setActionStatus(a.id, a.status === status ? 'open' : status);
  const openCount = items.filter((a) => a.status !== 'done').length;

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl px-6 py-8">
          <div className="mb-5 flex items-center gap-1">
            <h1 className="mr-4 text-2xl font-semibold tracking-tight">Action items</h1>
            {(['open', 'done'] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`rounded-full px-3 py-1 text-sm ${tab === t ? 'bg-ink text-white' : 'text-muted hover:bg-white hover:text-ink'}`}
              >
                {t === 'open' ? 'Open' : 'Done'} <span className="opacity-60">{t === 'open' ? openCount : items.length - openCount}</span>
              </button>
            ))}
          </div>

          <div className="space-y-5">
            {caseIds.map((cid) => (
              <section key={cid}>
                <Link to={`/cases/${cid}`} className="mb-2 inline-block font-semibold hover:text-brand">
                  {name(cid)}
                </Link>
                <div className="divide-y divide-line overflow-hidden rounded-xl border border-line bg-white">
                  {shown
                    .filter((a) => a.caseId === cid)
                    .map((a) => (
                      <div key={a.id} className="flex items-center gap-3 px-4 py-3">
                        <div className="min-w-0 flex-1">
                          <div className={`text-sm ${a.status === 'done' ? 'text-muted line-through' : ''}`}>{a.question}</div>
                          <div className="text-xs text-muted">Ask: {a.askRole}</div>
                        </div>
                        <button
                          onClick={() => set(a, 'asked')}
                          className={`inline-flex items-center gap-1 rounded-lg px-2.5 py-1 text-xs font-medium ring-1 ${
                            a.status === 'asked' ? 'bg-warn-soft text-warn ring-warn/40' : 'text-muted ring-line hover:text-ink'
                          }`}
                        >
                          <Send size={12} /> Asked
                        </button>
                        <button
                          onClick={() => set(a, 'done')}
                          className={`inline-flex items-center gap-1 rounded-lg px-2.5 py-1 text-xs font-medium ring-1 ${
                            a.status === 'done' ? 'bg-ok text-white ring-ok' : 'text-muted ring-line hover:text-ok'
                          }`}
                        >
                          <Check size={12} /> Done
                        </button>
                      </div>
                    ))}
                </div>
              </section>
            ))}
            {shown.length === 0 && <p className="py-10 text-center text-sm text-muted">{tab === 'open' ? 'All clear.' : 'Nothing done yet.'}</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
