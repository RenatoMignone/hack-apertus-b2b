import { ExternalLink, X } from 'lucide-react';
import type { Evidence } from '../types/contract';
import { INSTITUTION } from './ui';

export default function EvidenceDrawer({ ev, onClose }: { ev: Evidence; onClose: () => void }) {
  const i = ev.highlight ? ev.excerpt.indexOf(ev.highlight) : -1;
  return (
    <div className="slide-in absolute inset-0 z-20 flex flex-col bg-white">
      <div className="flex items-center gap-2 border-b border-line px-4 py-3">
        <span className="rounded bg-ink px-1.5 text-xs font-semibold text-white">{ev.n}</span>
        <span className="flex items-center gap-1.5 text-sm font-semibold">
          <span className={`h-2 w-2 rounded-full ${INSTITUTION[ev.institution].dot}`} />
          {ev.label}
        </span>
        <button onClick={onClose} className="ml-auto rounded-md p-1 text-muted hover:bg-canvas hover:text-ink" aria-label="Close">
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
        <a
          href={ev.url}
          target="_blank"
          rel="noreferrer"
          title="Opens the live page, which may have changed since retrieval"
          className="inline-flex items-center gap-1.5 rounded-lg border border-line px-3 py-1.5 font-medium hover:bg-canvas"
        >
          Open page <ExternalLink size={14} />
        </a>
        <div className="text-xs text-muted">
          {INSTITUTION[ev.institution].label} · retrieved {ev.fetchedAt}
        </div>
      </div>
    </div>
  );
}
