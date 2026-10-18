import { useEffect, useState } from 'react';

export function reportApiError(reason: unknown) {
  window.dispatchEvent(new CustomEvent('navigator-api-error', {
    detail: reason instanceof Error ? reason.message : 'The request could not be completed.',
  }));
}

export default function ApiErrors() {
  const [message, setMessage] = useState('');
  useEffect(() => {
    const shown = (event: Event) => setMessage((event as CustomEvent<string>).detail);
    const rejected = (event: PromiseRejectionEvent) => { event.preventDefault(); reportApiError(event.reason); };
    window.addEventListener('navigator-api-error', shown);
    window.addEventListener('unhandledrejection', rejected);
    return () => { window.removeEventListener('navigator-api-error', shown); window.removeEventListener('unhandledrejection', rejected); };
  }, []);
  return message ? <div role="alert" className="fixed bottom-5 right-5 z-[70] max-w-md rounded-xl border border-brand/30 bg-white p-4 text-sm shadow-lg">
    <p>{message}</p><button className="mt-2 text-brand underline" onClick={() => setMessage('')}>Dismiss</button>
  </div> : null;
}
