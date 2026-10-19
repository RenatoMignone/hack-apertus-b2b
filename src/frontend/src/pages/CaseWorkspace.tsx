import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';
import { ArrowLeft, ChevronDown, Download, MessageSquare } from 'lucide-react';
import { api, apiMode } from '../api';
import type { BriefRevision, CaseDetail, CaseStatus, RunStage, Selection } from '../types/contract';
import ChatPanel from '../components/ChatPanel';
import EvidenceDrawer from '../components/EvidenceDrawer';
import ExportModal from '../components/ExportModal';
import Results from '../components/Results';
import CaseDataControls from '../components/CaseDataControls';
import RunStepper from '../components/RunStepper';
import { useToast } from '../components/Toast';
import { Button, CaseFlags, Skeleton, StatusSelect, useTitle } from '../components/ui';
import { reportApiError } from '../components/ApiErrors';

function useWide(query = '(min-width: 1100px)') {
  const [wide, setWide] = useState(() => window.matchMedia(query).matches);
  useEffect(() => {
    const m = window.matchMedia(query);
    const on = () => setWide(m.matches);
    m.addEventListener('change', on);
    return () => m.removeEventListener('change', on);
  }, [query]);
  return wide;
}

function readChatPref() {
  try {
    return localStorage.getItem('nav-chat-open') !== 'false';
  } catch {
    return true;
  }
}

/** Compact "v2 ▾" button; the menu lists every version with its change note. */
function VersionMenu({ detail, current, onPick }: { detail: CaseDetail; current: BriefRevision; onPick: (id: string) => void }) {
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLDivElement>(null);
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
  const latest = detail.revisions[detail.revisions.length - 1];
  return (
    <div ref={box} className="relative">
      <button
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        aria-label={`Version ${current.version}. Change version`}
        title={current.changeNote}
        className="flex items-center gap-1 rounded-lg border border-line bg-white px-2.5 py-1.5 text-sm hover:bg-canvas"
      >
        v{current.version}
        {current.id !== latest.id && <span className="text-xs text-warn">(older)</span>}
        <ChevronDown size={14} aria-hidden />
      </button>
      {open && (
        <div className="absolute right-0 top-10 z-30 w-64 rounded-xl border border-line bg-white p-1 shadow-lg">
          {[...detail.revisions].reverse().map((r) => (
            <button
              key={r.id}
              onClick={() => (onPick(r.id), setOpen(false))}
              className={`flex w-full items-start gap-2 rounded-md px-2.5 py-1.5 text-left text-sm hover:bg-canvas ${r.id === current.id ? 'bg-canvas' : ''}`}
            >
              <span className="font-medium">v{r.version}</span>
              <span className="min-w-0 flex-1 text-muted">{r.changeNote}</span>
              {r.id === latest.id && <span className="text-xs text-ok">latest</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/** Sticky row of links to the sections present on this case page. */
function JumpBar({ revision }: { revision: BriefRevision }) {
  const has = (c: string) => revision.reasons.some((r) => r.category === c);
  const links = [
    has('people') && ['people', 'People'],
    has('groups') && ['groups', 'Groups'],
    has('projects') && ['projects', 'Projects'],
    has('infrastructure') && ['infrastructure', 'Infrastructure'],
    has('ideas') && ['ideas', 'Ideas'],
    (revision.openQuestions.length > 0 || revision.coverage.limitations.length > 0 || has('people')) && ['next', 'Follow-up'],
    (revision.similarCases?.length ?? 0) > 0 && ['similar', 'Similar cases'],
    revision.reasons.length > 0 && ['search', 'How I searched'],
  ].filter(Boolean) as [string, string][];
  if (links.length < 2) return null;
  return (
    <nav aria-label="Sections" className="sticky top-0 z-10 -mx-6 mb-4 flex gap-1.5 overflow-x-auto border-b border-line bg-canvas/95 px-6 py-2 backdrop-blur">
      {links.map(([id, label]) => (
        <a key={id} href={`#sec-${id}`} className="shrink-0 rounded-full bg-white px-3 py-1 text-sm text-muted ring-1 ring-line hover:text-ink">
          {label}
        </a>
      ))}
    </nav>
  );
}

/** Chat shortcuts that match this case instead of fixed strings. */
function suggestionsFor(revision?: BriefRevision): string[] {
  if (!revision?.reasons.length) return ['Explain simpler'];
  const idea = revision.reasons.find((r) => r.category === 'ideas')?.entries[0]?.name;
  const group = revision.reasons.find((r) => r.category === 'groups')?.entries[0]?.name;
  return ['Make it shorter', idea && `Exclude ${idea}`, group && `Focus on ${group}`, 'Can we contact them?'].filter(Boolean) as string[];
}

export default function CaseWorkspace() {
  const { id = '' } = useParams();
  const location = useLocation();
  const toast = useToast();
  const wide = useWide();
  const [detail, setDetail] = useState<CaseDetail | null | undefined>(undefined);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState('');
  const [stage, setStage] = useState<RunStage>('interpreting');
  const [drawer, setDrawer] = useState<string | null>(null);
  const [flash, setFlash] = useState<Set<string>>(new Set());
  const [exportOpen, setExportOpen] = useState(false);
  const [started, setStarted] = useState(false);
  const [viewedRevisionId, setViewedRevisionId] = useState<string>();
  const [selecting, setSelecting] = useState(false);
  const activeCase = useRef(id);
  activeCase.current = id;
  const [chatPref, setChatPref] = useState(readChatPref);
  const [narrowChat, setNarrowChat] = useState(false);
  const [unread, setUnread] = useState(false);
  const seenTurns = useRef(0);
  useTitle(detail?.case.companyLabel);

  const chatOpen = wide ? chatPref : narrowChat;
  const setChatOpen = (open: boolean) => {
    if (wide) {
      setChatPref(open);
      try {
        localStorage.setItem('nav-chat-open', String(open));
      } catch {
        // ignore
      }
    } else setNarrowChat(open);
    if (open) setUnread(false);
  };

  useEffect(() => {
    let alive = true;
    setStarted(false);
    setViewedRevisionId(undefined);
    setSelecting(false);
    setExportOpen(false);
    setRunning(false); setError('');
    setDrawer(null);
    setDetail(undefined);
    api.getCase(id).then((data) => { if (alive) setDetail(data); }).catch((reason) => {
      if (alive) setError(reason instanceof Error ? reason.message : 'Cannot load this case.');
    });
    return () => { alive = false; };
  }, [id]);

  const failed = (reason: unknown) => {
    if (activeCase.current !== id) return;
    setRunning(false);
    setError(reason instanceof Error ? reason.message : 'The request could not be completed.');
    void api.getCase(id).then((value) => { if (activeCase.current === id) setDetail(value); }).catch(reportApiError);
  };

  // Show an unread dot when the agent replies while the chat is closed.
  useEffect(() => {
    const n = detail?.turns.length ?? 0;
    if (n > seenTurns.current && !chatOpen && seenTurns.current > 0) setUnread(true);
    seenTurns.current = n;
  }, [detail?.turns.length, chatOpen]);

  // A freshly created case runs its first search here.
  useEffect(() => {
    const wantsRun = (location.state as { run?: boolean } | null)?.run;
    if (!detail || started) return;
    const active = detail.currentRun && ['queued', 'running'].includes(detail.currentRun.status);
    if (!active && !(wantsRun && !detail.currentRun && !detail.revisions.length)) return;
    setStarted(true);
    setRunning(true);
    api.runCase(detail.case.id, (next) => { if (activeCase.current === id) setStage(next); }).then((d) => {
      if (activeCase.current !== id) return;
      setDetail(d);
      setRunning(false);
    }).catch(failed);
  }, [detail, location.state, started]);

  const revision = useMemo(
    () => detail?.revisions.find((r) => r.id === (viewedRevisionId ?? detail.currentRevisionId)),
    [detail, viewedRevisionId],
  );

  const highlight = useCallback((ids: string[]) => {
    if (!ids.length) return;
    setFlash(new Set(ids));
    setTimeout(() => document.getElementById(`reason-${ids[0]}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' }), 50);
    setTimeout(() => setFlash(new Set()), 3300);
  }, []);

  const afterAgent = (d: CaseDetail) => {
    if (activeCase.current !== d.case.id) return;
    setViewedRevisionId(undefined);
    setDetail(d);
    setRunning(false);
    const rev = d.revisions.find((r) => r.id === d.currentRevisionId);
    if (rev) highlight(rev.changedReasonIds);
  };

  if (detail === undefined)
    return (
      <div className="mx-auto max-w-3xl space-y-3 px-6 py-8">
        {error && <p role="alert" className="text-brand">{error}</p>}
        <Skeleton className="h-28" />
        <Skeleton className="h-20" />
        <Skeleton className="h-20" />
      </div>
    );
  if (detail === null)
    return (
      <div className="p-10 text-center text-muted">
        Case not found. <Link to="/cases" className="text-brand">Back to my cases</Link>
      </div>
    );

  const send = (text: string, kind: 'focus' | 'formatting') => {
    setDetail({ ...detail, turns: [...detail.turns, { id: 'pending', role: 'operator', text, createdAt: new Date().toISOString() }] });
    setRunning(true);
    setStage('interpreting');
    setError('');
    api.sendMessage(detail.case.id, text, setStage, kind).then(afterAgent).catch(failed);
  };
  const answer = (turnId: string, a: string) => {
    setRunning(true);
    setStage('interpreting');
    setError('');
    api.answerFollowUp(detail.case.id, turnId, a, setStage).then(afterAgent).catch(failed);
  };
  const select = async (reasonId: string, s: Selection) => {
    if (selecting || running || revision?.id !== detail.currentRevisionId) return;
    const r = revision?.reasons.find((x) => x.id === reasonId);
    const prev = r?.selection ?? 'none';
    const expected = revision?.resultHash ? { resultId: revision.id, resultHash: revision.resultHash } : undefined;
    setSelecting(true);
    try {
      const updated = await api.setSelection(detail.case.id, reasonId, s, expected);
      if (activeCase.current !== updated.case.id) return;
      setDetail(updated);
      if (s === 'kept') toast('Kept for the pitch');
      if (s === 'rejected') toast(`Hidden: ${r?.headline ?? 'item'}`, () => api.setSelection(detail.case.id, reasonId, prev, expected).then((value) => {
        if (activeCase.current === value.case.id) setDetail(value);
      }));
    } catch (reason) { reportApiError(reason); }
    finally { setSelecting(false); }
  };
  const setStatus = (s: CaseStatus) => api.setStatus(detail.case.id, s).then((value) => {
    if (activeCase.current === value.case.id) setDetail(value);
  });
  const kept = revision?.reasons.filter((r) => r.selection === 'kept').length ?? 0;
  const historical = !!revision && revision.id !== detail.currentRevisionId;
  const awaitingAnswers = detail.currentRun?.status === 'waiting_for_input' ||
    (apiMode === 'mock' && detail.turns.some((turn) => turn.followUp && !turn.followUp.answer));
  const retry = () => {
    setError(''); setRunning(true);
    void api.runCase(detail.case.id, setStage).then(afterAgent).catch(failed);
  };

  const chat = (
    <ChatPanel
      turns={detail.turns}
      running={running}
      awaitingAnswers={awaitingAnswers}
      questionIds={detail.currentRun?.questions?.map((question) => question.id)}
      canRewrite={!!detail.currentRevisionId}
      stage={stage}
      suggestions={suggestionsFor(revision)}
      onSend={send}
      onAnswer={answer}
      onClose={() => setChatOpen(false)}
    />
  );

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex min-w-0 items-center gap-3 border-b border-line bg-white px-4 py-2.5 lg:px-5">
        <Link to="/cases" className="shrink-0 rounded-md p-1 text-muted hover:bg-canvas hover:text-ink" aria-label="Back to my cases">
          <ArrowLeft size={18} />
        </Link>
        <h1 className="min-w-0 truncate font-semibold" title={detail.case.companyLabel}>{detail.case.companyLabel}</h1>
        <span className="shrink-0">
          <StatusSelect status={detail.case.status} onChange={setStatus} />
        </span>
        <span className="hidden shrink-0 gap-1 sm:flex">
          <CaseFlags outcome={detail.case.outcome} onHold={detail.case.onHold} />
        </span>
        {revision && (
          <div className="ml-auto flex shrink-0 items-center gap-2">
            {detail.revisions.length > 1 && (
              <VersionMenu detail={detail} current={revision} onPick={setViewedRevisionId} />
            )}
            <span title={kept ? undefined : 'Keep or hide every item, keeping at least one, to export'}>
              <Button variant="primary" disabled={historical || running || selecting} onClick={() => setExportOpen(true)}>
                <Download size={15} aria-hidden /> Export{kept ? ` (${kept})` : ''}
              </Button>
            </span>
          </div>
        )}
      </div>

      {(error || detail.currentRun?.status === 'failed') && <div role="alert" className="border-b border-line bg-white px-6 py-3 text-sm text-brand">
        {error || 'Research stopped before a report could be published.'}
        {!running && <button className="ml-3 underline" onClick={retry}>{detail.currentRun?.pack_id ? 'Retry report from existing evidence' : 'Retry / resume research'}</button>}
      </div>}
      {awaitingAnswers && <div role="status" className="border-b border-line bg-white px-6 py-3 text-sm">
        Research needs your answer. <button className="text-brand underline" onClick={() => setChatOpen(true)}>Open clarification questions</button>
      </div>}
      {historical && <p className="border-b border-line bg-white px-6 py-3 text-sm text-muted">Viewing an older report. Selections and export are available on the current report.
        <button className="ml-2 text-brand underline" onClick={() => setViewedRevisionId(undefined)}>Show current report</button></p>}

      <div className="relative flex min-h-0 flex-1">
        <div className="min-w-0 flex-1 overflow-y-auto" id="case-scroll">
          <div className="mx-auto max-w-3xl px-6 pb-16 pt-4">
            <CaseDataControls key={`${detail.case.id}:${detail.inputId}`} detail={detail}
              busy={running || selecting || awaitingAnswers || historical} onBusy={setRunning} onChange={setDetail} onStage={setStage} />
            {revision && <JumpBar revision={revision} />}
            {!revision && running && (
              <div className="mx-auto mt-10 max-w-xs rounded-2xl border border-line bg-white p-6">
                <RunStepper stage={stage} />
              </div>
            )}
            {!revision && !running && (
              <p className="mt-10 text-center text-sm text-muted">
                No brief yet for this case. <Link to="/cases/new" className="font-medium text-brand">Start a new case</Link>
              </p>
            )}
            {revision && (
              <Results
                revision={revision}
                companyLabel={detail.case.companyLabel}
                evidence={detail.evidence}
                onOpen={setDrawer}
                activeEvidence={drawer ?? undefined}
                flash={flash}
                onSelect={select}
                readOnly={historical || running || selecting}
              />
            )}
          </div>
        </div>

        {/* Wide screens: chat is a column. Narrow screens: an overlay drawer. */}
        {chatOpen && wide && <aside aria-label="Agent chat" className="flex w-[360px] shrink-0 flex-col border-l border-line bg-white xl:w-[400px]">{chat}</aside>}
        {chatOpen && !wide && (
          <>
            <div className="fixed inset-0 z-30 bg-ink/20" onClick={() => setChatOpen(false)} aria-hidden />
            <aside aria-label="Agent chat" className="slide-in fixed bottom-0 right-0 top-14 z-40 flex w-[min(400px,100vw)] flex-col bg-white shadow-xl">
              {chat}
            </aside>
          </>
        )}
        {!chatOpen && (
          <button
            onClick={() => setChatOpen(true)}
            className="fixed bottom-5 right-5 z-30 flex items-center gap-2 rounded-full bg-ink px-4 py-2.5 text-sm font-medium text-white shadow-lg hover:bg-ink/90"
          >
            <MessageSquare size={16} aria-hidden /> Chat with the agent
            {unread && <span className="h-2.5 w-2.5 rounded-full bg-brand ring-2 ring-white" aria-label="New reply" />}
          </button>
        )}
      </div>

      {drawer && detail.evidence[drawer] && <EvidenceDrawer ev={detail.evidence[drawer]} onClose={() => setDrawer(null)} />}
      {exportOpen && revision && <ExportModal detail={detail} revision={revision} onClose={() => setExportOpen(false)} />}
    </div>
  );
}
