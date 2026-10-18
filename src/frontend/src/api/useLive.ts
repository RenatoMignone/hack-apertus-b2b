import { useEffect, useState } from 'react';
import { api } from './index';
import { reportApiError } from '../components/ApiErrors';

/** Loads data with `load` and reloads it whenever the API reports a change. */
export function useLive<T>(load: () => Promise<T>): T | undefined {
  const [data, setData] = useState<T>();
  useEffect(() => {
    let alive = true;
    const run = () => load().then((d) => alive && setData(d)).catch((error) => alive && reportApiError(error));
    run();
    const off = api.subscribe(run);
    return () => {
      alive = false;
      off();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return data;
}
