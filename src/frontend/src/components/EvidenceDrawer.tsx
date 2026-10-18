import { useEffect, useRef } from 'react';
import { ExternalLink, X } from 'lucide-react';
import type { Evidence } from '../types/contract';
import { INSTITUTION } from './ui';

/** Source quote panel. Esc closes it; focus moves in on open and back on close. */
export default function EvidenceDrawer({ ev, onClose }: { ev: Evidence; onClose: () => void }) {
  const closeBtn = useRef<HTMLButtonElement>(null);
  const opener = useRef<Element | null>(null);
  const close = useRef(onClose);
  close.current = onClose;

  // Runs once per opening; the parent's inline onClose must not re-trigger it.
  useEffect(() => {
    opener.current = document.activeElement;
    closeBtn.current?.focus();
    const esc = (e: KeyboardEvent) => e.key === 'Escape' && close.current();
    document.addEventListener('keydown', esc);
    return () => {
      document.removeEventListener('keydown', esc);
      (opener.current as HTMLElement | null)?.focus?.();
    };
  }, []);

  const i = ev.highlight ? ev.excerpt.indexOf(ev.highlight) : -1;
  return (
    <aside
      role="dialog"
      aria-label={`Source ${ev.n}: ${ev.label}`}
      className="slide-in fixed bottom-0 right-0 top-14 z-50 flex w-[min(400px,100vw)] flex-col border-l border-line bg-white shadow-xl"
    >
      <div className="flex items-center gap-2 border-b border-line px-4 py-3">
        <span className="rounded bg-ink px-1.5 text-xs font-semibold text-white">{ev.n}</span>
        <span className="flex min-w-0 items-center gap-1.5 text-sm font-semibold">
          <span className={`h-2 w-2 shrink-0 rounded-full ${INSTITUTION[ev.institution].dot}`} aria-hidden />
          <span className="truncate">{ev.label}</span>
        </span>
        <button ref={closeBtn} onClick={onClose} className="ml-auto rounded-md p-1 text-muted hover:bg-canvas hover:text-ink" aria-label="Close source (Esc)">
          <X size={18} />
        </button>
      </div>
      <div className="space-y-4 overflow-y-auto p-4 text-sm">
        <blockquote className="rounded-lg border-l-4 border-ink bg-canvas p-3 text-[15px] leading-relaxed">
          {i < 0 ? (
            ev.excerpt
          ) : (
            <>
              {ev.excerpt.slice(0, i)}
              <mark className="ev">{ev.highlight}</mark>
              {ev.excerpt.slice(i + ev.highlight!.length)}
            </>
          )}
        </blockquote>
        <p className="text-muted">{ev.relevance}</p>
        {ev.origin && <p className="rounded-lg bg-canvas p-2 text-xs text-muted">
          {ev.origin === 'web' ? 'New case research' : 'Pinned corpus'} · {ev.reviewStatus ?? 'unreviewed'} source.
          {' '}Claim support does not certify the source.
        </p>}
        <a
          href={ev.url}
          target="_blank"
          rel="noreferrer"
          title="Opens the live page, which may have changed since retrieval"
          className="inline-flex items-center gap-1.5 rounded-lg border border-line px-3 py-1.5 font-medium hover:bg-canvas"
        >
          Open page <ExternalLink size={14} aria-hidden />
        </a>
        <div className="text-xs text-muted">
          {INSTITUTION[ev.institution].label} · retrieved {ev.fetchedAt}
        </div>
      </div>
    </aside>
  );
}
