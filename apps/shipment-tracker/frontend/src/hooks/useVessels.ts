'use client';

import useSWR from 'swr';
import { useEffect, useRef, useCallback } from 'react';
import { api } from '@/lib/api';
import { createWebSocket } from '@/lib/websocket';
import type { ActiveShipment } from '@/lib/types';

/**
 * Provides real-time vessel positions sourced from active shipments.
 * Polls the API every 30 seconds and applies WebSocket position updates
 * in between polls so the globe stays current.
 */
export function useVessels() {
  const {
    data: shipments,
    error,
    isLoading,
    mutate,
  } = useSWR<ActiveShipment[]>('shipments-active', () => api.getActiveShipments(), {
    refreshInterval: 30_000,
    revalidateOnFocus: false,
    dedupingInterval: 10_000,
  });

  // Keep a ref to avoid stale closures in the WS callback
  const mutateRef = useRef(mutate);
  mutateRef.current = mutate;

  useEffect(() => {
    const ws = createWebSocket();

    const unsub = ws.onVesselUpdate((update) => {
      // Optimistically patch vessel position in the cached shipments list
      mutateRef.current(
        (current) => {
          if (!current) return current;
          return current.map((s) => {
            if (s.mmsi === update.vessel_id || s.imo_number === update.vessel_id) {
              return {
                ...s,
                vessel_lat: update.lat,
                vessel_lon: update.lon,
                vessel_speed: update.speed,
                vessel_heading: update.heading,
                last_ais_update: update.timestamp,
              };
            }
            return s;
          });
        },
        { revalidate: false },
      );
    });

    return () => {
      unsub();
      ws.close();
    };
  }, []);

  // Derive vessels that have a known position
  const vessels = (shipments ?? []).filter(
    (s): s is ActiveShipment & { vessel_lat: number; vessel_lon: number } =>
      s.vessel_lat !== null && s.vessel_lon !== null,
  );

  const refresh = useCallback(() => mutate(), [mutate]);

  return {
    shipments: shipments ?? [],
    vessels,
    error,
    isLoading,
    refresh,
  };
}
