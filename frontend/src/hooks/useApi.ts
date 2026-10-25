import { useState, useEffect, useCallback } from 'react';
import type { AxiosResponse } from 'axios';

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

interface UseApiResult<T> extends UseApiState<T> {
  refetch: () => void;
}

/**
 * Generic data fetching hook.
 * Pass an async function that returns an AxiosResponse.
 * The hook auto-fetches on mount and whenever deps change.
 */
export function useApi<T>(
  fetcher: () => Promise<AxiosResponse<T>>,
  deps: unknown[] = [],
  skip = false
): UseApiResult<T> {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: !skip,
    error: null,
  });

  const fetchData = useCallback(async () => {
    if (skip) return;
    setState(prev => ({ ...prev, loading: true, error: null }));
    try {
      const response = await fetcher();
      setState({ data: response.data, loading: false, error: null });
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'An unexpected error occurred';
      setState({ data: null, loading: false, error: message });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { ...state, refetch: fetchData };
}
