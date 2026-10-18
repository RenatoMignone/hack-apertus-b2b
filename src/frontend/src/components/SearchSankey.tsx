import { useEffect, useMemo, useRef, useState } from 'react';
import { sankey, sankeyLinkHorizontal, type SankeyLink, type SankeyNode } from 'd3-sankey';
import type { Evidence, SearchTrace } from '../types/contract';
import { INSTITUTION } from './ui';

type N = { id: string; label: string; col: 0 | 1 | 2; color: string };
type L = { source: string; target: string; value: number };

const LEFT = 120;
const RIGHT = 200;

/** Your message → ontology terms → source entries (each extracted from a URL). */
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
  const [width, setWidth] = useState(700);
  const [hover, setHover] = useState<string | null>(null);

  useEffect(() => {
    if (!box.current) return;
    const ro = new ResizeObserver(([e]) => setWidth(e.contentRect.width));
    ro.observe(box.current);
    return () => ro.disconnect();
  }, []);

  const entryIds = useMemo(() => [...new Set(trace.links.map((l) => l.target).filter((id) => evidence[id]))], [trace, evidence]);
  const height = Math.max(trace.inputs.length, trace.terms.length, entryIds.length) * 30 + 20;

  const graph = useMemo(() => {
    const nodes: N[] = [
      ...trace.inputs.map((i) => ({ id: i.id, label: i.label, col: 0 as const, color: '#1a1d23' })),
      ...trace.terms.map((t) => ({ id: t.id, label: t.label, col: 1 as const, color: '#8a919c' })),
      ...entryIds.map((id) => ({ id, label: evidence[id].label, col: 2 as const, color: INSTITUTION[evidence[id].institution].hex })),
    ];
    const ids = new Set(nodes.map((n) => n.id));
    const links: L[] = trace.links.filter((l) => ids.has(l.source) && ids.has(l.target)).map((l) => ({ ...l }));
    if (!links.length || width < LEFT + RIGHT + 100) return null;
    return sankey<N, L>()
      .nodeId((d) => d.id)
      .nodeWidth(8)
      .nodePadding(12)
      .extent([
        [LEFT, 10],
        [width - RIGHT, height - 10],
      ])({ nodes, links });
  }, [trace, evidence, entryIds, width, height]);

  const linked = (l: SankeyLink<N, L>, id: string | null) =>
    !!id && ((l.source as SankeyNode<N, L>).id === id || (l.target as SankeyNode<N, L>).id === id);

  return (
    <div ref={box} className="w-full">
      <div className="mb-2 grid grid-cols-3 text-xs font-medium uppercase tracking-wide text-muted">
        <span>Your words</span>
        <span className="text-center">Terms searched</span>
        <span className="text-right">Sources</span>
      </div>
      {graph && (
        <svg width={width} height={height} className="overflow-visible">
          <g fill="none">
            {graph.links.map((l, i) => {
              const tgt = l.target as SankeyNode<N, L>;
              const on = linked(l, hover);
              return (
                <path
                  key={i}
                  d={sankeyLinkHorizontal()(l) ?? ''}
                  stroke={tgt.col === 2 ? tgt.color : '#b9bec7'}
                  strokeWidth={Math.max(2, l.width ?? 1)}
                  strokeOpacity={hover ? (on ? 0.65 : 0.08) : 0.3}
                  className="transition-[stroke-opacity]"
                />
              );
            })}
          </g>
          {graph.nodes.map((n) => {
            const x0 = n.x0 ?? 0;
            const x1 = n.x1 ?? 0;
            const y0 = n.y0 ?? 0;
            const y1 = n.y1 ?? 0;
            const ym = (y0 + y1) / 2;
            const clickable = n.col === 2;
            return (
              <g
                key={n.id}
                onMouseEnter={() => setHover(n.id)}
                onMouseLeave={() => setHover(null)}
                onClick={clickable ? () => onOpen(n.id) : undefined}
                className={clickable ? 'cursor-pointer' : undefined}
              >
                <rect x={x0} y={y0} width={x1 - x0} height={Math.max(2, y1 - y0)} rx={2} fill={n.color} />
                <text
                  x={n.col === 0 ? x0 - 8 : x1 + 8}
                  y={ym}
                  dy="0.35em"
                  textAnchor={n.col === 0 ? 'end' : 'start'}
                  fontSize={12.5}
                  fontWeight={500}
                  fill={n.col === 1 ? '#3a404a' : '#1a1d23'}
                  stroke="#ffffff"
                  strokeWidth={5}
                  strokeLinejoin="round"
                  paintOrder="stroke"
                  className={clickable ? 'hover:underline' : undefined}
                >
                  <title>{n.label}</title>
                  {n.col === 2 && n.label.length > 26 ? n.label.slice(0, 25) + '…' : n.label}
                </text>
              </g>
            );
          })}
        </svg>
      )}
    </div>
  );
}
