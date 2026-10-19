import { useEffect, useRef, useState, useSyncExternalStore } from 'react';
import { sessionVersion, subscribeSession } from './session';
import { OperationScope } from './operationScope';
import { api } from './index';
import { reportApiError } from '../components/ApiErrors';

/** Loads data with `load` and reloads it whenever the API reports a change. */
export function useLive<T>(load: () => Promise<T>): T | undefined {
  const session = useSyncExternalStore(subscribeSession, sessionVersion);
  const latest = useRef(load); latest.current = load;
  const [data, setData] = useState<T>();
  useEffect(() => {
    const scope = new OperationScope('list');
    const run = () => {
      const ticket = scope.begin();
      return latest.current().then(d => { if (ticket.current()) setData(d); })
        .catch(error => { if (ticket.current()) reportApiError(error); });
    };
    run();
    const off = api.subscribe(run);
    return () => {
      scope.stop();
      off();
    };
  }, [session]);
  return data;
}
