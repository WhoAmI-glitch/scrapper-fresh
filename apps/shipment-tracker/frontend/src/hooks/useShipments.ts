'use client';

import { useState, useCallback } from 'react';
import useSWR from 'swr';
import { api } from '@/lib/api';
import type { ActiveShipment, DashboardMetrics, RiskZone } from '@/lib/types';

/**
 * Manages the shipment list, the currently selected shipment, and related data
 * needed by the dashboard (metrics, risk zones).
 */
export function useShipments() {
  const [selectedShipmentId, setSelectedShipmentId] = useState<string | null>(null);

  // Active shipments
  const {
    data: shipments,
    error: shipmentsError,
    isLoading: shipmentsLoading,
    mutate: mutateShipments,
  } = useSWR<ActiveShipment[]>('shipments-active', () => api.getActiveShipments(), {
    refreshInterval: 30_000,
    revalidateOnFocus: false,
    dedupingInterval: 10_000,
  });

  // Dashboard metrics
  const {
    data: metrics,
    error: metricsError,
    isLoading: metricsLoading,
  } = useSWR<DashboardMetrics>('dashboard-metrics', () => api.getMetrics(), {
    refreshInterval: 30_000,
    revalidateOnFocus: false,
  });

  // Risk zones (change infrequently)
  const {
    data: riskZones,
    error: riskZonesError,
    isLoading: riskZonesLoading,
  } = useSWR<RiskZone[]>('risk-zones', () => api.getRiskZones(), {
    refreshInterval: 300_000, // 5 minutes
    revalidateOnFocus: false,
  });

  // Derive the currently selected shipment from the list
  const selectedShipment =
    shipments?.find((s) => s.id === selectedShipmentId) ?? null;

  const selectShipment = useCallback((id: string | null) => {
    setSelectedShipmentId(id);
  }, []);

  const refresh = useCallback(() => {
    mutateShipments();
  }, [mutateShipments]);

  return {
    shipments: shipments ?? [],
    selectedShipment,
    selectedShipmentId,
    selectShipment,
    metrics: metrics ?? null,
    riskZones: riskZones ?? [],
    isLoading: shipmentsLoading || metricsLoading || riskZonesLoading,
    error: shipmentsError || metricsError || riskZonesError,
    refresh,
  };
}
