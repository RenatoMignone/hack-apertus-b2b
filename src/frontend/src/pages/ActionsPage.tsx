import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Send } from 'lucide-react';
import { api } from '../api';
import { useLive } from '../api/useLive';
import type { ActionItem } from '../types/contract';
import { useToast } from '../components/Toast';
import { Skeleton, useTitle } from '../components/ui';

const ROLES = ['Account owner', 'Life-sciences lead', 'Investment team', 'Other colleague'];

function Row({ a }: { a: ActionItem }) {
  const toast = useToast();
  const [answer, setAnswer] = useState(a.answer ?? '');
  const done = a.status === 'done';

  return (
    <li className="px-4 py-3">
      <div className="flex items-start gap-3">
        <input
          type="checkbox"
          checked={done}
          aria-label={`${done ? 'Reopen' : 'Mark done'}: ${a.question}`}
          onChange={async () => {
            await api.setActionStatus(a.id, done ? 'open' : 'done');
            toast(done ? 'Reopened' : 'Marked done', () => api.setActionStatus(a.id, a.status));
          }}
          className="mt-1 h-4 w-4 shrink-0 accent-[var(--color-ok)]"
        />
        <div className="min-w-0 flex-1">
          <div className={`text-sm ${done ? 'text-muted line-through' : ''}`}>{a.question}</div>
          <div className="text-xs text-muted">
            Ask: {a.askRole}
            {a.status === 'asked' && <span className="ml-2 font-medium text-warn">· Awaiting answer</span>}
          </div>
        </div>
        {!done && (
          <button
            onClick={async () => {
              const next = a.status === 'asked' ? 'open' : 'asked';
              await api.setActionStatus(a.id, next);
              toast(next === 'asked' ? 'Marked as asked' : 'Marked as not asked yet');
            }}
            className={`inline-flex shrink-0 items-center gap-1 rounded-lg px-2.5 py-1 text-xs font-medium ring-1 ${
              a.status === 'asked' ? 'bg-warn-soft text-warn ring-warn/40' : 'text-muted ring-line hover:text-ink'
            }`}
          >
            <Send size={12} aria-hidden /> {a.status === 'asked' ? 'Asked' : 'Mark asked'}
          </button>
        )}
      </div>
      {done && (
        <input
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          onBlur={() => answer !== (a.answer ?? '') && api.setActionStatus(a.id, 'done', answer)}
          placeholder="Their answer (optional)"
          aria-label="Answer note"
          className="ml-7 mt-2 w-[calc(100%-1.75rem)] rounded-lg border border-line bg-canvas px-2.5 py-1.5 text-sm outline-none focus:border-ink/40"
        />
      )}
    </li>
  );
}

function AddQuestion({ caseId }: { caseId: string }) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState('');
  const [role, setRole] = useState(ROLES[0]);
  const toast = useToast();

  if (!open)
    return (
      <li>
        <button onClick={() => setOpen(true)} className="flex w-full items-center gap-2 px-4 py-2.5 text-sm text-muted hover:bg-canvas hover:text-ink">
          <Plus size={15} aria-hidden /> Add question
        </button>
      </li>
    );

  const save = async () => {
    if (!q.trim()) return;
    await api.addActionItem(caseId, q.trim(), role);
    toast('Question added');
    setQ('');
    setOpen(false);
  };

  return (
    <li className="flex flex-wrap items-center gap-2 px-4 py-2.5">
      <input
        autoFocus
        value={q}
        onChange={(e) => setQ(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && save()}
        placeholder="What do you need to ask?"
        aria-label="New question"
        className="min-w-48 flex-1 rounded-lg border border-line px-2.5 py-1.5 text-sm outline-none focus:border-ink/40"
      />
      <select value={role} onChange={(e) => setRole(e.target.value)} aria-label="Who to ask" className="rounded-lg border border-line bg-white px-2 py-1.5 text-sm">
        {ROLES.map((r) => <option key={r}>{r}</option>)}
      </select>
      <button onClick={save} className="rounded-lg bg-brand px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-dark">Add</button>
      <button onClick={() => setOpen(false)} className="rounded-lg px-2 py-1.5 text-sm text-muted hover:text-ink">Cancel</button>
    </li>
  );
}

export default function ActionsPage() {
  useTitle('Action items');
  const items = useLive(() => api.listActionItems());
  const cases = useLive(() => api.listCases()) ?? [];
  const [tab, setTab] = useState<'open' | 'done'>('open');

  const all = items ?? [];
  const shown = all.filter((a) => (tab === 'done' ? a.status === 'done' : a.status !== 'done'));
  const caseIds = tab === 'open' ? [...new Set([...shown.map((a) => a.caseId), ...cases.filter((c) => c.status !== 'closed').map((c) => c.id)])] : [...new Set(shown.map((a) => a.caseId))];
  const name = (id: string) => cases.find((c) => c.id === id)?.companyLabel ?? 'Case';
  const openCount = all.filter((a) => a.status !== 'done').length;

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-3xl px-6 py-8">
        <div className="mb-1 flex flex-wrap items-center gap-2">
          <h1 className="mr-3 text-2xl font-semibold tracking-tight">Action items</h1>
          <div role="tablist" className="flex gap-1">
            {(['open', 'done'] as const).map((t) => (
              <button
                key={t}
                role="tab"
                aria-selected={tab === t}
                onClick={() => setTab(t)}
                className={`rounded-full px-3 py-1 text-sm ${tab === t ? 'bg-ink text-white' : 'text-muted hover:bg-white hover:text-ink'}`}
              >
                {t === 'open' ? 'Open' : 'Done'} <span className="opacity-70">{t === 'open' ? openCount : all.length - openCount}</span>
              </button>
            ))}
          </div>
        </div>
        <p className="mb-5 text-sm text-muted">Questions to ask colleagues, per case. Tick them off when you have the answer.</p>

        {!items && <Skeleton className="h-40" />}
        <div className="space-y-5">
          {caseIds.map((cid) => {
            const rows = shown.filter((a) => a.caseId === cid);
            return (
              <section key={cid}>
                <Link to={`/cases/${cid}`} className="mb-2 inline-block font-semibold hover:text-brand">{name(cid)}</Link>
                <ul className="divide-y divide-line overflow-hidden rounded-xl border border-line bg-white">
                  {rows.map((a) => <Row key={a.id} a={a} />)}
                  {tab === 'open' && <AddQuestion caseId={cid} />}
                </ul>
              </section>
            );
          })}
          {items && shown.length === 0 && tab === 'done' && <p className="py-10 text-center text-sm text-muted">Nothing done yet.</p>}
        </div>
      </div>
    </div>
  );
}
