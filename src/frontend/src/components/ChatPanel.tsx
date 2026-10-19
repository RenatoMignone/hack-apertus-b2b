import { useEffect, useRef, useState } from 'react';
import { ArrowUp, PanelRightClose } from 'lucide-react';
import type { DialogueTurn, RunStage } from '../types/contract';
import RunStepper from './RunStepper';

function ClarificationAnswer({ turn, running, onAnswer }: {
  turn: DialogueTurn; running: boolean; onAnswer: (turnId: string, answer: string) => void;
}) {
  const [answer, setAnswer] = useState('');
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
        className="mt-1 w-full rounded-lg border border-line p-2 text-sm text-ink" />
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
}: {
  turns: DialogueTurn[];
  running: boolean;
  stage: RunStage;
  suggestions: string[];
  onSend: (text: string, kind: 'focus' | 'formatting') => void;
  onAnswer: (turnId: string, answer: string) => void;
  onClose: () => void;
  awaitingAnswers?: boolean;
  questionIds?: string[];
  canRewrite?: boolean;
}) {
  const [text, setText] = useState('');
  const [kind, setKind] = useState<'focus' | 'formatting'>('focus');
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => {
    end.current?.scrollIntoView({ behavior: 'smooth' });
  }, [turns.length, running]);

  const send = (t = text) => {
    if (!t.trim() || running || awaitingAnswers) return;
    onSend(t.trim(), canRewrite ? kind : 'focus');
    setText('');
  };

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex items-center gap-2 border-b border-line px-4 py-2.5">
        <span className="text-sm font-semibold">Agent</span>
        <span className="text-xs text-muted">push back or ask</span>
        <button onClick={onClose} aria-label="Close chat" title="Close chat" className="ml-auto rounded-md p-1 text-muted hover:bg-canvas hover:text-ink">
          <PanelRightClose size={17} />
        </button>
      </div>
      <div tabIndex={0} aria-label="Conversation" className="flex-1 space-y-3 overflow-y-auto p-4">
        {turns.map((t) =>
          t.role === 'operator' ? (
            <div key={t.id} className="ml-8 rounded-2xl rounded-br-sm bg-ink px-3.5 py-2 text-sm leading-relaxed text-white">
              {t.text}
            </div>
          ) : (
            <div key={t.id} className="mr-8 space-y-2">
              <div className="rounded-2xl rounded-bl-sm bg-canvas px-3.5 py-2 text-sm leading-relaxed">{t.text}</div>
              {t.followUp?.answer && <p className="text-sm text-muted">Your answer: {t.followUp.answer}</p>}
              {awaitingAnswers && (!questionIds || questionIds.includes(t.followUp?.id ?? '')) && <ClarificationAnswer turn={t} running={running} onAnswer={onAnswer} />}
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
        {canRewrite && <label className="mb-2 block text-xs text-muted">Request type
          <select aria-label="Request type" value={kind} disabled={running || awaitingAnswers}
            onChange={(event) => setKind(event.target.value as 'focus' | 'formatting')}
            className="ml-2 rounded border border-line bg-white p-1 text-ink">
            <option value="focus">Research / change focus</option>
            <option value="formatting">Rewrite existing report</option>
          </select>
        </label>}
        <div className="mb-2 flex flex-wrap gap-1.5">
          {suggestions.map((s) => (
            <button
              key={s}
              disabled={running || awaitingAnswers}
              onClick={() => send(s)}
              className="rounded-full border border-line px-2.5 py-0.5 text-xs text-muted hover:border-ink/40 hover:text-ink disabled:opacity-40"
            >
              {s}
            </button>
          ))}
        </div>
        <div className="flex items-end gap-2 rounded-xl border border-line bg-white p-2 focus-within:border-ink/40">
          <textarea
            aria-label="Message the agent"
            disabled={running || awaitingAnswers}
            maxLength={50000}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
            rows={1}
            placeholder={awaitingAnswers ? 'Answer the clarification above to continue.' : 'Push back or ask…'}
            className="flex-1 resize-none bg-transparent px-1 py-1 text-sm outline-none"
          />
          <button
            onClick={() => send()}
            disabled={!text.trim() || running || awaitingAnswers}
            className="rounded-lg bg-brand p-1.5 text-white hover:bg-brand-dark disabled:opacity-40"
            aria-label="Send"
          >
            <ArrowUp size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
