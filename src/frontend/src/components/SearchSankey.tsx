import { useEffect, useMemo, useRef, useState } from 'react';
import { sankey, sankeyLinkHorizontal, type SankeyLink, type SankeyNode } from 'd3-sankey';
import type { Evidence, SearchTrace } from '../types/contract';
import { INSTITUTION } from './ui';

type N = { id: string; label: string; col: 0 | 1 | 2; color: string; sub?: string };
type L = { source: string; target: string; value: number };
type GN = SankeyNode<N, L>;
type GL = SankeyLink<N, L>;

const ROW = 60; // vertical space per node in the tallest column
const NODE_W = 12;
const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));

/**
 * Your message → ontology terms → source entries (each extracted from a URL).
 * Nodes and flows are SVG; labels are HTML so they can wrap instead of being cut off.
 */
export default function SearchSankey({
  trace,
  evidence,
  onOpen,
}: {
  trace: SearchTrace;
  evidence: Record<string, Evidence>;
  onOpen: (evidenceId: string) => void;
}) {
  const box = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(720);
  const [hover, setHover] = useState<string | null>(null);

  useEffect(() => {
    if (!box.current) return;
    const ro = new ResizeObserver(([e]) => setWidth(e.contentRect.width));
    ro.observe(box.current);
    return () => ro.disconnect();
  }, []);

  const entryIds = useMemo(() => [...new Set(trace.links.map((l) => l.target).filter((id) => evidence[id]))], [trace, evidence]);
  const rows = Math.max(trace.inputs.length, trace.terms.length, entryIds.length);
  const height = Math.max(220, rows * ROW + 20);
  const leftW = clamp(width * 0.2, 120, 190); // space for "your words" labels
  const rightW = clamp(width * 0.28, 160, 240); // space for source labels

  const graph = useMemo(() => {
    const nodes: N[] = [
      ...trace.inputs.map((i) => ({ id: i.id, label: i.label, col: 0 as const, color: '#1a1d23' })),
      ...trace.terms.map((t) => ({ id: t.id, label: t.label, col: 1 as const, color: '#6b7280' })),
      ...entryIds.map((id) => ({
        id,
        label: evidence[id].label,
        sub: INSTITUTION[evidence[id].institution].short,
        col: 2 as const,
        color: INSTITUTION[evidence[id].institution].hex,
      })),
    ];
    const ids = new Set(nodes.map((n) => n.id));
    const links: L[] = trace.links.filter((l) => ids.has(l.source) && ids.has(l.target)).map((l) => ({ ...l }));
    if (!links.length || width < leftW + rightW + 120) return null;
    return sankey<N, L>()
      .nodeId((d) => d.id)
      .nodeWidth(NODE_W)
      .nodePadding(rows > 6 ? 16 : 24)
      .extent([
        [leftW, 10],
        [width - rightW, height - 10],
      ])({ nodes, links });
  }, [trace, evidence, entryIds, width, height, leftW, rightW, rows]);

  // Hovering a node highlights it, its neighbours and the flows between them.
  const lit = useMemo(() => {
    if (!hover || !graph) return null;
    const set = new Set([hover]);
    for (const l of graph.links) {
      const s = (l.source as GN).id;
      const t = (l.target as GN).id;
      if (s === hover) set.add(t);
      if (t === hover) set.add(s);
    }
    return set;
  }, [hover, graph]);
  const isLit = (l: GL) => !!lit && lit.has((l.source as GN).id) && lit.has((l.target as GN).id);

  const colX = (c: 0 | 1 | 2) => graph?.nodes.find((n) => n.col === c);

  return (
    <div ref={box} className="w-full">
      {graph && (
        <div className="relative" style={{ height: height + 28 }}>
          {/* Column headers, aligned with their columns */}
          <div className="absolute left-0 top-0 text-right text-xs font-semibold uppercase tracking-wide text-muted" style={{ width: (colX(0)?.x0 ?? leftW) - 12 }}>
            Your words
          </div>
          <div
            className="absolute top-0 -translate-x-1/2 text-xs font-semibold uppercase tracking-wide text-muted"
            style={{ left: ((colX(1)?.x0 ?? 0) + (colX(1)?.x1 ?? 0)) / 2 }}
          >
            Terms searched
          </div>
          <div className="absolute top-0 text-xs font-semibold uppercase tracking-wide text-muted" style={{ left: (colX(2)?.x1 ?? 0) + 12 }}>
            Sources
          </div>

          <div className="absolute inset-x-0" style={{ top: 28, height }}>
            <svg width={width} height={height} className="absolute inset-0 overflow-visible" aria-hidden>
              <g fill="none">
                {graph.links.map((l, i) => {
                  const tgt = l.target as GN;
                  const on = isLit(l);
                  return (
                    <path
                      key={i}
                      d={sankeyLinkHorizontal()(l) ?? ''}
                      stroke={tgt.col === 2 ? tgt.color : '#94a3b8'}
                      strokeWidth={Math.max(3, l.width ?? 1)}
                      strokeOpacity={lit ? (on ? 0.7 : 0.08) : tgt.col === 2 ? 0.4 : 0.22}
                      className="transition-[stroke-opacity] duration-150"
                    />
                  );
                })}
              </g>
              {graph.nodes.map((n) => (
                <rect
                  key={n.id}
                  x={n.x0}
                  y={n.y0}
                  width={(n.x1 ?? 0) - (n.x0 ?? 0)}
                  height={Math.max(4, (n.y1 ?? 0) - (n.y0 ?? 0))}
                  rx={3}
                  fill={n.color}
                  opacity={lit && !lit.has(n.id) ? 0.35 : 1}
                  onMouseEnter={() => setHover(n.id)}
                  onMouseLeave={() => setHover(null)}
                />
              ))}
            </svg>

            {/* Labels */}
            {graph.nodes.map((n) => {
              const ym = ((n.y0 ?? 0) + (n.y1 ?? 0)) / 2;
              const dim = lit && !lit.has(n.id) ? 'opacity-40' : '';
              const hoverProps = { onMouseEnter: () => setHover(n.id), onMouseLeave: () => setHover(null) };
              if (n.col === 0)
                return (
                  <div
                    key={n.id}
                    {...hoverProps}
                    className={`absolute left-0 -translate-y-1/2 pr-3 text-right text-sm font-semibold leading-tight text-ink transition-opacity ${dim}`}
                    style={{ top: ym, width: n.x0 }}
                  >
                    {n.label}
                  </div>
                );
              if (n.col === 1)
                return (
                  <div
                    key={n.id}
                    {...hoverProps}
                    title={n.label}
                    className={`absolute -translate-x-1/2 -translate-y-1/2 truncate whitespace-nowrap rounded-full bg-white px-3 py-1 text-sm font-medium leading-tight text-ink shadow-sm ring-1 ring-line transition-opacity ${dim}`}
                    style={{ top: ym, left: ((n.x0 ?? 0) + (n.x1 ?? 0)) / 2, maxWidth: Math.min(240, width - leftW - rightW) }}
                  >
                    {n.label}
                  </div>
                );
              return (
                <button
                  key={n.id}
                  {...hoverProps}
                  onFocus={() => setHover(n.id)}
                  onBlur={() => setHover(null)}
                  onClick={() => onOpen(n.id)}
                  title="Open the source quote"
                  className={`absolute -translate-y-1/2 pl-3 text-left leading-tight transition-opacity hover:text-brand ${dim}`}
                  style={{ top: ym, left: n.x1, width: rightW - 4 }}
                >
                  <span className="block text-sm font-semibold underline decoration-line underline-offset-2">{n.label}</span>
                  <span className="text-xs text-muted">{n.sub}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}
      {graph && <p className="mt-3 text-xs text-muted">Hover to trace a path. Click a source to read the quote.</p>}
    </div>
  );
}
