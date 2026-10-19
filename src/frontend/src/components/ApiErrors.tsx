import { useEffect, useState, useSyncExternalStore } from 'react';
import { sessionVersion, subscribeSession } from '../api/session';
import { ApiError } from '../api/httpApi';

type Notice = {message:string; requestId?:string; retryable?:boolean};
function errorNotice(reason: unknown): Notice {
  return {message:reason instanceof Error ? reason.message : 'The request could not be completed.',
    ...(reason instanceof ApiError ? {requestId:reason.requestId,retryable:reason.retryable} : {})};
}
export function reportApiError(reason: unknown) {
  const detail = errorNotice(reason);
  window.dispatchEvent(new CustomEvent('navigator-api-error', {detail}));
}

export function ErrorDetails({error}: {error:unknown}) {
  return <NoticeContent notice={errorNotice(error)} />;
}
function NoticeContent({notice}: {notice:Notice}) {
  const [copied, setCopied] = useState(false);
  return <>
    <p>{notice.message}</p>
    {notice.requestId && <div className="mt-2 text-xs">
      <p>Request ID: <code className="select-all">{notice.requestId}</code></p>
      <button className="mt-1 underline" onClick={() => {
        void navigator.clipboard.writeText(notice.requestId!).then(() => setCopied(true)).catch(() => setCopied(false));
      }}>{copied ? 'Copied request ID' : 'Copy request ID'}</button>
    </div>}
    {notice.retryable === true && <p className="mt-2 text-xs">The server marked this failure as retryable. Check current state before retrying.</p>}
  </>;
}
export default function ApiErrors() {
  const session = useSyncExternalStore(subscribeSession, sessionVersion);
  const [notice, setNotice] = useState<Notice>();
  useEffect(() => { setNotice(undefined); }, [session]);
  useEffect(() => {
    const shown = (event: Event) => { setNotice((event as CustomEvent<Notice>).detail); };
    const rejected = (event: PromiseRejectionEvent) => { event.preventDefault(); reportApiError(event.reason); };
    window.addEventListener('navigator-api-error', shown);
    window.addEventListener('unhandledrejection', rejected);
    return () => { window.removeEventListener('navigator-api-error', shown); window.removeEventListener('unhandledrejection', rejected); };
  }, []);
  return notice ? <div role="alert" className="fixed bottom-5 right-5 z-[70] max-w-md rounded-xl border border-brand/30 bg-white p-4 text-sm shadow-lg">
    <NoticeContent key={notice.requestId ?? notice.message} notice={notice} />
    <button className="mt-2 text-brand underline" onClick={() => setNotice(undefined)}>Dismiss</button>
  </div> : null;
}
