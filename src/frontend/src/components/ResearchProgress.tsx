import { useEffect, useState, useSyncExternalStore } from 'react';
import { Badge, Card, Spinner } from '@radix-ui/themes';
import { Database, Globe, Sparkles } from 'lucide-react';
import { runProgress, subscribeProgress } from '../api/progress';
import type { RunStage } from '../types/contract';
import RunStepper from './RunStepper';

function label(step: string) {
  const key = step.split('.')[0];
  return ({ taxonomy: 'Loading the topic vocabulary', interpret: 'Apertus is interpreting your request',
    retrieve: 'Searching the corpus: embeddings, keywords, vectors and reranking',
    discover: 'Discovering public web sources', fetch: 'Fetching and reading public pages',
    register: 'Checking duplicates and saving case evidence', extract: 'Apertus is extracting cited facts',
    assess: 'Apertus is checking factual support', evidence: 'Verifying source passages',
    persist_extraction: 'Saving evidence-backed facts', propose_pack: 'Preparing the evidence pack',
    pack: 'Freezing the evidence pack', draft: 'Apertus is writing and checking the report',
    replan: 'Apertus is refining the search queries' } as Record<string, string>)[key] ?? 'Processing verified evidence';
}
export default function ResearchProgress({ caseId, stage }: { caseId: string; stage: RunStage }) {
  const progress = useSyncExternalStore(subscribeProgress, () => runProgress(caseId));
  const [now, setNow] = useState(Date.now());
  useEffect(() => { const timer = setInterval(() => setNow(Date.now()), 1000); return () => clearInterval(timer); }, []);
  const active = progress?.activity ?? [];
  return <Card size="4" className="research-progress">
    <div className="mb-6 flex items-center justify-between gap-3">
      <h2 className="text-lg font-semibold">Research in progress</h2>
      <Badge color="red" variant="soft"><Spinner size="1" /> {progress?.status === 'queued' ? 'Queued' : 'Working'}</Badge>
    </div>
    <RunStepper stage={stage} />
    <div className="mt-6 space-y-3 border-t border-line pt-5" aria-live="polite">
      {active.length ? active.map((item) => <div key={item.step} className="flex items-start gap-3 text-sm">
        {item.step.startsWith('retrieve') ? <Database size={16} className="mt-0.5 shrink-0 text-unibe" /> : /^(discover|fetch)/.test(item.step) ? <Globe size={16} className="mt-0.5 shrink-0 text-artorg" /> : <Sparkles size={16} className="mt-0.5 shrink-0 text-brand" />}
        <span className="flex-1">{label(item.step)}</span>
        <span className="shrink-0 tabular-nums text-muted">{Math.max(0, Math.floor((now-Date.parse(item.started_at))/1000))}s</span>
      </div>) : <p className="text-sm text-muted">{progress?.status === 'queued' ? 'Waiting for the worker to pick up this case.' : 'Waiting for the next server progress update.'}</p>}
    </div>
    <p className="mt-5 text-xs text-muted">You can open another case and return here. Research continues in the background.</p>
  </Card>;
}
