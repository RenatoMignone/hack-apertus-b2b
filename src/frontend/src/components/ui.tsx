import { useEffect, type ReactNode } from 'react';
import type { CaseOutcome, CaseStatus, Institution } from '../types/contract';

/** Sets the browser tab title, e.g. "My desk · Navigator". */
export function useTitle(title: string | undefined) {
  useEffect(() => {
    document.title = title ? `${title} · Navigator` : 'Bern Expertise Navigator';
  }, [title]);
}

export const STATUS: Record<CaseStatus, { label: string; cls: string; dot: string }> = {
  researching: { label: 'To research', cls: 'bg-unibe-soft text-unibe', dot: 'bg-unibe' },
  in_review: { label: 'In review', cls: 'bg-warn-soft text-warn', dot: 'bg-warn' },
  pitch_sent: { label: 'Pitch sent', cls: 'bg-artorg-soft text-artorg', dot: 'bg-artorg' },
  closed: { label: 'Closed', cls: 'bg-other-soft text-ink', dot: 'bg-ink' },
};

export const STATUS_ORDER: CaseStatus[] = ['researching', 'in_review', 'pitch_sent', 'closed'];

export const OUTCOME: Record<CaseOutcome, { label: string; cls: string }> = {
  visit: { label: 'Visit', cls: 'bg-ok-soft text-ok' },
  no_interest: { label: 'No interest', cls: 'bg-bad-soft text-bad' },
};

/** Small badges for a case's outcome and on-hold flag. */
export function CaseFlags({ outcome, onHold }: { outcome?: CaseOutcome; onHold?: boolean }) {
  return (
    <>
      {outcome && <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${OUTCOME[outcome].cls}`}>{OUTCOME[outcome].label}</span>}
      {onHold && <span className="rounded-full bg-other-soft px-2 py-0.5 text-xs font-medium text-muted">On hold</span>}
    </>
  );
}

export function Skeleton({ className = '' }: { className?: string }) {
  return <div className={`animate-pulse rounded-xl bg-line/60 ${className}`} />;
}

export const INSTITUTION: Record<Institution, { label: string; short: string; dot: string; hex: string }> = {
  UniBE: { label: 'University of Bern', short: 'UniBE', dot: 'bg-unibe', hex: '#2557c7' },
  ARTORG: { label: 'ARTORG Center', short: 'ARTORG', dot: 'bg-artorg', hex: '#0b6e65' },
  DCB: { label: 'Diabetes Center Berne', short: 'DCB', dot: 'bg-dcb', hex: '#b45f06' },
  Other: { label: 'Other', short: 'Other', dot: 'bg-other', hex: '#6b7280' },
};

export function StatusBadge({ status, caret }: { status: CaseStatus; caret?: boolean }) {
  return (
    <span className={`inline-flex items-center whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS[status].cls}`}>
      {STATUS[status].label}
      {caret && ' ▾'}
    </span>
  );
}

/** A status pill that is also a native select. */
export function StatusSelect({ status, onChange }: { status: CaseStatus; onChange: (s: CaseStatus) => void }) {
  return (
    <label className="relative inline-block cursor-pointer">
      <StatusBadge status={status} caret />
      <select
        aria-label="Status"
        value={status}
        onChange={(e) => onChange(e.target.value as CaseStatus)}
        className="absolute inset-0 cursor-pointer opacity-0"
      >
        {STATUS_ORDER.map((s) => (
          <option key={s} value={s}>{STATUS[s].label}</option>
        ))}
      </select>
    </label>
  );
}

export function Button({
  children,
  onClick,
  variant = 'secondary',
  disabled,
  type = 'button',
}: {
  children: ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary';
  disabled?: boolean;
  type?: 'button' | 'submit';
}) {
  const v = variant === 'primary' ? 'bg-brand text-white hover:bg-brand-dark border-transparent' : 'bg-white text-ink border-line hover:bg-canvas';
  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={`inline-flex items-center justify-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-50 ${v}`}
    >
      {children}
    </button>
  );
}

export function timeAgo(iso: string) {
  const d = (Date.now() - new Date(iso).getTime()) / 1000;
  if (d < 3600) return 'today';
  if (d < 86400) return `${Math.floor(d / 3600)} h ago`;
  return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
}
