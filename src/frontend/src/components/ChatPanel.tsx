import { useEffect, useRef, useState, type Dispatch, type SetStateAction } from 'react';
import { ArrowUp, PanelRightClose } from 'lucide-react';
import type { DialogueTurn, RunStage } from '../types/contract';
import RunStepper from './RunStepper';

/** A chat shortcut: a short chip label and the full instruction it sends. */
export type Suggestion = { label: string; text: string };

/** Operator bubble; long messages (like the first brief) start clamped to three lines. */
function OperatorBubble({ text }: { text: string }) {
  const long = text.length > 220;
  const [open, setOpen] = useState(false);
  return (
    <div className="ml-8 rounded-2xl rounded-br-sm bg-ink px-3.5 py-2 text-sm leading-relaxed text-white">
      <p className={long && !open ? 'line-clamp-3' : undefined}>{text}</p>
      {long && <button onClick={() => setOpen(!open)} className="mt-1 text-xs text-white/70 underline hover:text-white">
        {open ? 'Show less' : 'Show more'}
      </button>}
    </div>
  );
}

function ClarificationAnswer({ turn, running, onAnswer, draft, onDraft }: {
  turn: DialogueTurn; running: boolean; onAnswer: (turnId: string, answer: string) => void;
  draft?: string; onDraft?: (value:string) => void;
}) {
  const [localAnswer, setLocalAnswer] = useState('');
  const answer = draft ?? localAnswer;
  const setAnswer = onDraft ?? setLocalAnswer;
  if (!turn.followUp || turn.followUp.answer) return null;
  return <form className="space-y-2" onSubmit={(event) => {
    event.preventDefault();
    if (answer.trim() && !running) onAnswer(turn.id, answer.trim());
  }}>
    <div className="flex flex-wrap gap-1.5">
      {turn.followUp.choices.map((choice) => <button type="button" key={choice} disabled={running}
        onClick={() => onAnswer(turn.id, choice)} className="rounded-full border border-brand/40 px-3 py-1 text-sm text-brand disabled:opacity-40">{choice}</button>)}
    </div>
    <label className="block text-xs text-muted">Your answer
      <textarea aria-label={`Answer: ${turn.followUp.question}`} value={answer} disabled={running}
        maxLength={10000} onChange={(event) => setAnswer(event.target.value)} rows={2}
        className="mt-1 w-full rounded-lg border border-line p-2 text-sm text-ink focus:border-ink/40" />
    </label>
    <button type="submit" disabled={running || !answer.trim()}
      className="rounded-lg bg-brand px-3 py-1.5 text-sm text-white disabled:opacity-40">Submit answer</button>
  </form>;
}

export default function ChatPanel({
  turns,
  running,
  stage,
  suggestions,
  onSend,
  onAnswer,
  onClose,
  awaitingAnswers = false,
  questionIds,
  canRewrite = false,
  draft, onDraftChange, answerDrafts, onAnswerDraft,
}: {
  turns: DialogueTurn[];
  running: boolean;
  stage: RunStage;
  suggestions: Suggestion[];
  onSend: (text: string, kind: 'focus' | 'formatting') => Promise<boolean>;
  onAnswer: (turnId: string, answer: string) => void;
  onClose: () => void;
  awaitingAnswers?: boolean;
  questionIds?: string[];
  canRewrite?: boolean;
  draft?: string; onDraftChange?: Dispatch<SetStateAction<string>>;
  answerDrafts?: Record<string,string>; onAnswerDraft?: (id:string,value:string) => void;
}) {
  const [localText, setLocalText] = useState('');
  const text = draft ?? localText;
  const setText = onDraftChange ?? setLocalText;
  const [kind, setKind] = useState<'focus' | 'formatting'>('focus');
  const end = useRef<HTMLDivElement>(null);
  const box = useRef<HTMLTextAreaElement>(null);
  const locked = running || awaitingAnswers;

  useEffect(() => {
    end.current?.scrollIntoView({ behavior: 'smooth' });
  }, [turns.length, running]);

  // Grow with the text up to about eight lines, then scroll.
  useEffect(() => {
    const el = box.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 180) + 'px';
  }, [text]);

  const sending = useRef(false);
  const send = async (t = text) => {
    if (!t.trim() || running || awaitingAnswers || sending.current) return;
    sending.current = true;
    try {
      const accepted = await onSend(t.trim(), canRewrite ? kind : 'focus');
      if (accepted) setText(current => current === t ? '' : current);
    } finally { sending.current = false; }
  };

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex items-center gap-2 border-b border-line px-4 py-2.5">
        <span className="text-sm font-semibold">Agent</span>
        <button onClick={onClose} aria-label="Close chat" title="Close chat" className="ml-auto rounded-md p-1 text-muted hover:bg-canvas hover:text-ink">
          <PanelRightClose size={17} />
        </button>
      </div>
      <div tabIndex={0} aria-label="Conversation" className="flex-1 space-y-3 overflow-y-auto p-4">
        {turns.map((t) =>
          t.role === 'operator' ? (
            <OperatorBubble key={t.id} text={t.text} />
          ) : (
            <div key={t.id} className="mr-8 space-y-2">
              <div className="rounded-2xl rounded-bl-sm bg-canvas px-3.5 py-2 text-sm leading-relaxed">{t.text}</div>
              {t.followUp?.answer && <p className="text-sm text-muted">Your answer: {t.followUp.answer}</p>}
              {awaitingAnswers && (!questionIds || questionIds.includes(t.followUp?.id ?? '')) && <ClarificationAnswer turn={t} running={running} onAnswer={onAnswer} draft={answerDrafts?.[t.id]} onDraft={onAnswerDraft ? value => onAnswerDraft(t.id,value) : undefined} />}
            </div>
          ),
        )}
        {running && (
          <div className="mr-8 rounded-2xl rounded-bl-sm bg-canvas px-3.5 py-3">
            <RunStepper stage={stage} compact />
          </div>
        )}
        <div ref={end} />
      </div>

      <div className="border-t border-line p-3">
        {/* Shortcuts only while the box is empty, on one line. */}
        {!text && suggestions.length > 0 && (
          <div className="no-scrollbar mb-2 flex gap-1.5 overflow-x-auto">
            {suggestions.slice(0, 3).map((s) => (
              <button
                key={s.label}
                title={s.text === s.label ? undefined : s.text}
                disabled={locked}
                onClick={() => send(s.text)}
                className="shrink-0 rounded-full border border-line bg-white px-2.5 py-1 text-xs text-ink hover:border-ink/40 hover:bg-canvas disabled:opacity-40"
              >
                {s.label}
              </button>
            ))}
          </div>
        )}
        <div className="rounded-xl border border-line bg-white p-2 focus-within:border-ink/40">
          <textarea
            ref={box}
            aria-label="Message the agent"
            disabled={locked}
            maxLength={50000}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
            rows={2}
            placeholder={awaitingAnswers ? 'Answer the question above to continue.' : 'Ask, refine or push back…'}
            className="block w-full resize-none bg-transparent px-1 py-1 text-sm outline-none"
          />
          <div className="mt-1 flex items-center gap-2">
            {canRewrite && (
              <div role="radiogroup" aria-label="Request type" className="flex rounded-lg bg-canvas p-0.5 text-xs">
                {([['focus', 'Research', 'Search again or change the focus'], ['formatting', 'Rewrite', 'Rewrite the current report without new research']] as const).map(([value, label, hint]) => (
                  <button
                    key={value}
                    role="radio"
                    aria-checked={kind === value}
                    title={hint}
                    disabled={locked}
                    onClick={() => setKind(value)}
                    className={`rounded-md px-2 py-0.5 ${kind === value ? 'bg-white font-medium text-ink shadow-sm' : 'text-muted hover:text-ink'} disabled:opacity-40`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            )}
            <button
              onClick={() => send()}
              disabled={!text.trim() || locked}
              className="ml-auto rounded-lg bg-brand p-1.5 text-white hover:bg-brand-dark disabled:opacity-40"
              aria-label="Send"
            >
              <ArrowUp size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
