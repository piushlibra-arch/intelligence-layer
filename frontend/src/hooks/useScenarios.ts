import { useApi } from './useApi';
import { getScenarios } from '../api/client';
import type { Scenario } from '../types';

export function useScenarios() {
  const { data, loading, error, refetch } = useApi<Scenario[]>(
    () => getScenarios(),
    []
  );

  return {
    scenarios: data || [],
    loading,
    error,
    refetch,
  };
}
