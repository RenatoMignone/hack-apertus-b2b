import { Check, Loader2 } from 'lucide-react';
import type { RunStage } from '../types/contract';

const STEPS: { key: RunStage; label: string }[] = [
  { key: 'interpreting', label: 'Reading' },
  { key: 'searching', label: 'Searching sources' },
  { key: 'validating', label: 'Checking sources' },
  { key: 'drafting', label: 'Writing' },
];

export default function RunStepper({ stage, compact = false }: { stage: RunStage; compact?: boolean }) {
  const idx = stage === 'done' ? STEPS.length : STEPS.findIndex((s) => s.key === stage);
  return (
    <ol className={compact ? 'space-y-1.5 text-xs' : 'space-y-3 text-sm'}>
      {STEPS.map((s, i) => {
        const done = i < idx;
        const active = i === idx;
        return (
          <li key={s.key} className={`flex items-center gap-2.5 ${done || active ? 'text-ink' : 'text-muted/50'} ${active ? 'font-medium' : ''}`}>
            <span
              className={`flex shrink-0 items-center justify-center rounded-full ${compact ? 'h-4 w-4' : 'h-6 w-6'} ${
                done ? 'bg-ok text-white' : active ? 'bg-brand text-white' : 'border border-line'
              }`}
            >
              {done ? <Check size={compact ? 10 : 14} /> : active ? <Loader2 size={compact ? 10 : 14} className="animate-spin" /> : null}
            </span>
            {s.label}
          </li>
        );
      })}
    </ol>
  );
}
