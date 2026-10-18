import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { MoreHorizontal, Search } from 'lucide-react';
import { api } from '../api';
import { useLive } from '../api/useLive';
import type { CaseOutcome, CaseStatus, CaseSummary } from '../types/contract';
import { useToast } from '../components/Toast';
import { CaseFlags, OUTCOME, Skeleton, STATUS, STATUS_ORDER, timeAgo, useTitle } from '../components/ui';

/** Keyboard- and mouse-friendly alternative to dragging. */
function CardMenu({ c, onMove }: { c: CaseSummary; onMove: (s: CaseStatus, outcome?: CaseOutcome) => void }) {
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  const toast = useToast();

  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent) => !box.current?.contains(e.target as Node) && setOpen(false);
    const esc = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false);
    document.addEventListener('mousedown', close);
    document.addEventListener('keydown', esc);
    return () => {
      document.removeEventListener('mousedown', close);
      document.removeEventListener('keydown', esc);
    };
  }, [open]);

  const item = 'block w-full rounded-md px-2.5 py-1.5 text-left text-sm hover:bg-canvas';
  return (
    <div ref={box} className="relative">
      <button
        onClick={() => setOpen(!open)}
        aria-label={`Actions for ${c.companyLabel}`}
        aria-expanded={open}
        className="rounded-md p-1 text-muted hover:bg-canvas hover:text-ink"
      >
        <MoreHorizontal size={16} />
      </button>
      {open && (
        <div className="absolute right-0 top-7 z-20 w-48 rounded-xl border border-line bg-white p-1 shadow-lg">
          <div className="px-2.5 pb-1 pt-1.5 text-xs font-medium text-muted">Move to</div>
          {STATUS_ORDER.filter((s) => s !== c.status && s !== 'closed').map((s) => (
            <button key={s} className={item} onClick={() => (onMove(s), setOpen(false))}>
              {STATUS[s].label}
            </button>
          ))}
          {(['visit', 'no_interest'] as CaseOutcome[]).map((o) => (
            <button key={o} className={item} onClick={() => (onMove('closed', o), setOpen(false))}>
              Closed · {OUTCOME[o].label.toLowerCase()}
            </button>
          ))}
          <div className="my-1 border-t border-line" />
          <button
            className={item}
            onClick={async () => {
              await api.setCaseFlags(c.id, { onHold: !c.onHold });
              toast(c.onHold ? `${c.companyLabel} is active again` : `${c.companyLabel} put on hold`, () => api.setCaseFlags(c.id, { onHold: c.onHold }));
              setOpen(false);
            }}
          >
            {c.onHold ? 'Take off hold' : 'Put on hold'}
          </button>
        </div>
      )}
    </div>
  );
}

export default function BoardPage() {
  useTitle('My cases');
  const cases = useLive(() => api.listCases());
  const toast = useToast();
  const [dragId, setDragId] = useState<string | null>(null);
  const [over, setOver] = useState<CaseStatus | null>(null);
  const [q, setQ] = useState('');

  const move = async (c: CaseSummary, status: CaseStatus, outcome?: CaseOutcome) => {
    if (c.status === status && c.outcome === outcome) return;
    const prev = { status: c.status, outcome: c.outcome };
    await api.setStatus(c.id, status);
    if (outcome) await api.setCaseFlags(c.id, { outcome });
    toast(`${c.companyLabel} → ${STATUS[status].label}${outcome ? ` · ${OUTCOME[outcome].label}` : ''}`, async () => {
      await api.setStatus(c.id, prev.status);
      if (prev.outcome) await api.setCaseFlags(c.id, { outcome: prev.outcome });
    });
  };

  const visible = (cases ?? []).filter((c) => `${c.companyLabel} ${c.oneLineNeed}`.toLowerCase().includes(q.toLowerCase()));

  return (
    <div className="flex h-full flex-col">
      <div className="flex flex-wrap items-center gap-3 px-6 pt-6">
        <h1 className="mr-auto text-2xl font-semibold tracking-tight">My cases</h1>
        <label className="flex items-center gap-2 rounded-lg border border-line bg-white px-3 py-1.5 text-sm">
          <Search size={15} className="text-muted" aria-hidden />
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search cases" aria-label="Search cases" className="w-40 outline-none" />
        </label>
      </div>
      <p className="px-6 pt-1 text-sm text-muted">Drag a card to another column, or use its ⋯ menu.</p>

      <div className="grid min-h-0 flex-1 grid-cols-4 gap-3 overflow-x-auto p-5" style={{ minWidth: 0 }}>
        {STATUS_ORDER.map((s) => {
          const col = visible.filter((c) => c.status === s);
          return (
            <section
              key={s}
              aria-label={STATUS[s].label}
              onDragOver={(e) => {
                e.preventDefault();
                setOver(s);
              }}
              onDragLeave={() => setOver((o) => (o === s ? null : o))}
              onDrop={() => {
                const c = cases?.find((x) => x.id === dragId);
                if (c) move(c, s);
                setDragId(null);
                setOver(null);
              }}
              className={`flex min-w-[200px] flex-col rounded-2xl p-2 transition ${over === s ? 'bg-brand-soft ring-2 ring-brand/40' : 'bg-white/60'}`}
            >
              <h2 className="flex items-center gap-2 px-2 pb-2 pt-1 text-sm font-semibold">
                <span className={`h-2 w-2 rounded-full ${STATUS[s].dot}`} aria-hidden />
                {STATUS[s].label}
                <span className="ml-auto font-normal text-muted">{col.length}</span>
              </h2>
              <div className="flex-1 space-y-2 overflow-y-auto">
                {!cases && [0, 1].map((i) => <Skeleton key={i} className="h-24" />)}
                {col.map((c) => (
                  <div
                    key={c.id}
                    draggable
                    onDragStart={() => setDragId(c.id)}
                    onDragEnd={() => setDragId(null)}
                    className={`group rounded-xl border bg-white p-3 shadow-sm transition hover:border-ink/30 ${dragId === c.id ? 'opacity-40' : ''} ${
                      c.onHold ? 'border-dashed border-muted/60 bg-canvas' : 'border-line'
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      <Link to={`/cases/${c.id}`} draggable={false} className="min-w-0 flex-1 font-medium hover:text-brand">
                        {c.companyLabel}
                      </Link>
                      <CardMenu c={c} onMove={(st, o) => move(c, st, o)} />
                    </div>
                    <div className="mt-0.5 line-clamp-2 text-sm text-muted">{c.oneLineNeed}</div>
                    <div className="mt-2 flex flex-wrap items-center gap-1.5 text-xs text-muted">
                      <CaseFlags outcome={c.outcome} onHold={c.onHold} />
                      {c.keptCount > 0 && <span title="Items kept for the pitch">✓ {c.keptCount}</span>}
                      <span className="ml-auto">{timeAgo(c.updatedAt)}</span>
                    </div>
                  </div>
                ))}
                {cases && col.length === 0 && (
                  <div className="rounded-xl border border-dashed border-line px-3 py-6 text-center text-xs text-muted">No cases</div>
                )}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}
