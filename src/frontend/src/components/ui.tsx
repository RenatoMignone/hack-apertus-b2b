import { Button as RadixButton, Select, Badge } from '@radix-ui/themes';
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
  return <Badge size="2" variant="soft" color={status === 'researching' ? 'blue' : status === 'in_review' ? 'amber' : status === 'pitch_sent' ? 'teal' : 'gray'}>
    {STATUS[status].label}{caret && ' ▾'}
  </Badge>;
}

/** A status pill that is also a native select. */
export function StatusSelect({ status, onChange }: { status: CaseStatus; onChange: (s: CaseStatus) => void }) {
  return <Select.Root value={status} onValueChange={(value) => onChange(value as CaseStatus)}>
    <Select.Trigger aria-label="Status" variant="soft" />
    <Select.Content>{STATUS_ORDER.map((s) => <Select.Item key={s} value={s}>{STATUS[s].label}</Select.Item>)}</Select.Content>
  </Select.Root>;
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
  return <RadixButton type={type} disabled={disabled} onClick={onClick}
    variant={variant === 'primary' ? 'solid' : 'surface'} color={variant === 'primary' ? 'red' : 'gray'}>
    {children}
  </RadixButton>;
}

export function timeAgo(iso: string) {
  const d = (Date.now() - new Date(iso).getTime()) / 1000;
  if (d < 3600) return 'today';
  if (d < 86400) return `${Math.floor(d / 3600)} h ago`;
  return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
}
