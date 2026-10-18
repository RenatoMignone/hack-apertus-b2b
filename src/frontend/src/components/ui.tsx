import type { ReactNode } from 'react';
import type { CaseStatus, Institution } from '../types/contract';

export const STATUS: Record<CaseStatus, { label: string; cls: string; dot: string }> = {
  draft: { label: 'Draft', cls: 'bg-other-soft text-other', dot: 'bg-other' },
  researching: { label: 'Researching', cls: 'bg-unibe-soft text-unibe', dot: 'bg-unibe' },
  in_review: { label: 'In review', cls: 'bg-warn-soft text-warn', dot: 'bg-warn' },
  pitch_sent: { label: 'Pitch sent', cls: 'bg-artorg-soft text-artorg', dot: 'bg-artorg' },
  closed_visit: { label: 'Closed · visit', cls: 'bg-ok-soft text-ok', dot: 'bg-ok' },
  closed_no_interest: { label: 'Closed · no interest', cls: 'bg-bad-soft text-bad', dot: 'bg-bad' },
  on_hold: { label: 'On hold', cls: 'bg-other-soft text-muted', dot: 'bg-line' },
};

export const STATUS_ORDER: CaseStatus[] = ['draft', 'researching', 'in_review', 'pitch_sent', 'closed_visit', 'closed_no_interest', 'on_hold'];

export const INSTITUTION: Record<Institution, { label: string; short: string; dot: string; hex: string }> = {
  UniBE: { label: 'University of Bern', short: 'UniBE', dot: 'bg-unibe', hex: '#2557c7' },
  ARTORG: { label: 'ARTORG Center', short: 'ARTORG', dot: 'bg-artorg', hex: '#0f8a7e' },
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
}: {
  children: ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary';
  disabled?: boolean;
}) {
  const v = variant === 'primary' ? 'bg-brand text-white hover:bg-brand-dark border-transparent' : 'bg-white text-ink border-line hover:bg-canvas';
  return (
    <button
      type="button"
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
