import type {
  ActiveShipment,
  Alert,
  DashboardMetrics,
  Deal,
  RiskZone,
  VesselTrackPoint,
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiError extends Error {
  status: number;

  constructor(status: number, statusText: string, url: string) {
    super(`API error ${status} (${statusText}) for ${url}`);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;

  const res = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    throw new ApiError(res.status, res.statusText, url);
  }

  // Handle 204 No Content responses
  if (res.status === 204) {
    return undefined as T;
  }

  return res.json();
}

export const api = {
  // Dashboard metrics
  getMetrics: () => request<DashboardMetrics>('/api/dashboard/metrics'),

  // Active shipments (includes vessel position, ports, contract info)
  getActiveShipments: () => request<ActiveShipment[]>('/api/shipments/active'),

  // Single shipment detail
  getShipment: (id: string) => request<ActiveShipment>(`/api/shipments/${id}`),

  // Vessel historical track points
  getVesselTrack: (id: string, hours: number = 72) =>
    request<VesselTrackPoint[]>(`/api/vessels/${id}/track?hours=${hours}`),

  // Risk zone polygons
  getRiskZones: () => request<RiskZone[]>('/api/risk-zones'),

  // Alerts (newest first)
  getAlerts: (limit: number = 50) =>
    request<Alert[]>(`/api/alerts?limit=${limit}`),

  // Acknowledge a single alert
  acknowledgeAlert: (id: string) =>
    request<void>(`/api/alerts/${id}/acknowledge`, { method: 'POST' }),

  // All deals
  getDeals: () => request<Deal[]>('/api/deals'),
};
