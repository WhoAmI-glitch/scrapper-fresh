import type {
  ActionItem,
  ActiveShipment,
  AiDealUpdateDetail,
  Alert,
  Counterparty,
  DashboardMetrics,
  Deal,
  DealPnL,
  Meeting,
  MemorySearchResult,
  PaginatedResponse,
  PreMeetingBriefing,
  RiskZone,
  TranscriptSegment,
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

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json();
}

export const api = {
  // Auth
  login: (email: string, password: string) =>
    request<{ access_token: string; refresh_token: string; token_type: string; user: { id: string; email: string; full_name: string; role: string } }>(
      '/api/auth/login',
      { method: 'POST', body: JSON.stringify({ email, password }) }
    ),

  getMe: () => request<{ id: string; email: string; full_name: string; role: string }>('/api/auth/me'),

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

  // Deals
  getDeals: (page = 1, pageSize = 50, status?: string) => {
    let url = `/api/deals?page=${page}&page_size=${pageSize}`;
    if (status) url += `&status=${status}`;
    return request<PaginatedResponse<Deal>>(url);
  },

  getDeal: (id: string) => request<Deal>(`/api/deals/${id}`),

  // Counterparties
  getCounterparties: (page = 1, pageSize = 50, type?: string) => {
    let url = `/api/counterparties?page=${page}&page_size=${pageSize}`;
    if (type) url += `&type=${type}`;
    return request<PaginatedResponse<Counterparty>>(url);
  },

  // Reports / P&L
  getDealsPnl: () => request<{ items: DealPnL[]; total: number }>('/api/reports/pnl'),

  getDealPnl: (dealId: string) => request<DealPnL>(`/api/reports/pnl/${dealId}`),

  // Export URLs (open in new tab)
  getExportUrl: (type: 'trading-book' | 'shipment-progress') =>
    `${API_BASE}/api/reports/export/${type}`,

  // Exposure by region
  getExposureByRegion: () =>
    request<{ region: string; total_tons: number; total_value: number; shipment_count: number }[]>(
      '/api/dashboard/exposure-by-region'
    ),

  // Meetings
  getMeetings: (page = 1, pageSize = 20, status?: string) => {
    let url = `/api/meetings?page=${page}&page_size=${pageSize}`;
    if (status) url += `&status=${status}`;
    return request<PaginatedResponse<Meeting>>(url);
  },

  getMeeting: (id: string) => request<Meeting>(`/api/meetings/${id}`),

  getTranscript: (meetingId: string) =>
    request<TranscriptSegment[]>(`/api/meetings/${meetingId}/transcript`),

  getActionItems: (meetingId: string) =>
    request<ActionItem[]>(`/api/meetings/${meetingId}/action-items`),

  createMeeting: (data: { title: string; scheduled_start?: string; scheduled_end?: string; google_meet_url?: string }) =>
    request<Meeting>('/api/meetings', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updateMeeting: (id: string, data: Record<string, unknown>) =>
    request<Meeting>(`/api/meetings/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  // AI Intelligence
  getAiDealUpdates: (status: string = 'pending') =>
    request<{ items: AiDealUpdateDetail[]; count: number }>(`/api/ai/deal-updates?status=${status}`),

  approveAiDealUpdate: (id: string, reviewer = 'admin') =>
    request<{ status: string; id: string }>(`/api/ai/deal-updates/${id}/approve`, {
      method: 'POST',
      body: JSON.stringify({ reviewer }),
    }),

  rejectAiDealUpdate: (id: string, reviewer = 'admin') =>
    request<{ status: string; id: string }>(`/api/ai/deal-updates/${id}/reject`, {
      method: 'POST',
      body: JSON.stringify({ reviewer }),
    }),

  getPreMeetingBriefing: (meetingId: string) =>
    request<PreMeetingBriefing>(`/api/ai/briefing/${meetingId}`),

  searchMemory: (query: string, limit = 10) =>
    request<{ query: string; results: MemorySearchResult[]; count: number }>(
      `/api/ai/memory/search?q=${encodeURIComponent(query)}&limit=${limit}`
    ),

  reprocessMeeting: (meetingId: string) =>
    request<{ status: string; meeting_id: string }>(`/api/ai/meetings/${meetingId}/reprocess`, {
      method: 'POST',
    }),

  // Analytics
  getMeetingAnalytics: () =>
    request<{
      meetings: { total: number; completed: number; scheduled: number; in_progress: number; avg_duration_minutes: number };
      action_items: { total: number; open: number; done: number; in_progress: number; overdue: number; completion_rate: number };
      ai_updates: { total_proposals: number; pending: number; approved: number; rejected: number; approval_rate: number; avg_confidence: number };
    }>('/api/analytics/meetings'),

  getDealIntelligence: () =>
    request<{ deal_id: string; contract_id: string; commodity: string; buyer: string; seller: string; status: string; contract_value: number; meeting_count: number; ai_proposals: number; approved_updates: number }[]>(
      '/api/analytics/deal-intelligence'
    ),
};
