import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Check, ChevronDown, ClipboardList, ExternalLink, FlaskConical, HelpCircle, Lightbulb, SearchX, Users } from 'lucide-react';
import type { BriefRevision, Evidence, Reason, ReasonCategory, Selection } from '../types/contract';
import { CaseFlags, INSTITUTION, StatusBadge } from './ui';
import SearchSankey from './SearchSankey';

type Open = (evidenceId: string) => void;

const plural = (n: number, word: string) => `${n} ${word}${n === 1 ? '' : 's'}`;

const CATEGORIES: { key: ReasonCategory; label: string; Icon: typeof Users }[] = [
  { key: 'people', label: 'People', Icon: Users },
  { key: 'groups', label: 'Research groups', Icon: FlaskConical },
  { key: 'projects', label: 'Projects & studies', Icon: ClipboardList },
  { key: 'ideas', label: 'Ideas to explore', Icon: Lightbulb },
];

function Chips({ ids, evidence, onOpen, active }: { ids: string[]; evidence: Record<string, Evidence>; onOpen: Open; active?: string }) {
  return (
    <span className="ml-1 inline-flex gap-0.5 align-baseline">
      {ids.map((id) => {
        const ev = evidence[id];
        if (!ev) return null;
        return (
          <button
            key={id}
            title={`${ev.label} · ${INSTITUTION[ev.institution].label}`}
            onClick={(e) => {
              e.stopPropagation();
              onOpen(id);
            }}
            className={`inline-flex h-[18px] min-w-[18px] items-center justify-center rounded px-1 text-xs font-semibold tabular-nums ${
              active === id ? 'bg-ink text-white' : 'bg-white text-ink ring-1 ring-line hover:bg-ink hover:text-white'
            }`}
          >
            {ev.n}
          </button>
        );
      })}
    </span>
  );
}

function Highlighted({ ev }: { ev: Evidence }) {
  const i = ev.highlight ? ev.excerpt.indexOf(ev.highlight) : -1;
  if (i < 0) return <>{ev.excerpt}</>;
  return (
    <>
      {ev.excerpt.slice(0, i)}
      <mark className="ev">{ev.highlight}</mark>
      {ev.excerpt.slice(i + ev.highlight!.length)}
    </>
  );
}

function ReasonCard({
  r,
  n,
  evidence,
  onOpen,
  active,
  flash,
  onSelect,
}: {
  r: Reason;
  n: number;
  evidence: Record<string, Evidence>;
  onOpen: Open;
  active?: string;
  flash: boolean;
  onSelect: (s: Selection) => void;
}) {
  const [open, setOpen] = useState(false);
  const kept = r.selection === 'kept';
  const idea = r.category === 'ideas';
  const person = r.category === 'people' ? r.entries[0] : undefined;
  const initials = r.headline
    .split(/\s+/)
    .filter((w) => !/^(prof|dr|med|phil|pd)\.?$/i.test(w))
    .map((w) => w[0])
    .slice(-2)
    .join('');
  const profileUrl = person ? evidence[person.evidenceIds[0]]?.url : undefined;

  if (r.selection === 'rejected') {
    return (
      <div className="flex items-center justify-between rounded-xl px-4 py-2 text-sm text-muted">
        <span>
          <span className="line-through">{r.headline}</span> · hidden
        </span>
        <button onClick={() => onSelect('none')} className="text-xs font-medium text-ink hover:underline">Show again</button>
      </div>
    );
  }

  const sources = [...new Set(r.entries.flatMap((e) => e.evidenceIds))].map((id) => evidence[id]).filter(Boolean);

  return (
    <div
      id={`reason-${r.id}`}
      className={`rounded-xl border bg-white transition ${flash ? 'changed-flash' : ''} ${
        kept ? 'border-ok ring-1 ring-ok/30' : idea ? 'border-dashed border-warn/60' : 'border-line'
      }`}
    >
      <div className="flex cursor-pointer items-start gap-3 p-4" onClick={() => setOpen(!open)}>
        {person ? (
          <span
            className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-sm font-semibold text-white"
            style={{ background: INSTITUTION[person.institution].hex }}
          >
            {initials}
          </span>
        ) : (
          <span
            className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-sm font-semibold ${
              idea ? 'bg-warn-soft text-warn' : 'bg-brand text-white'
            }`}
          >
            {idea ? <Lightbulb size={15} /> : n}
          </span>
        )}
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-[16px] font-semibold leading-snug">{r.headline}</h3>
            {r.fromLead && <span className="rounded-full bg-ok-soft px-2 py-0.5 text-xs font-medium text-ok">Your lead ✓</span>}
            {idea && <span className="rounded-full bg-warn-soft px-2 py-0.5 text-xs font-medium text-warn">Idea · to validate</span>}
          </div>
          {person?.role && (
            <div className="text-sm">
              <span className="text-muted">{INSTITUTION[person.institution].short} · </span>
              {person.role}
            </div>
          )}
          <p className="mt-0.5 text-sm text-muted">
            {r.line.text}
            <Chips ids={r.line.evidenceIds} evidence={evidence} onOpen={onOpen} active={active} />
          </p>
          {person ? (
            profileUrl && (
              <a
                href={profileUrl}
                target="_blank"
                rel="noreferrer"
                onClick={(e) => e.stopPropagation()}
                className="mt-2 inline-flex items-center gap-1 text-sm font-medium text-ink hover:text-brand"
              >
                Source page <ExternalLink size={13} />
              </a>
            )
          ) : (
            <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm">
              {r.entries.map((e) => (
                <span key={e.id} className="flex items-center gap-1.5">
                  <span className={`h-2 w-2 rounded-full ${INSTITUTION[e.institution].dot}`} />
                  <span className="text-muted">{INSTITUTION[e.institution].short}</span>
                  <span className="font-medium">{e.name}</span>
                </span>
              ))}
            </div>
          )}
        </div>
        <div className="flex shrink-0 items-center gap-1" onClick={(e) => e.stopPropagation()}>
          <button
            aria-pressed={kept}
            onClick={() => onSelect(kept ? 'none' : 'kept')}
            className={`inline-flex items-center gap-1 rounded-lg px-2 py-1 text-sm font-medium ${
              kept ? 'bg-ok text-white' : 'text-muted ring-1 ring-line hover:text-ok hover:ring-ok'
            }`}
          >
            <Check size={14} aria-hidden /> {kept ? 'Kept' : 'Keep'}
          </button>
          <button onClick={() => onSelect('rejected')} className="rounded-lg px-2 py-1 text-sm text-muted ring-1 ring-line hover:text-bad hover:ring-bad">
            Hide
          </button>
          <button
            onClick={() => setOpen(!open)}
            aria-expanded={open}
            aria-label={open ? 'Hide sources' : 'Show sources'}
            title={open ? 'Hide sources' : 'Show sources'}
            className="ml-0.5 rounded-md p-1 text-muted hover:bg-canvas hover:text-ink"
          >
            <ChevronDown size={16} className={`transition ${open ? 'rotate-180' : ''}`} />
          </button>
        </div>
      </div>

      {open && (
        <div className="space-y-2 border-t border-line px-4 py-3">
          {sources.map((ev) => (
            <div key={ev.id} className="flex gap-2 text-sm">
              <span className="mt-0.5 h-fit rounded bg-canvas px-1.5 text-xs font-semibold ring-1 ring-line">{ev.n}</span>
              <div className="min-w-0">
                <p className="leading-relaxed">“<Highlighted ev={ev} />”</p>
                <a href={ev.url} target="_blank" rel="noreferrer" className="mt-0.5 inline-flex items-center gap-1 text-xs text-muted hover:text-ink">
                  {ev.title.split(' — ')[0]} <ExternalLink size={11} />
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Results({
  revision,
  companyLabel,
  evidence,
  onOpen,
  activeEvidence,
  flash,
  onSelect,
}: {
  revision: BriefRevision;
  companyLabel: string;
  evidence: Record<string, Evidence>;
  onOpen: Open;
  activeEvidence?: string;
  flash: Set<string>;
  onSelect: (reasonId: string, s: Selection) => void;
}) {
  const [traceOpen, setTraceOpen] = useState(false);
  const { reasons, coverage, openQuestions, trace } = revision;
  // Groups and projects are numbered as one running list; people and ideas use icons.
  const numbered = reasons.filter((r) => r.category === 'groups' || r.category === 'projects').map((r) => r.id);
  const sourceCount = new Set(trace.links.map((l) => l.target).filter((id) => evidence[id])).size;

  if (!reasons.length) {
    return (
      <div className="mx-auto mt-12 max-w-md rounded-2xl border border-line bg-white p-8 text-center">
        <SearchX className="mx-auto text-muted" />
        <h2 className="mt-3 font-semibold">{coverage.resultKind === 'out_of_scope' ? 'Out of scope' : 'No reliable match'}</h2>
        <p className="mt-1 text-sm text-muted">{revision.emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {revision.company && (
        <div className="rounded-2xl border border-line bg-white p-5">
          <div className="flex items-baseline gap-2">
            <h1 className="text-xl font-semibold tracking-tight">{companyLabel}</h1>
            <span className="text-xs text-muted">from your message</span>
          </div>
          <p className="mt-1 text-[15px]">{revision.company.summary}</p>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {revision.company.facts.map((f) => (
              <span key={f} className="rounded-full bg-canvas px-2.5 py-0.5 text-sm text-muted ring-1 ring-line">{f}</span>
            ))}
          </div>
        </div>
      )}

      <div className="flex items-baseline justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Why Bern</h2>
          <p className="text-sm text-muted">Keep what you want in the pitch.</p>
        </div>
        <span className="flex shrink-0 items-center gap-2 text-xs text-muted">
          {coverage.institutions.map((i) => (
            <span key={i} className="flex items-center gap-1">
              <span className={`h-2 w-2 rounded-full ${INSTITUTION[i].dot}`} />
              {INSTITUTION[i].short}
            </span>
          ))}
        </span>
      </div>

      <div className="space-y-6">
        {CATEGORIES.map(({ key, label, Icon }) => {
          const items = reasons.filter((r) => r.category === key);
          if (!items.length) return null;
          return (
            <section key={key} id={`sec-${key}`} className="scroll-mt-16">
              <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-muted">
                <Icon size={15} />
                {label}
                <span className="font-normal">{items.length}</span>
              </h3>
              <div className="space-y-2.5">
                {items.map((r) => (
                  <ReasonCard
                    key={r.id}
                    r={r}
                    n={numbered.indexOf(r.id) + 1}
                    evidence={evidence}
                    onOpen={onOpen}
                    active={activeEvidence}
                    flash={flash.has(r.id)}
                    onSelect={(s) => onSelect(r.id, s)}
                  />
                ))}
              </div>
            </section>
          );
        })}
      </div>

      {(openQuestions.length > 0 || coverage.limitations.length > 0) && (
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <HelpCircle size={15} className="text-muted" />
          {[...openQuestions, ...coverage.limitations].map((q) => (
            <span key={q} className="rounded-full bg-white px-2.5 py-0.5 text-muted ring-1 ring-line">{q}</span>
          ))}
        </div>
      )}

      {revision.similarCases && revision.similarCases.length > 0 && (
        <div id="sec-similar" className="scroll-mt-16">
          <h2 className="mb-2 flex items-center gap-2 text-lg font-semibold tracking-tight">
            Similar cases
            <span title="How similar the company needs and topics are. Not a chance of success.">
              <HelpCircle size={15} className="text-muted" />
            </span>
          </h2>
          <div className="divide-y divide-line overflow-hidden rounded-xl border border-line bg-white">
            {revision.similarCases.map((s) => (
              <Link key={s.caseId} to={`/cases/${s.caseId}`} className="flex items-center gap-4 px-4 py-3 hover:bg-canvas">
                <div className="w-28 shrink-0">
                  <div className="text-lg font-semibold tabular-nums">{s.score}%</div>
                  <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-canvas">
                    <div className="h-full rounded-full bg-ink" style={{ width: `${s.score}%` }} />
                  </div>
                </div>
                <div className="min-w-0 flex-1">
                  <div className="font-medium">{s.companyLabel}</div>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {s.shared.map((x) => (
                      <span key={x} className="rounded-full bg-canvas px-2 py-0.5 text-xs text-muted">{x}</span>
                    ))}
                  </div>
                </div>
                <span className="flex shrink-0 items-center gap-1">
                  <StatusBadge status={s.status} />
                  <CaseFlags outcome={s.outcome} />
                </span>
              </Link>
            ))}
          </div>
        </div>
      )}

      <div id="sec-search" className="scroll-mt-16 rounded-xl border border-line bg-white">
        <button onClick={() => setTraceOpen(!traceOpen)} aria-expanded={traceOpen} className="flex w-full items-center gap-2 px-4 py-3 text-sm">
          <span className="font-medium">How I searched</span>
          <span className="text-muted">
            {plural(trace.inputs.length, 'word')} → {plural(trace.terms.length, 'term')} → {plural(sourceCount, 'source')}
          </span>
          <ChevronDown size={16} className={`ml-auto text-muted transition ${traceOpen ? 'rotate-180' : ''}`} />
        </button>
        {traceOpen && (
          <div className="border-t border-line px-4 py-4">
            <SearchSankey trace={trace} evidence={evidence} onOpen={onOpen} />
          </div>
        )}
      </div>
    </div>
  );
}
