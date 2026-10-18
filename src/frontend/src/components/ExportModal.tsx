import { useState } from 'react';
import { Download, X } from 'lucide-react';
import { api } from '../api';
import type { BriefRevision, CaseDetail } from '../types/contract';
import { Button } from './ui';
import { useToast } from './Toast';
import { apiMode } from '../api';
import { reportApiError } from './ApiErrors';

export default function ExportModal({ detail, revision, onClose }: { detail: CaseDetail; revision: BriefRevision; onClose: () => void }) {
  const [busy, setBusy] = useState(false);
  const toast = useToast();
  const kept = revision.reasons.filter((r) => r.selection === 'kept');
  const unreviewed = revision.reasons.filter((r) => r.selection === 'none').length;

  const run = async () => {
    setBusy(true);
    try {
    const { filename, blob } = await api.exportDeck(detail.case.id, revision.resultHash ? {
      resultId: revision.id, resultHash: revision.resultHash } : undefined);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    toast(`Downloaded ${filename}`);
    onClose();
    } catch (error) { reportApiError(error); }
    finally { setBusy(false); }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/30 p-4" onClick={onClose}>
      <div className="w-full max-w-sm rounded-2xl bg-white p-5 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center">
          <h2 className="font-semibold">{apiMode === 'http' ? 'Export reviewed PDF' : 'Export demo brief'}</h2>
          <button onClick={onClose} className="ml-auto rounded-md p-1 text-muted hover:bg-canvas" aria-label="Close">
            <X size={18} />
          </button>
        </div>
        {kept.length ? (
          <ul className="mt-3 space-y-1 text-sm">
            {kept.map((r) => (
              <li key={r.id} className="flex gap-2">
                <span className="text-ok">✓</span>
                {r.headline}
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-sm text-muted">Keep at least one reason first (✓).</p>
        )}
        {unreviewed > 0 && <p className="mt-3 text-sm text-muted">Review all {unreviewed} remaining reason(s) before exporting.</p>}
        <div className="mt-5 flex justify-end gap-2">
          <Button onClick={onClose}>Cancel</Button>
          <Button variant="primary" onClick={run} disabled={!kept.length || unreviewed > 0 || busy}>
            <Download size={15} /> {busy ? 'Building…' : 'Download'}
          </Button>
        </div>
      </div>
    </div>
  );
}
