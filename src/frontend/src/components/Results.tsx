import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Building2, Check, ChevronDown, ChevronRight, ClipboardList, ExternalLink, FlaskConical, HelpCircle, Lightbulb, SearchX, Users } from 'lucide-react';
import type { BriefRevision, Evidence, Reason, ReasonCategory, Selection } from '../types/contract';
import { CaseFlags, INSTITUTION, StatusBadge } from './ui';
import SearchSankey from './SearchSankey';

type Open = (evidenceId: string) => void;

const plural = (n: number, word: string) => `${n} ${n === 1 ? word : word === 'query' ? 'queries' : word + 's'}`;

const CATEGORIES: { key: ReasonCategory; label: string; Icon: typeof Users }[] = [
  { key: 'people', label: 'People', Icon: Users },
  { key: 'groups', label: 'Research groups', Icon: FlaskConical },
  { key: 'projects', label: 'Projects & studies', Icon: ClipboardList },
  { key: 'infrastructure', label: 'Infrastructure & services', Icon: Building2 },
  { key: 'ideas', label: 'Ideas to explore', Icon: Lightbulb },
];

/** Structured result fields: unit hierarchy, expertise tags and fields the sources don't state. */
function Fields({ r }: { r: Reason }) {
  const path = r.entries.find((e) => e.unitPath?.length)?.unitPath;
  const expertise = [...new Set(r.entries.flatMap((e) => e.expertise ?? []))];
  const missing = r.missingFields ?? [];
  if (!path && !expertise.length && !missing.length) return null;
  return (
    <div className="mt-2 space-y-1.5">
      {path && (
        <div className="flex flex-wrap items-center gap-0.5 text-xs text-muted" aria-label="Unit">
          {path.map((u, i) => (
            <span key={u + i} className="flex items-center gap-0.5">
              {i > 0 && <ChevronRight size={11} aria-hidden />}
              {u}
            </span>
          ))}
        </div>
      )}
      {expertise.length > 0 && (
        <div className="flex flex-wrap gap-1" aria-label="Expertise">
          {expertise.map((t) => (
            <span key={t} className="rounded-md bg-canvas px-1.5 py-0.5 text-xs text-ink ring-1 ring-line">{t}</span>
          ))}
        </div>
      )}
      {missing.length > 0 && (
        <div className="text-xs text-muted">
          <span className="font-medium">Not stated in sources:</span> {missing.join(' · ')}
        </div>
      )}
    </div>
  );
}

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
  readOnly = false,
}: {
  r: Reason;
  n: number;
  evidence: Record<string, Evidence>;
  onOpen: Open;
  active?: string;
  flash: boolean;
  onSelect: (s: Selection) => void;
  readOnly?: boolean;
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
        <button disabled={readOnly} onClick={() => onSelect('none')} className="text-xs font-medium text-ink hover:underline disabled:opacity-40">Show again</button>
      </div>
    );
  }

  const sources = [...new Set([...r.line.evidenceIds, ...r.entries.flatMap((e) => e.evidenceIds)])].map((id) => evidence[id]).filter(Boolean);

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
              <span className="text-muted">{person.institutionLabel ?? INSTITUTION[person.institution].short} · </span>
              {person.role}
            </div>
          )}
          <p className="mt-0.5 text-sm text-muted">
            {r.line.text}
            <Chips ids={r.line.evidenceIds} evidence={evidence} onOpen={onOpen} active={active} />
          </p>
          <Fields r={r} />
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
                  <span className="text-muted">{e.institutionLabel ?? INSTITUTION[e.institution].short}</span>
                  <span className="font-medium">{e.name}</span>
                </span>
              ))}
            </div>
          )}
        </div>
        <div className="flex shrink-0 items-center gap-1" onClick={(e) => e.stopPropagation()}>
          <button
            aria-pressed={kept}
            disabled={readOnly}
            onClick={() => onSelect(kept ? 'none' : 'kept')}
            className={`inline-flex items-center gap-1 rounded-lg px-2 py-1 text-sm font-medium ${
              kept ? 'bg-ok text-white' : 'text-muted ring-1 ring-line hover:text-ok hover:ring-ok'
            }`}
          >
            <Check size={14} aria-hidden /> {kept ? 'Kept' : 'Keep'}
          </button>
          <button disabled={readOnly} onClick={() => onSelect('rejected')} className="rounded-lg px-2 py-1 text-sm text-muted ring-1 ring-line hover:text-bad hover:ring-bad disabled:opacity-40">
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
  readOnly = false,
}: {
  revision: BriefRevision;
  companyLabel: string;
  evidence: Record<string, Evidence>;
  onOpen: Open;
  activeEvidence?: string;
  flash: Set<string>;
  onSelect: (reasonId: string, s: Selection) => void;
  readOnly?: boolean;
}) {
  const [traceOpen, setTraceOpen] = useState(false);
  const { reasons, coverage, openQuestions, trace } = revision;
  // People she might ask the agency to introduce (hidden ones excluded, kept ones first).
  const introductions = reasons
    .filter((r) => r.category === 'people' && r.selection !== 'rejected')
    .sort((a, b) => Number(b.selection === 'kept') - Number(a.selection === 'kept'))
    .map((r) => r.entries[0])
    .filter(Boolean)
    .slice(0, 4);
  // Groups and projects are numbered as one running list; people and ideas use icons.
  const numbered = (['groups', 'projects', 'infrastructure'] as const).flatMap((c) => reasons.filter((r) => r.category === c).map((r) => r.id));
  const sourceCount = new Set(trace.links.map((l) => l.target).filter((id) => evidence[id])).size;

  if (!reasons.length) {
    return (
      <div className="mx-auto mt-12 max-w-md rounded-2xl border border-line bg-white p-8 text-center">
        <SearchX className="mx-auto text-muted" />
        <h2 className="mt-3 font-semibold">{coverage.resultKind === 'out_of_scope' ? 'Out of scope' : 'No reliable match'}</h2>
        <p className="mt-1 text-sm text-muted">{revision.emptyMessage}</p>
        {[...new Set([...openQuestions, ...coverage.limitations])].length > 0 && <ul className="mt-4 space-y-2 text-left text-sm text-muted">
          {[...new Set([...openQuestions, ...coverage.limitations])].map((item) => <li key={item}>{item}</li>)}
        </ul>}
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
                    readOnly={readOnly}
                  />
                ))}
              </div>
            </section>
          );
        })}
      </div>

      {(openQuestions.length > 0 || introductions.length > 0 || coverage.limitations.length > 0) && (
        <section id="sec-next" className="scroll-mt-16 rounded-xl border border-line bg-white p-4">
          <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold tracking-tight">
            <HelpCircle size={17} className="text-muted" aria-hidden /> Next steps
          </h2>
          <div className="grid gap-4 text-sm sm:grid-cols-2">
            {openQuestions.length > 0 && (
              <div>
                <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted">Open questions and caveats</h3>
                <ul className="list-inside list-disc space-y-1">
                  {openQuestions.map((q) => <li key={q}>{q}</li>)}
                </ul>
              </div>
            )}
            {introductions.length > 0 && (
              <div>
                <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted">Possible introductions</h3>
                <ul className="space-y-1">
                  {introductions.map((p) => (
                    <li key={p.id} className="flex items-center gap-1.5">
                      <span className={`h-2 w-2 shrink-0 rounded-full ${INSTITUTION[p.institution].dot}`} aria-hidden />
                      {p.name} <span className="text-muted">· {p.institutionLabel ?? INSTITUTION[p.institution].short}</span>
                    </li>
                  ))}
                </ul>
                <p className="mt-1.5 text-xs text-muted">Availability not confirmed. The agency makes contact.</p>
              </div>
            )}
          </div>
          {coverage.limitations.some((q) => !openQuestions.includes(q)) && <p className="mt-3 text-xs text-muted">{coverage.limitations.filter((q) => !openQuestions.includes(q)).join(' ')}</p>}
        </section>
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
                  <div className="text-lg font-semibold tabular-nums">{s.score}/100</div>
                  <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-canvas">
                    <div className="h-full rounded-full bg-ink" style={{ width: `${s.score}/100` }} />
                  </div>
                </div>
                <div className="min-w-0 flex-1">
                  <div className="font-medium">{s.companyLabel}</div>
                  {s.indexedAt && <p className="text-xs text-muted">Indexed {new Date(s.indexedAt).toLocaleDateString()} · Needs similarity, not success probability</p>}
                  {!!s.differences?.length && <p className="text-xs text-muted">Additional current needs: {s.differences.join('; ')}</p>}
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

      {trace.inputs.length || trace.terms.length || trace.links.length ? <div id="sec-search" className="scroll-mt-16 rounded-xl border border-line bg-white">
        <button onClick={() => setTraceOpen(!traceOpen)} aria-expanded={traceOpen} className="flex w-full items-center gap-2 px-4 py-3 text-sm">
          <span className="font-medium">How I searched</span>
          <span className="text-muted">
            {plural(trace.inputs.length, 'input')} → {plural(trace.terms.length, 'query')} → {plural(sourceCount, 'source')}
          </span>
          <ChevronDown size={16} className={`ml-auto text-muted transition ${traceOpen ? 'rotate-180' : ''}`} />
        </button>
        {traceOpen && (
          <div className="border-t border-line px-4 py-4">
            <SearchSankey trace={trace} evidence={evidence} onOpen={onOpen} />
          </div>
        )}
      </div> : <p id="sec-search" className="text-sm text-muted">Source passages are available on each reason. A detailed search trace is not available.</p>}
    </div>
  );
}
