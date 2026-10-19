import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowUp, Lock } from 'lucide-react';
import { api } from '../api';
import { HERO_PROMPT } from '../mocks/cases';
import { useTitle } from '../components/ui';
import { reportApiError } from '../components/ApiErrors';

// The first example is the demo's hero case: written in everyday words, so the
// "How I searched" Sankey shows the bridge to scientific terms.
const EXAMPLES: { label: string; text: string }[] = [
  { label: 'HelioSense (wearable)', text: HERO_PROMPT },
  {
    label: 'Insulin pump',
    text: 'European insulin pump maker wants to add closed-loop automated insulin delivery and is looking at Bern for R&D.',
  },
  { label: 'Out of scope', text: 'Grain trading company looking for commodity partners in Bern.' },
];

export default function NewCasePage() {
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const [pending, setPending] = useState<string | null>(null);
  const box = useRef<HTMLTextAreaElement>(null);
  const navigate = useNavigate();
  // Back to the text box after an example, so Ctrl + Enter submits it.
  const fill = (value: string) => {
    setText(value);
    setPending(null);
    box.current?.focus();
  };
  useTitle('New case');

  const submit = async () => {
    if (!text.trim() || busy) return;
    setBusy(true);
    try {
      const c = await api.createCase(text.trim());
      navigate(`/cases/${c.case.id}`, { state: { run: true } });
    } catch (error) { reportApiError(error); }
    finally { setBusy(false); }
  };

  return (
    <div className="flex h-full items-start justify-center overflow-auto px-6 pt-[14vh]">
      <div className="w-full max-w-2xl">
        <h1 className="text-center text-3xl font-semibold tracking-tight">Tell me about the company</h1>

        <div className="mt-8 rounded-2xl border border-line bg-white p-3 shadow-sm focus-within:border-ink/40">
          <textarea
            ref={box}
            autoFocus
            aria-label="Company description"
            disabled={busy}
            maxLength={50000}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) submit();
            }}
            rows={5}
            placeholder="What they do, what they need, keywords, any Bern groups you suspect…"
            className="w-full resize-none bg-transparent px-2 py-1 text-[15px] leading-relaxed outline-none placeholder:text-muted/60"
          />
          <div className="flex items-center gap-3 px-2 pt-1">
            <span className="flex items-center gap-1.5 text-xs text-muted">
              <Lock size={13} aria-hidden /> Public information only. No confidential documents.
            </span>
            <span className="ml-auto hidden text-xs text-muted sm:inline">Ctrl + Enter</span>
            <button
              onClick={submit}
              disabled={!text.trim() || busy}
              className="inline-flex items-center gap-1.5 rounded-lg bg-brand px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-dark disabled:opacity-40"
            >
              {busy ? 'Starting…' : 'Start'} <ArrowUp size={15} aria-hidden />
            </button>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
          <span className="text-sm text-muted">Try an example:</span>
          {EXAMPLES.map((e) => (
            <button
              key={e.label}
              disabled={busy}
              onClick={() => (text.trim() && text !== e.text ? setPending(e.text) : fill(e.text))}
              className="rounded-full border border-line bg-white px-3 py-1 text-sm text-muted hover:border-ink/30 hover:text-ink"
            >
              {e.label}
            </button>
          ))}
        </div>
        {pending && (
          <div className="mt-3 flex items-center justify-center gap-2 text-sm">
            <span className="text-muted">Replace your text with the example?</span>
            <button onClick={() => fill(pending)} className="font-medium text-brand hover:underline">Replace</button>
            <button onClick={() => setPending(null)} className="text-muted hover:text-ink">Keep mine</button>
          </div>
        )}
      </div>
    </div>
  );
}
