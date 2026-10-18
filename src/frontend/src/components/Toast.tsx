import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from 'react';
import { X } from 'lucide-react';

type Toast = { id: number; message: string; undo?: () => void };
type ShowToast = (message: string, undo?: () => void) => void;

const ToastContext = createContext<ShowToast>(() => {});

/** Feedback for every action: a short message, optionally with Undo. */
export function useToast() {
  return useContext(ToastContext);
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const seq = useRef(0);

  const dismiss = useCallback((id: number) => setToasts((t) => t.filter((x) => x.id !== id)), []);

  const show = useCallback<ShowToast>(
    (message, undo) => {
      const id = ++seq.current;
      setToasts((t) => [...t.slice(-2), { id, message, undo }]);
      setTimeout(() => dismiss(id), undo ? 6000 : 3500);
    },
    [dismiss],
  );

  return (
    <ToastContext.Provider value={show}>
      {children}
      <div aria-live="polite" className="pointer-events-none fixed bottom-5 left-1/2 z-[60] flex -translate-x-1/2 flex-col items-center gap-2">
        {toasts.map((t) => (
          <div key={t.id} className="pointer-events-auto flex items-center gap-3 rounded-xl bg-ink px-4 py-2.5 text-sm text-white shadow-lg">
            <span>{t.message}</span>
            {t.undo && (
              <button
                onClick={() => {
                  t.undo!();
                  dismiss(t.id);
                }}
                className="font-semibold text-white underline underline-offset-2 hover:no-underline"
              >
                Undo
              </button>
            )}
            <button onClick={() => dismiss(t.id)} aria-label="Dismiss" className="text-white/60 hover:text-white">
              <X size={14} />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
