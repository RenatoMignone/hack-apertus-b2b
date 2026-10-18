import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowUp } from 'lucide-react';
import { api } from '../api';

const EXAMPLES: { label: string; text: string }[] = [
  {
    label: 'Glucose sensor',
    text: 'GlucoWave builds a needle-free wearable glucose sensor and needs partners for clinical studies and algorithms. Most early users are women; I think DCB studied diabetes and the menstrual cycle.',
  },
  {
    label: 'Insulin pump',
    text: 'European insulin pump maker wants to add closed-loop automated insulin delivery and is looking at Bern for R&D.',
  },
  { label: 'Out of scope', text: 'Grain trading company looking for commodity partners in Bern.' },
];

export default function NewCasePage() {
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  const submit = async () => {
    if (!text.trim() || busy) return;
    setBusy(true);
    const c = await api.createCase(text.trim());
    navigate(`/cases/${c.case.id}`, { state: { run: true } });
  };

  return (
    <div className="flex h-full items-start justify-center overflow-auto px-6 pt-[14vh]">
      <div className="w-full max-w-2xl">
        <h1 className="text-center text-3xl font-semibold tracking-tight">Tell me about the company</h1>

        <div className="mt-8 rounded-2xl border border-line bg-white p-3 shadow-sm focus-within:border-ink/40">
          <textarea
            autoFocus
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) submit();
            }}
            rows={5}
            placeholder="What they do, what they need, keywords, any Bern groups you suspect…"
            className="w-full resize-none bg-transparent px-2 py-1 text-[15px] leading-relaxed outline-none placeholder:text-muted/60"
          />
          <div className="flex items-center justify-between px-2 pt-1">
            <span className="text-xs text-muted">Public info only</span>
            <button
              onClick={submit}
              disabled={!text.trim() || busy}
              className="inline-flex items-center gap-1.5 rounded-lg bg-brand px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-dark disabled:opacity-40"
            >
              Search <ArrowUp size={15} />
            </button>
          </div>
        </div>

        <div className="mt-4 flex justify-center gap-2">
          {EXAMPLES.map((e) => (
            <button
              key={e.label}
              onClick={() => setText(e.text)}
              className="rounded-full border border-line bg-white px-3 py-1 text-sm text-muted hover:border-ink/30 hover:text-ink"
            >
              {e.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
