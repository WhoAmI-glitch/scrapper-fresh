'use client';

import { useEffect, useRef, useCallback, useMemo } from 'react';
import useSWR from 'swr';
import { api } from '@/lib/api';
import { createWebSocket } from '@/lib/websocket';
import type { Alert } from '@/lib/types';

/**
 * Fetches alerts, provides the unacknowledged count, and exposes an
 * acknowledge function. Listens for new alerts via WebSocket and
 * prepends them to the list optimistically.
 */
export function useAlerts() {
  const {
    data: alerts,
    error,
    isLoading,
    mutate,
  } = useSWR<Alert[]>('alerts', () => api.getAlerts(50), {
    refreshInterval: 60_000,
    revalidateOnFocus: false,
  });

  const mutateRef = useRef(mutate);
  mutateRef.current = mutate;

  // Subscribe to new alerts via WebSocket
  useEffect(() => {
    const ws = createWebSocket();

    const unsub = ws.onNewAlert((newAlert) => {
      mutateRef.current(
        (current) => {
          if (!current) return [newAlert];
          // Prepend, avoiding duplicates
          if (current.some((a) => a.id === newAlert.id)) return current;
          return [newAlert, ...current];
        },
        { revalidate: false },
      );
    });

    return () => {
      unsub();
      ws.close();
    };
  }, []);

  // Count of alerts that haven't been acknowledged
  const unacknowledgedCount = useMemo(
    () => (alerts ?? []).filter((a) => !a.acknowledged).length,
    [alerts],
  );

  // Acknowledge an alert optimistically
  const acknowledge = useCallback(
    async (alertId: string) => {
      // Optimistic update
      mutate(
        (current) =>
          current?.map((a) =>
            a.id === alertId ? { ...a, acknowledged: true } : a,
          ),
        { revalidate: false },
      );

      try {
        await api.acknowledgeAlert(alertId);
      } catch {
        // Revert on failure by re-fetching
        mutate();
      }
    },
    [mutate],
  );

  return {
    alerts: alerts ?? [],
    unacknowledgedCount,
    error,
    isLoading,
    acknowledge,
    refresh: useCallback(() => mutate(), [mutate]),
  };
}
