import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { Callout, Card, Spinner, Text } from '@radix-ui/themes';
import { ArrowLeft, Check } from 'lucide-react';
import { forgetPendingCase, pendingCase } from '../api/pendingCase';
import { useTitle } from '../components/ui';

export default function StartingCasePage() {
  const { requestId = '' } = useParams();
  const navigate = useNavigate();
  const pending = pendingCase(requestId);
  const [error, setError] = useState('');
  const [seconds, setSeconds] = useState(0);
  useTitle('Preparing case');
  useEffect(() => {
    let alive = true;
    const timer = setInterval(() => setSeconds((s) => s + 1), 1000);
    if (pending) void pending.promise.then((detail) => {
      if (!alive) return;
      forgetPendingCase(requestId);
      navigate(`/cases/${detail.case.id}`, { replace: true, state: { run: true } });
    }).catch((reason) => { if (alive) setError(reason instanceof Error ? reason.message : 'Could not prepare the case.'); });
    return () => { alive = false; clearInterval(timer); };
  }, [pending, requestId, navigate]);
  return <div className="mx-auto max-w-3xl px-6 py-12">
    <Link to="/cases" className="mb-8 inline-flex items-center gap-2 text-sm text-muted"><ArrowLeft size={16} /> My cases</Link>
    <h1 className="text-3xl font-semibold tracking-tight">Preparing your research</h1>
    <p className="mt-3 mb-7 text-muted">Your request is being saved and the available institutional sources are being pinned for this case.</p>
    {!pending || error ? <Callout.Root color="red"><Callout.Text>
      {error || 'This preparation session is no longer available. Check My cases before submitting again.'}
      {' '}<Link to="/cases">Open My cases</Link>
    </Callout.Text></Callout.Root> : <Card size="4" aria-live="polite">
      <div className="flex items-center gap-4"><Spinner size="3" /><div>
        <Text as="p" weight="medium">Preparing the evidence snapshot</Text>
        <Text as="p" size="2" color="gray">{seconds}s elapsed · you can leave this page; accepted work continues on the server.</Text>
      </div></div>
      <div className="mt-6 flex items-center gap-2 text-sm text-muted"><Check size={16} /> Company context submitted</div>
      {seconds >= 15 && <p className="mt-4 text-sm text-muted">Still waiting for the server to finish preparation. No need to send your prompt again.</p>}
    </Card>}
  </div>;
}
