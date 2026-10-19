import { useState } from 'react';
import { DropdownMenu, IconButton } from '@radix-ui/themes';
import { Link } from 'react-router-dom';
import { MoreHorizontal, Search } from 'lucide-react';
import { api } from '../api';
import { reportApiError } from '../components/ApiErrors';
import { useLive } from '../api/useLive';
import type { CaseOutcome, CaseStatus, CaseSummary } from '../types/contract';
import { useToast } from '../components/Toast';
import { CaseFlags, OUTCOME, Skeleton, STATUS, STATUS_ORDER, timeAgo, useTitle } from '../components/ui';

/** Keyboard- and mouse-friendly alternative to dragging. */
function CardMenu({ c, onMove }: { c: CaseSummary; onMove: (s: CaseStatus, outcome?: CaseOutcome) => void }) {
  const toast = useToast();
  const toggleHold = async () => {
    try {
      await api.setCaseFlags(c.id, { onHold: !c.onHold });
      toast(c.onHold ? `${c.companyLabel} is active again` : `${c.companyLabel} put on hold`,
        () => { void api.setCaseFlags(c.id, { onHold: c.onHold }).catch(reportApiError); });
    } catch (error) { reportApiError(error); }
  };
  return <div className="case-menu">
    <DropdownMenu.Root>
      <DropdownMenu.Trigger><IconButton variant="ghost" color="gray" aria-label={`Actions for ${c.companyLabel}`}><MoreHorizontal size={18} /></IconButton></DropdownMenu.Trigger>
      <DropdownMenu.Content>
        <DropdownMenu.Item asChild><Link to={`/cases/${c.id}`}>Open case</Link></DropdownMenu.Item>
        <DropdownMenu.Separator />
        <DropdownMenu.Label>Move to</DropdownMenu.Label>
        {STATUS_ORDER.filter((s) => s !== c.status && s !== 'closed').map((s) =>
          <DropdownMenu.Item key={s} onSelect={() => onMove(s)}>{STATUS[s].label}</DropdownMenu.Item>)}
        {(['visit', 'no_interest'] as CaseOutcome[]).map((o) =>
          <DropdownMenu.Item key={o} onSelect={() => onMove('closed', o)}>Closed · {OUTCOME[o].label.toLowerCase()}</DropdownMenu.Item>)}
        <DropdownMenu.Separator />
        <DropdownMenu.Item onSelect={() => { void toggleHold(); }}>{c.onHold ? 'Take off hold' : 'Put on hold'}</DropdownMenu.Item>
      </DropdownMenu.Content>
    </DropdownMenu.Root>
  </div>;
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
    try {
    const prev = { status: c.status, outcome: c.outcome };
    await api.setStatus(c.id, status);
    if (outcome) await api.setCaseFlags(c.id, { outcome });
    toast(`${c.companyLabel} → ${STATUS[status].label}${outcome ? ` · ${OUTCOME[outcome].label}` : ''}`, async () => {
      await api.setStatus(c.id, prev.status);
      await api.setCaseFlags(c.id, { outcome: prev.outcome });
    });
    } catch (error) { reportApiError(error); }
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
      <p className="px-6 pt-1 text-sm text-muted">Click anywhere on a card to open it. Drag to change status, or use its actions menu.</p>

      <div className="case-board grid min-h-0 flex-1 gap-3 overflow-x-auto p-5" style={{ minWidth: 0 }}>
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
                    className={`case-card group transition ${dragId === c.id ? 'opacity-40' : ''} ${
                      c.onHold ? 'border-dashed border-muted/60 bg-canvas' : 'border-line'
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      <Link to={`/cases/${c.id}`} draggable={false} className="case-link min-w-0 flex-1 font-semibold hover:text-brand">
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
