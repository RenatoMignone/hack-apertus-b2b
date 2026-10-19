import { useState } from 'react';
import { FileText, Presentation, X } from 'lucide-react';
import type { BriefRevision, CaseDetail } from '../types/contract';
import { buildExportModel, download, fileSlug, kept as keptOf } from '../export/model';
import { useToast } from './Toast';
import { api, apiMode } from '../api';
import { reportApiError } from './ApiErrors';
import { assertExportAllowed } from '../export/policy';
import { serverFormats } from '../api/session';

type Format = 'pdf' | 'pptx';

/**
 * Exports only the items she kept (✓ Keep), as a PDF brief with the agency logo or
 * as an editable demo PowerPoint built from the partner template. Connected PDF
 * export uses the server's exact-revision approval and authenticated download.
 */
export default function ExportModal({ detail, revision, onClose }: { detail: CaseDetail; revision: BriefRevision; onClose: () => void }) {
  const [busy, setBusy] = useState<Format | null>(null);
  const toast = useToast();
  const kept = keptOf(revision);
  const unreviewed = revision.reasons.filter((r) => r.selection === 'none').length;
  const formats = detail.exportFormats ?? serverFormats();
  const pdfAvailable = apiMode === 'mock' || formats.includes('pdf');

  const run = async (format: Format) => {
    setBusy(format);
    try {
      assertExportAllowed(revision, apiMode, format, formats.filter((f): f is Format => f === 'pdf' || f === 'pptx'));
      if (apiMode === 'http') {
        const { filename, blob } = await api.exportDeck(detail.case.id, {
          resultId: revision.id, resultHash: revision.resultHash!,
        }, format);
        download(blob, filename);
        toast(`Downloaded ${filename}`);
        onClose();
        return;
      }
      const model = buildExportModel(detail, revision);
      const slug = fileSlug(detail.case.companyLabel);
      if (format === 'pdf') {
        const { buildPdf } = await import('../export/pdf');
        download(await buildPdf(model), `why-bern-${slug}.pdf`);
        toast(`Downloaded why-bern-${slug}.pdf`);
      } else {
        const { buildPptx } = await import('../export/pptx');
        download(await buildPptx(model), `why-bern-${slug}.pptx`);
        toast(`Downloaded why-bern-${slug}.pptx`);
      }
      onClose();
    } catch (e) {
      if (apiMode === 'http') reportApiError(e);
      else toast('Export failed. Please try again.');
    } finally {
      setBusy(null);
    }
  };

  const option = (format: Format, Icon: typeof FileText, title: string, hint: string) => (
    <button
      onClick={() => run(format)}
      disabled={!kept.length || unreviewed > 0 || busy !== null || (format === 'pdf' && !pdfAvailable) || (apiMode === 'http' && !revision.resultHash)}
      className="flex w-full items-start gap-3 rounded-xl border border-line p-3 text-left hover:border-ink/40 hover:bg-canvas disabled:cursor-not-allowed disabled:opacity-50"
    >
      <Icon size={20} className="mt-0.5 shrink-0 text-brand" aria-hidden />
      <span>
        <span className="block font-medium">{busy === format ? 'Building…' : title}</span>
        <span className="block text-sm text-muted">{hint}</span>
      </span>
    </button>
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/30 p-4" onClick={onClose}>
      <div role="dialog" aria-label="Export" className="w-full max-w-md rounded-2xl bg-white p-5 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center">
          <h2 className="font-semibold">Export for {detail.case.companyLabel}</h2>
          <button onClick={onClose} className="ml-auto rounded-md p-1 text-muted hover:bg-canvas" aria-label="Close">
            <X size={18} />
          </button>
        </div>

        {kept.length ? (
          <>
            <p className="mt-3 text-sm text-muted">Includes the {kept.length} item{kept.length === 1 ? '' : 's'} you kept, with their sources:</p>
            <ul className="mt-2 max-h-40 space-y-1 overflow-y-auto text-sm">
              {kept.map((r) => (
                <li key={r.id} className="flex gap-2">
                  <span className="text-ok" aria-hidden>✓</span>
                  {r.headline}
                </li>
              ))}
            </ul>
          </>
        ) : (
          <p className="mt-3 rounded-lg bg-warn-soft px-3 py-2 text-sm text-warn">Keep at least one item (✓ Keep) on the case page first.</p>
        )}

        <div className="mt-4 space-y-2">
          {unreviewed > 0 && <p className="text-sm text-muted">Keep or hide the {unreviewed} remaining item{unreviewed === 1 ? '' : 's'} before exporting.</p>}
          {!pdfAvailable && <p className="text-sm text-muted">PDF export is unavailable on the connected server.</p>}
          {option('pdf', FileText, 'PDF brief', 'Short company-facing brief with the agency logo and a source appendix.')}
          {(apiMode === 'mock' || formats.includes('pptx')) && option('pptx', Presentation, 'PowerPoint (agency template)', apiMode === 'mock' ? 'Editable demo slides.' : 'Reviewed content and source passages in editable agency slides.')}
        </div>
      </div>
    </div>
  );
}
