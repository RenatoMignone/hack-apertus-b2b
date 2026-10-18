import { useEffect, useRef, useState } from 'react';
import { ArrowUp } from 'lucide-react';
import type { DialogueTurn, RunStage } from '../types/contract';
import RunStepper from './RunStepper';

const SUGGESTIONS = ['Make it shorter', 'Exclude nutrition', 'Explain simpler'];

export default function ChatPanel({
  turns,
  running,
  stage,
  onSend,
  onAnswer,
}: {
  turns: DialogueTurn[];
  running: boolean;
  stage: RunStage;
  onSend: (text: string) => void;
  onAnswer: (turnId: string, answer: string) => void;
}) {
  const [text, setText] = useState('');
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => {
    end.current?.scrollIntoView({ behavior: 'smooth' });
  }, [turns.length, running]);

  const send = (t = text) => {
    if (!t.trim() || running) return;
    onSend(t.trim());
    setText('');
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {turns.map((t) =>
          t.role === 'operator' ? (
            <div key={t.id} className="ml-8 rounded-2xl rounded-br-sm bg-ink px-3.5 py-2 text-sm leading-relaxed text-white">
              {t.text}
            </div>
          ) : (
            <div key={t.id} className="mr-8 space-y-2">
              <div className="rounded-2xl rounded-bl-sm bg-canvas px-3.5 py-2 text-sm leading-relaxed">{t.text}</div>
              {t.followUp && (
                <div className="flex flex-wrap gap-1.5">
                  {t.followUp.choices.map((c) => {
                    const chosen = t.followUp!.answer === c;
                    return (
                      <button
                        key={c}
                        disabled={!!t.followUp!.answer || running}
                        onClick={() => onAnswer(t.id, c)}
                        className={`rounded-full border px-3 py-1 text-sm ${
                          chosen ? 'border-brand bg-brand text-white' : 'border-brand/40 text-brand hover:bg-brand-soft disabled:opacity-40'
                        }`}
                      >
                        {c}
                      </button>
                    );
                  })}
                </div>
              )}
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
        <div className="mb-2 flex flex-wrap gap-1.5">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              disabled={running}
              onClick={() => send(s)}
              className="rounded-full border border-line px-2.5 py-0.5 text-xs text-muted hover:border-ink/40 hover:text-ink disabled:opacity-40"
            >
              {s}
            </button>
          ))}
        </div>
        <div className="flex items-end gap-2 rounded-xl border border-line bg-white p-2 focus-within:border-ink/40">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
            rows={1}
            placeholder="Push back or ask…"
            className="flex-1 resize-none bg-transparent px-1 py-1 text-sm outline-none"
          />
          <button
            onClick={() => send()}
            disabled={!text.trim() || running}
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
