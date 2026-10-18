import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Columns3, ListChecks, Plus } from 'lucide-react';
import { api } from '../api';
import { useLive } from '../api/useLive';
import { useToast } from '../components/Toast';
import { CaseFlags, Skeleton, STATUS, STATUS_ORDER, useTitle } from '../components/ui';

function Card({ icon, title, count, children, footer }: { icon: ReactNode; title: string; count?: number; children: ReactNode; footer: ReactNode }) {
  return (
    <section className="flex flex-col rounded-2xl border border-line bg-white p-5">
      <header className="mb-4 flex items-center gap-2.5">
        <span className="rounded-lg bg-canvas p-1.5 text-muted" aria-hidden>{icon}</span>
        <h2 className="font-semibold">{title}</h2>
        {count !== undefined && <span className="ml-auto text-2xl font-semibold tabular-nums">{count}</span>}
      </header>
      <div className="flex-1">{children}</div>
      <footer className="mt-4 flex items-center justify-between text-sm text-muted">{footer}</footer>
    </section>
  );
}

function greeting() {
  const h = new Date().getHours();
  return h < 12 ? 'Good morning' : h < 18 ? 'Good afternoon' : 'Good evening';
}

export default function DeskPage() {
  useTitle('My desk');
  const cases = useLive(() => api.listCases());
  const actions = useLive(() => api.listActionItems());
  const last = useLive(() => api.getLastOpened());
  const toast = useToast();
  const name = (id: string) => cases?.find((c) => c.id === id)?.companyLabel ?? '';

  const byStatus = STATUS_ORDER.map((s) => ({ s, n: (cases ?? []).filter((c) => c.status === s).length })).filter((x) => x.n);
  const openItems = (actions ?? []).filter((a) => a.status !== 'done');
  const done = (actions?.length ?? 0) - openItems.length;

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-5xl px-6 py-8">
        <h1 className="mb-5 text-2xl font-semibold tracking-tight">{greeting()}</h1>

        <div className="mb-5 flex flex-wrap items-center gap-4 rounded-2xl bg-ink px-6 py-5 text-white">
          <div className="min-w-0 flex-1">
            <div className="text-lg font-semibold">Start a new case</div>
            <div className="text-sm text-white/70">Describe a company in your own words; get the Bern matches with sources.</div>
          </div>
          <Link to="/cases/new" className="inline-flex items-center gap-1.5 rounded-lg bg-brand px-4 py-2 font-medium hover:bg-brand-dark">
            <Plus size={18} aria-hidden /> New case
          </Link>
        </div>

        <div className="grid gap-5 md:grid-cols-2">
          <Card
            icon={<Columns3 size={16} />}
            title="My cases"
            count={cases?.length}
            footer={
              <>
                <span />
                <Link to="/cases" className="font-medium hover:text-ink">Open board →</Link>
              </>
            }
          >
            {!cases ? (
              <Skeleton className="h-32" />
            ) : (
              <>
                <div className="flex h-2 gap-0.5 overflow-hidden rounded-full" role="img" aria-label={byStatus.map(({ s, n }) => `${n} ${STATUS[s].label}`).join(', ')}>
                  {byStatus.map(({ s, n }) => (
                    <span key={s} className={STATUS[s].dot} style={{ flex: n }} />
                  ))}
                </div>
                <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted">
                  {byStatus.map(({ s, n }) => (
                    <span key={s} className="flex items-center gap-1">
                      <span className={`h-1.5 w-1.5 rounded-full ${STATUS[s].dot}`} aria-hidden />
                      {n} {STATUS[s].label.toLowerCase()}
                    </span>
                  ))}
                </div>
                {last && (
                  <Link to={`/cases/${last.id}`} className="mt-4 flex items-center gap-2 rounded-xl bg-canvas px-3 py-2.5 text-sm hover:bg-line/60">
                    <span className="text-muted">Continue:</span>
                    <span className="font-medium">{last.companyLabel}</span>
                    <ArrowRight size={15} className="ml-auto text-muted" aria-hidden />
                  </Link>
                )}
                <ul className="mt-3 space-y-1">
                  {cases.slice(0, 3).map((c) => (
                    <li key={c.id}>
                      <Link to={`/cases/${c.id}`} className="flex items-center gap-2 rounded-lg px-1 py-1.5 text-sm hover:text-brand">
                        <span className="font-medium">{c.companyLabel}</span>
                        <span className="ml-auto flex items-center gap-1.5 text-xs text-muted">
                          <CaseFlags outcome={c.outcome} onHold={c.onHold} />
                          <span className={`h-1.5 w-1.5 rounded-full ${STATUS[c.status].dot}`} aria-hidden />
                          {STATUS[c.status].label}
                        </span>
                      </Link>
                    </li>
                  ))}
                </ul>
              </>
            )}
          </Card>

          <Card
            icon={<ListChecks size={16} />}
            title="Action items"
            count={actions ? openItems.length : undefined}
            footer={
              <>
                <span className="text-xs">{done} done · {openItems.length} open</span>
                <Link to="/actions" className="font-medium hover:text-ink">All items →</Link>
              </>
            }
          >
            {!actions ? (
              <Skeleton className="h-32" />
            ) : openItems.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted">All clear.</p>
            ) : (
              <ul className="space-y-2">
                {openItems.slice(0, 4).map((a) => (
                  <li key={a.id} className="flex items-start gap-2.5 text-sm">
                    <input
                      type="checkbox"
                      aria-label={`Mark done: ${a.question}`}
                      onChange={async () => {
                        await api.setActionStatus(a.id, 'done');
                        toast('Marked done', () => api.setActionStatus(a.id, a.status));
                      }}
                      className="mt-0.5 h-4 w-4 shrink-0 accent-[var(--color-ok)]"
                    />
                    <span className="min-w-0 flex-1">
                      {a.question}
                      {a.status === 'asked' && <span className="ml-1.5 text-xs text-warn">awaiting answer</span>}
                    </span>
                    <span className="shrink-0 text-xs text-muted">{name(a.caseId)}</span>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
