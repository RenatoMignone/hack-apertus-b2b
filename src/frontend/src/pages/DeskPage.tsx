import type { ReactNode } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Columns3, ListChecks, Plus } from 'lucide-react';
import { api } from '../api';
import { useLive } from '../api/useLive';
import { STATUS, STATUS_ORDER } from '../components/ui';

function Card({ icon, title, count, children, footer }: { icon: ReactNode; title: string; count?: number; children: ReactNode; footer?: ReactNode }) {
  return (
    <section className="flex flex-col rounded-2xl border border-line bg-white p-5">
      <header className="mb-4 flex items-center gap-2.5">
        <span className="rounded-lg bg-canvas p-1.5 text-muted">{icon}</span>
        <h2 className="font-semibold">{title}</h2>
        {count !== undefined && <span className="ml-auto text-2xl font-semibold tabular-nums">{count}</span>}
      </header>
      <div className="flex-1">{children}</div>
      {footer && <footer className="mt-4 flex items-center justify-between text-sm text-muted">{footer}</footer>}
    </section>
  );
}

function greeting() {
  const h = new Date().getHours();
  return h < 12 ? 'Good morning' : h < 18 ? 'Good afternoon' : 'Good evening';
}

export default function DeskPage() {
  const cases = useLive(() => api.listCases()) ?? [];
  const actions = useLive(() => api.listActionItems()) ?? [];
  const navigate = useNavigate();
  const name = (id: string) => cases.find((c) => c.id === id)?.companyLabel ?? '';

  const byStatus = STATUS_ORDER.map((s) => ({ s, n: cases.filter((c) => c.status === s).length })).filter((x) => x.n);
  const openItems = actions.filter((a) => a.status !== 'done');
  const done = actions.length - openItems.length;

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-5xl px-6 py-8">
          <h1 className="mb-6 text-2xl font-semibold tracking-tight">{greeting()}</h1>
          <div className="grid gap-5 md:grid-cols-2">
            <Link
              to="/cases/new"
              className="group flex min-h-48 flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed border-line bg-white text-muted transition hover:border-brand hover:text-brand"
            >
              <span className="rounded-full bg-brand p-3 text-white transition group-hover:scale-105">
                <Plus size={22} />
              </span>
              <span className="text-lg font-semibold">New case</span>
            </Link>

            <Card
              icon={<Columns3 size={16} />}
              title="My cases"
              count={cases.length}
              footer={
                <>
                  <span>{cases.length > 3 ? `+${cases.length - 3} more` : ''}</span>
                  <Link to="/cases" className="hover:text-ink">Board →</Link>
                </>
              }
            >
              <div className="flex h-2 gap-0.5 overflow-hidden rounded-full">
                {byStatus.map(({ s, n }) => (
                  <span key={s} className={STATUS[s].dot} style={{ flex: n }} title={`${STATUS[s].label}: ${n}`} />
                ))}
              </div>
              <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted">
                {byStatus.map(({ s, n }) => (
                  <span key={s} className="flex items-center gap-1">
                    <span className={`h-1.5 w-1.5 rounded-full ${STATUS[s].dot}`} />
                    {n} {STATUS[s].label.toLowerCase()}
                  </span>
                ))}
              </div>
              <ul className="mt-4 space-y-2.5">
                {cases.slice(0, 3).map((c) => (
                  <li key={c.id} onClick={() => navigate(`/cases/${c.id}`)} className="flex cursor-pointer items-center gap-2 text-sm hover:text-brand">
                    <span className="font-medium">{c.companyLabel}</span>
                    <span className="ml-auto flex items-center gap-1.5 text-xs text-muted">
                      <span className={`h-1.5 w-1.5 rounded-full ${STATUS[c.status].dot}`} />
                      {STATUS[c.status].label}
                    </span>
                  </li>
                ))}
              </ul>
            </Card>

            <Card
              icon={<ListChecks size={16} />}
              title="Action items"
              count={openItems.length}
              footer={
                <>
                  <span>{openItems.length > 3 ? `+${openItems.length - 3} more` : ''}</span>
                  <Link to="/actions" className="hover:text-ink">All items →</Link>
                </>
              }
            >
              <div className="text-xs text-muted">
                <span className="font-medium text-ink">{done}</span> done Â· <span className="font-medium text-ink">{openItems.length}</span> open
              </div>
              <ul className="mt-3 space-y-2.5">
                {openItems.slice(0, 3).map((a) => (
                  <li key={a.id} className="flex items-start gap-2 text-sm">
                    <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full border ${a.status === 'asked' ? 'border-warn bg-warn' : 'border-muted'}`} />
                    <span className="min-w-0 flex-1">{a.question}</span>
                    <span className="shrink-0 text-xs text-muted">{name(a.caseId)}</span>
                  </li>
                ))}
              </ul>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
