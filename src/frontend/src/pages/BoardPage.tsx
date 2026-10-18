import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import { useLive } from '../api/useLive';
import type { CaseStatus } from '../types/contract';
import { STATUS, STATUS_ORDER, StatusSelect, timeAgo } from '../components/ui';

export default function BoardPage() {
  const cases = useLive(() => api.listCases()) ?? [];
  const navigate = useNavigate();
  const [dragId, setDragId] = useState<string | null>(null);
  const [over, setOver] = useState<CaseStatus | null>(null);

  const drop = (status: CaseStatus) => {
    const c = cases.find((x) => x.id === dragId);
    if (c && c.status !== status) api.setStatus(c.id, status);
    setDragId(null);
    setOver(null);
  };

  return (
    <div className="flex h-full flex-col">
      <h1 className="px-6 pt-6 text-2xl font-semibold tracking-tight">My cases</h1>
      <div className="flex min-h-0 flex-1 gap-3 overflow-x-auto p-5">
        {STATUS_ORDER.map((s) => {
          const col = cases.filter((c) => c.status === s);
          return (
            <div
              key={s}
              onDragOver={(e) => {
                e.preventDefault();
                setOver(s);
              }}
              onDragLeave={() => setOver((o) => (o === s ? null : o))}
              onDrop={() => drop(s)}
              className={`flex w-56 shrink-0 flex-col rounded-2xl p-2 transition ${over === s ? 'bg-brand-soft ring-2 ring-brand/40' : 'bg-white/60'}`}
            >
              <div className="flex items-center gap-2 px-2 pb-2 pt-1 text-sm font-medium">
                <span className={`h-2 w-2 rounded-full ${STATUS[s].dot}`} />
                {STATUS[s].label}
                <span className="ml-auto text-muted">{col.length}</span>
              </div>
              <div className="flex-1 space-y-2 overflow-y-auto">
                {col.map((c) => (
                  <div
                    key={c.id}
                    draggable
                    onDragStart={() => setDragId(c.id)}
                    onDragEnd={() => setDragId(null)}
                    onClick={() => navigate(`/cases/${c.id}`)}
                    className={`cursor-grab rounded-xl border border-line bg-white p-3 shadow-sm transition hover:border-ink/30 active:cursor-grabbing ${
                      dragId === c.id ? 'opacity-40' : ''
                    }`}
                  >
                    <div className="font-medium">{c.companyLabel}</div>
                    <div className="mt-0.5 line-clamp-2 text-sm text-muted">{c.oneLineNeed}</div>
                    <div className="mt-2 flex items-center gap-2 text-xs text-muted" onClick={(e) => e.stopPropagation()}>
                      <StatusSelect status={c.status} onChange={(ns) => api.setStatus(c.id, ns)} />
                      {c.keptCount > 0 && <span>✓ {c.keptCount}</span>}
                      <span className="ml-auto">{timeAgo(c.updatedAt)}</span>
                    </div>
                  </div>
                ))}
                {col.length === 0 && <div className="rounded-xl border border-dashed border-line px-3 py-6 text-center text-xs text-muted">Drop here</div>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
