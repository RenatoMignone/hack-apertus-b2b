import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';
import { ArrowLeft, Download } from 'lucide-react';
import { api } from '../api';
import type { CaseDetail, CaseStatus, RunStage, Selection } from '../types/contract';
import ChatPanel from '../components/ChatPanel';
import EvidenceDrawer from '../components/EvidenceDrawer';
import ExportModal from '../components/ExportModal';
import Results from '../components/Results';
import RunStepper from '../components/RunStepper';
import { Button, StatusSelect } from '../components/ui';

export default function CaseWorkspace() {
  const { id = '' } = useParams();
  const location = useLocation();
  const [detail, setDetail] = useState<CaseDetail | null | undefined>(undefined);
  const [running, setRunning] = useState(false);
  const [stage, setStage] = useState<RunStage>('interpreting');
  const [drawer, setDrawer] = useState<string | null>(null);
  const [flash, setFlash] = useState<Set<string>>(new Set());
  const [exportOpen, setExportOpen] = useState(false);
  const [started, setStarted] = useState(false);

  useEffect(() => {
    setStarted(false);
    setDrawer(null);
    api.getCase(id).then(setDetail);
  }, [id]);

  // A freshly created case runs its first search here.
  useEffect(() => {
    const wantsRun = (location.state as { run?: boolean } | null)?.run;
    if (!detail || started || !wantsRun || detail.revisions.length) return;
    setStarted(true);
    setRunning(true);
    api.runCase(detail.case.id, setStage).then((d) => {
      setDetail(d);
      setRunning(false);
    });
  }, [detail, location.state, started]);

  const revision = useMemo(
    () => detail?.revisions.find((r) => r.id === detail.currentRevisionId) ?? detail?.revisions[detail.revisions.length - 1],
    [detail],
  );

  const highlight = useCallback((ids: string[]) => {
    if (!ids.length) return;
    setFlash(new Set(ids));
    setTimeout(() => document.getElementById(`reason-${ids[0]}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' }), 50);
    setTimeout(() => setFlash(new Set()), 3300);
  }, []);

  const afterAgent = (d: CaseDetail) => {
    setDetail(d);
    setRunning(false);
    const rev = d.revisions.find((r) => r.id === d.currentRevisionId);
    if (rev) highlight(rev.changedReasonIds);
  };

  if (detail === undefined) return null;
  if (detail === null)
    return (
      <div className="p-10 text-center text-muted">
        Case not found. <Link to="/" className="text-brand">Back</Link>
      </div>
    );

  const send = (text: string) => {
    setDetail({ ...detail, turns: [...detail.turns, { id: 'pending', role: 'operator', text, createdAt: new Date().toISOString() }] });
    setRunning(true);
    setStage('interpreting');
    api.sendMessage(detail.case.id, text, setStage).then(afterAgent);
  };
  const answer = (turnId: string, a: string) => {
    setRunning(true);
    setStage('interpreting');
    api.answerFollowUp(detail.case.id, turnId, a, setStage).then(afterAgent);
  };
  const select = (reasonId: string, s: Selection) => api.setSelection(detail.case.id, reasonId, s).then(setDetail);
  const setStatus = (s: CaseStatus) => api.setStatus(detail.case.id, s).then(setDetail);
  const kept = revision?.reasons.filter((r) => r.selection === 'kept').length ?? 0;
  const latestId = detail.revisions[detail.revisions.length - 1]?.id;

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex items-center gap-3 border-b border-line bg-white px-5 py-2.5">
        <Link to="/cases" className="rounded-md p-1 text-muted hover:bg-canvas hover:text-ink" aria-label="Back to cases">
          <ArrowLeft size={18} />
        </Link>
        <span className="truncate font-semibold">{detail.case.companyLabel}</span>
        <StatusSelect status={detail.case.status} onChange={setStatus} />
        {revision && (
          <div className="ml-auto flex items-center gap-2">
            {detail.revisions.length > 1 && (
              <select
                aria-label="Version"
                value={revision.id}
                onChange={(e) => api.setCurrentRevision(detail.case.id, e.target.value).then(setDetail)}
                className="rounded-lg border border-line bg-white px-2 py-1.5 text-sm outline-none"
              >
                {[...detail.revisions].reverse().map((r) => (
                  <option key={r.id} value={r.id}>
                    v{r.version} · {r.changeNote}{r.id === latestId ? ' (latest)' : ''}
                  </option>
                ))}
              </select>
            )}
            <Button variant="primary" onClick={() => setExportOpen(true)}>
              <Download size={15} /> Export{kept ? ` (${kept})` : ''}
            </Button>
          </div>
        )}
      </div>

      <div className="flex min-h-0 flex-1">
        <div className="min-w-0 flex-1 overflow-y-auto">
          <div className="mx-auto max-w-3xl px-6 py-8">
            {!revision && running && (
              <div className="mx-auto mt-10 max-w-xs rounded-2xl border border-line bg-white p-6">
                <RunStepper stage={stage} />
              </div>
            )}
            {!revision && !running && (
              <p className="mt-10 text-center text-sm text-muted">
                No demo brief for this case. <Link to="/cases/case-glucowave" className="font-medium text-brand">See an example</Link>
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
              />
            )}
          </div>
        </div>

        <aside className="relative flex w-[300px] shrink-0 flex-col border-l border-line bg-white xl:w-[380px]">
          <ChatPanel turns={detail.turns} running={running && !!revision} stage={stage} onSend={send} onAnswer={answer} />
          {drawer && detail.evidence[drawer] && <EvidenceDrawer ev={detail.evidence[drawer]} onClose={() => setDrawer(null)} />}
        </aside>
      </div>

      {exportOpen && revision && <ExportModal detail={detail} revision={revision} onClose={() => setExportOpen(false)} />}
    </div>
  );
}
