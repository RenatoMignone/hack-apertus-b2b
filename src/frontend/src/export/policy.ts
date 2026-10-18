import type { BriefRevision } from '../types/contract';

export type ExportFormat = 'pdf' | 'pptx';

/** HTTP formats must have a server-side review/export implementation. */
export function assertExportAllowed(revision: BriefRevision, mode: 'http' | 'mock', format: ExportFormat) {
  if (!revision.reasons.some((r) => r.selection === 'kept') || revision.reasons.some((r) => r.selection === 'none')) {
    throw new Error('Review every item and keep at least one before exporting.');
  }
  if (mode === 'http' && (format !== 'pdf' || !revision.resultHash)) {
    throw new Error('This format is not available for a reviewed backend report.');
  }
}
