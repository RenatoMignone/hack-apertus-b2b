import { Dialog, IconButton } from '@radix-ui/themes';
import { useEffect, useRef, useState } from 'react';
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
export default function ExportModal({ detail, revision, onClose, onConflict }: { detail: CaseDetail; revision: BriefRevision; onClose: () => void; onConflict: (error: unknown) => Promise<void> }) {
  const alive = useRef(true), pending = useRef(false);
  useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);
  const [busy, setBusy] = useState<Format | null>(null);
  const toast = useToast();
  const kept = keptOf(revision);
  const unreviewed = revision.reasons.filter((r) => r.selection === 'none').length;
  const formats = detail.exportFormats ?? serverFormats();
  const pdfAvailable = apiMode === 'mock' || formats.includes('pdf');

  const run = async (format: Format) => {
    if (pending.current) return;
    pending.current = true; setBusy(format);
    try {
      assertExportAllowed(revision, apiMode, format, formats.filter((f): f is Format => f === 'pdf' || f === 'pptx'));
      if (!alive.current) return;
      if (apiMode === 'http') {
        const { filename, blob } = await api.exportDeck(detail.case.id, {
          resultId: revision.id, resultHash: revision.resultHash!,
        }, format);
        if (!alive.current) return;
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
      if (!alive.current) return;
      if (apiMode === 'http') { reportApiError(e); await onConflict(e); }
      else toast('Export failed. Please try again.');
    } finally {
      pending.current = false; if (alive.current) setBusy(null);
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
    <Dialog.Root open onOpenChange={(open) => { if (!open && !busy) onClose(); }}>
      <Dialog.Content maxWidth="480px" aria-describedby={undefined} onEscapeKeyDown={(event) => { if (busy) event.preventDefault(); }} onPointerDownOutside={(event) => { if (busy) event.preventDefault(); }}>
        <div className="flex items-center">
          <Dialog.Title className="mb-0">Export for {detail.case.companyLabel}</Dialog.Title>
          <IconButton variant="ghost" color="gray" disabled={busy !== null} onClick={onClose} className="ml-auto" aria-label="Close">
            <X size={18} />
          </IconButton>
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
      </Dialog.Content>
    </Dialog.Root>
  );
}
