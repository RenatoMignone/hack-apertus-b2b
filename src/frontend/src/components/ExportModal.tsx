import { useState } from 'react';
import { FileText, Presentation, X } from 'lucide-react';
import type { BriefRevision, CaseDetail } from '../types/contract';
import { buildExportModel, download, fileSlug, kept as keptOf } from '../export/model';
import { useToast } from './Toast';

type Format = 'pdf' | 'pptx';

/**
 * Exports only the items she kept (✓ Keep), as a PDF brief with the agency logo or
 * as an editable PowerPoint built from the partner template. Files are generated
 * in the browser; nothing is sent anywhere.
 */
export default function ExportModal({ detail, revision, onClose }: { detail: CaseDetail; revision: BriefRevision; onClose: () => void }) {
  const [busy, setBusy] = useState<Format | null>(null);
  const toast = useToast();
  const kept = keptOf(revision);

  const run = async (format: Format) => {
    setBusy(format);
    try {
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
      console.error(e);
      toast('Export failed. Please try again.');
    } finally {
      setBusy(null);
    }
  };

  const option = (format: Format, Icon: typeof FileText, title: string, hint: string) => (
    <button
      onClick={() => run(format)}
      disabled={!kept.length || busy !== null}
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
          {option('pdf', FileText, 'PDF brief', 'Short company-facing brief with the agency logo and a source appendix.')}
          {option('pptx', Presentation, 'PowerPoint (agency template)', 'Editable slides in the agency design, ready to adjust.')}
        </div>
      </div>
    </div>
  );
}
