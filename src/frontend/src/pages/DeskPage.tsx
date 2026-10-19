import { Card as Surface, Button as RadixButton } from '@radix-ui/themes';
import { beginCase } from '../api/pendingCase';
import { useEffect, useRef, useState, type ReactNode } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowRight, ArrowUp, Columns3, ListChecks, Lock } from 'lucide-react';
import { api, apiMode } from '../api';
import { useLive } from '../api/useLive';
import { reportApiError } from '../components/ApiErrors';
import { CaseFlags, Skeleton, STATUS, STATUS_ORDER, useTitle } from '../components/ui';
import type { CaseDetail, CaseSummary } from '../types/contract';

// Home: start a case, see all cases, and what is waiting on her. Next steps come
// only from her own case state (no colleague to-dos: meetings and follow-up are the
// agency's job, outside the challenge).

function Card({ icon, title, count, children, footer }: { icon: ReactNode; title: string; count?: number; children: ReactNode; footer: ReactNode }) {
  return (
    <Surface size="4" className="flex flex-col">
      <header className="mb-4 flex items-center gap-2.5">
        <span className="rounded-lg bg-canvas p-1.5 text-muted" aria-hidden>{icon}</span>
        <h2 className="text-sm font-semibold">{title}</h2>
        {count !== undefined && <span className="ml-auto text-xl font-semibold tabular-nums">{count}</span>}
      </header>
      <div className="flex-1">{children}</div>
      <footer className="mt-4 flex items-center justify-between text-sm text-muted">{footer}</footer>
    </Surface>
  );
}

function greeting() {
  const h = new Date().getHours();
  return h < 12 ? 'Good morning' : h < 18 ? 'Good afternoon' : 'Good evening';
}

type Step = { caseId: string; company: string; action: string; rank: number; updatedAt: string };

const isOpen = (c: CaseSummary) => c.status !== 'closed' && !c.onHold;
const byRecent = (a: { updatedAt: string }, b: { updatedAt: string }) => b.updatedAt.localeCompare(a.updatedAt);

/** What is waiting on her, most urgent first. Closed and on-hold cases are skipped. */
function nextSteps(cases: CaseSummary[], details: CaseDetail[]): Step[] {
  const detail = new Map(details.map((d) => [d.case.id, d]));
  const steps: Step[] = [];
  for (const c of cases.filter(isOpen)) {
    const step = (action: string, rank: number) => steps.push({ caseId: c.id, company: c.companyLabel, action, rank, updatedAt: c.updatedAt });
    if (c.status === 'pitch_sent') {
      step('Record the outcome', 4);
      continue;
    }
    const d = detail.get(c.id);
    if (!d) continue;
    if (d.currentRun && ["queued", "running"].includes(d.currentRun.status)) {
      step("View research progress", 2);
      continue;
    }
    if (d.currentRun?.status === "failed") {
      step("Retry interrupted research", 1);
      continue;
    }
    // Same rule as the case page: the backend's run state, or an open demo question.
    const waiting = d.currentRun?.status === 'waiting_for_input' ||
      (apiMode === 'mock' && d.turns.some((t) => t.followUp && !t.followUp.answer));
    if (waiting) {
      step('Answer the agent’s question', 1);
      continue;
    }
    const rev = d.revisions.find((r) => r.id === d.currentRevisionId) ?? d.revisions[d.revisions.length - 1];
    const unreviewed = rev?.reasons.filter((r) => r.selection === 'none').length ?? 0;
    if (unreviewed) step(`Review ${unreviewed} item${unreviewed === 1 ? '' : 's'}`, 2);
    else if (c.keptCount > 0) step('Export the brief', 3);
  }
  return steps.sort((a, b) => a.rank - b.rank || byRecent(a, b));
}

async function loadDesk() {
  const cases = (await api.listCases()).sort(byRecent);
  // Details only for open cases still in research or review, newest first.
  const open = cases.filter((c) => isOpen(c) && c.status !== 'pitch_sent').slice(0, 8);
  const loaded = await Promise.allSettled(open.map((c) => api.getCase(c.id)));
  const details = loaded.flatMap((item) => item.status === "fulfilled" && item.value ? [item.value] : []);
  return { cases, steps: nextSteps(cases, details), unavailable: loaded.filter((item) => item.status === "rejected").length };
}

function QuickStart() {
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  const box = useRef<HTMLTextAreaElement>(null);

  // Start roomy and grow with the text, so longer descriptions stay readable.
  useEffect(() => {
    const el = box.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 320) + 'px';
  }, [text]);

  const submit = async () => {
    if (!text.trim() || busy) return;
    setBusy(true);
    try {
      const requestId = beginCase(text.trim(), (prompt) => api.createCase(prompt));
      navigate(`/cases/starting/${requestId}`);
    } catch (error) { reportApiError(error); }
    finally { setBusy(false); }
  };

  return (
    <div className="mb-7 rounded-2xl bg-ink px-7 py-6 text-white">
      <div className="text-xl font-semibold tracking-tight">Start with a company</div>
      <div className="mt-4 rounded-xl bg-white p-3 text-ink">
        <textarea
          ref={box}
          aria-label="Company description"
          disabled={busy}
          maxLength={50000}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) submit();
          }}
          rows={4}
          placeholder="Describe a company in your own words: what they do, what they need…"
          className="w-full resize-none bg-transparent px-2 py-1 text-[15px] leading-relaxed outline-none placeholder:text-muted/60"
        />
        <div className="flex flex-wrap items-center gap-3 px-2">
          <span className="flex w-full items-start gap-1.5 text-xs text-muted sm:w-auto sm:items-center">
            <Lock size={13} className="shrink-0" aria-hidden /> Public information only. No confidential documents.
          </span>
          <span className="ml-auto hidden text-xs text-muted sm:inline">Ctrl + Enter</span>
          <RadixButton
            onClick={submit}
            disabled={!text.trim() || busy}
          >
            {busy ? 'Starting…' : 'Start research'} <ArrowUp size={15} aria-hidden />
          </RadixButton>
        </div>
      </div>
      <Link to="/cases/new" className="mt-3 inline-block text-sm text-white/70 hover:text-white">
        More room and examples →
      </Link>
    </div>
  );
}

export default function DeskPage() {
  useTitle('My desk');
  const desk = useLive(loadDesk);
  const cases = desk?.cases;
  const steps = desk?.steps;
  const byStatus = STATUS_ORDER.map((s) => ({ s, n: (cases ?? []).filter((c) => c.status === s).length })).filter((x) => x.n);
  const openCount = (cases ?? []).filter(isOpen).length;

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-6xl px-6 py-9 lg:px-10">
        <div className="mb-8"><p className="mb-2 text-sm text-muted">Research &amp; Expertise Navigator</p><h1 className="text-3xl font-semibold tracking-tight">{greeting()}</h1><p className="mt-2 text-muted">Turn company needs into a source-backed case for Bern.</p></div>

        <QuickStart />

        {!!desk?.unavailable && <p role="status" className="mb-4 text-sm text-warn">Some case details could not be loaded. Open the case directly to retry.</p>}
        <div className="grid gap-5 md:grid-cols-2">
          <Card
            icon={<Columns3 size={16} />}
            title="All cases"
            count={cases?.length}
            footer={
              <>
                <span />
                <Link to="/cases" className="font-medium hover:text-ink">Open board →</Link>
              </>
            }
          >
            {!cases ? (
              <Skeleton className="h-24" />
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
                <ul className="mt-3 space-y-0.5">
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
            title="Next steps"
            count={steps?.length}
            footer={
              <>
                <span className="text-xs">{cases && `${openCount} open case${openCount === 1 ? '' : 's'}`}</span>
                <Link to="/cases" className="font-medium hover:text-ink">Open board →</Link>
              </>
            }
          >
            {!steps ? (
              <Skeleton className="h-24" />
            ) : steps.length === 0 ? (
              <p className="py-4 text-center text-sm text-muted">Nothing waiting. All clear.</p>
            ) : (
              <ul className="space-y-0.5">
                {steps.slice(0, 5).map((s) => (
                  <li key={s.caseId}>
                    <Link to={`/cases/${s.caseId}`} className="flex items-center gap-2 rounded-lg px-1 py-1.5 text-sm hover:text-brand">
                      <span className="min-w-0 flex-1">
                        {s.action}
                        <span className="text-muted"> · {s.company}</span>
                      </span>
                      <ArrowRight size={15} className="shrink-0 text-muted" aria-hidden />
                    </Link>
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
