// ── Port ──────────────────────────────────────────────────────────────────────
export interface Port {
  id: string;
  name: string;
  country: string;
  unlocode: string;
  lat: number;
  lon: number;
}

// ── Vessel ────────────────────────────────────────────────────────────────────
export interface Vessel {
  id: string;
  name: string;
  imo_number: string;
  mmsi: string;
  vessel_type: string;
  flag: string;
  dwt: number;
  current_lat: number | null;
  current_lon: number | null;
  current_speed: number;
  current_heading: number;
  last_ais_update: string | null;
}

// ── Deal ──────────────────────────────────────────────────────────────────────
export interface Deal {
  id: string;
  contract_id: string;
  commodity: string;
  buyer: string;
  seller: string;
  quantity_tons: number;
  price_per_ton: number;
  contract_value: number;
  incoterms: string;
  load_port: Port;
  discharge_port: Port;
  load_port_id: string;
  discharge_port_id: string;
  status: DealStatus;
  notes: string | null;
  buyer_id: string | null;
  seller_id: string | null;
  broker_id: string | null;
  payment_terms: string | null;
  laycan_start: string | null;
  laycan_end: string | null;
  risk_notes: string | null;
  created_at: string;
  updated_at: string;
}

export type DealStatus =
  | 'draft'
  | 'confirmed'
  | 'loading'
  | 'in_transit'
  | 'arrived'
  | 'completed'
  | 'cancelled';

// ── Shipment ──────────────────────────────────────────────────────────────────
export type ShipmentStatus =
  | 'loading'
  | 'departed'
  | 'in_transit'
  | 'arriving'
  | 'arrived'
  | 'discharged';

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

export interface ActiveShipment {
  id: string;
  cargo_quantity_tons: number;
  status: ShipmentStatus;
  eta: string | null;
  current_risk_level: RiskLevel;
  bill_of_lading: string | null;
  load_date: string | null;
  departure_date: string | null;
  contract_id: string;
  buyer: string;
  seller: string;
  contract_value: number;
  commodity: string;
  incoterms: string;
  vessel_name: string | null;
  imo_number: string | null;
  mmsi: string | null;
  vessel_lat: number | null;
  vessel_lon: number | null;
  vessel_speed: number;
  vessel_heading: number;
  last_ais_update: string | null;
  load_port_name: string;
  load_port_code: string;
  load_port_lat: number;
  load_port_lon: number;
  discharge_port_name: string;
  discharge_port_code: string;
  discharge_port_lat: number;
  discharge_port_lon: number;
}

// ── Risk Zones ────────────────────────────────────────────────────────────────
export interface RiskZone {
  id: string;
  name: string;
  zone_type: 'piracy' | 'conflict' | 'restricted' | 'insurance';
  risk_level: RiskLevel;
  coordinates: number[][][]; // GeoJSON polygon coordinates
  description: string;
}

// ── Alerts ────────────────────────────────────────────────────────────────────
export type AlertSeverity = 'info' | 'warning' | 'critical';

export type AlertType =
  | 'risk_zone_entry'
  | 'delay'
  | 'route_deviation'
  | 'email_received'
  | 'milestone'
  | 'action_item_due';

export interface Alert {
  id: string;
  alert_type: AlertType;
  severity: AlertSeverity;
  title: string;
  message: string;
  acknowledged: boolean;
  created_at: string;
  shipment_id: string | null;
  vessel_name: string | null;
  contract_id: string | null;
}

// ── Dashboard ─────────────────────────────────────────────────────────────────
export interface DashboardMetrics {
  active_shipments: number;
  total_tons_at_sea: number;
  total_value_at_sea: number;
  vessels_in_risk_zones: number;
  active_vessels: number;
}

// ── Vessel Track ──────────────────────────────────────────────────────────────
export interface VesselTrackPoint {
  lat: number;
  lon: number;
  speed: number;
  heading: number;
  recorded_at: string;
}

// ── Counterparty ──────────────────────────────────────────────────────────────
export interface Counterparty {
  id: string;
  name: string;
  short_name: string | null;
  type: 'buyer' | 'seller' | 'broker' | 'agent';
  country: string | null;
  tax_id: string | null;
  primary_contact_name: string | null;
  primary_contact_email: string | null;
  primary_contact_phone: string | null;
  notes: string | null;
  deal_count: number;
  created_at: string;
  updated_at: string;
}

// ── Deal P&L ──────────────────────────────────────────────────────────────────
export interface DealPnL {
  deal_id: string;
  contract_id: string;
  revenue: number;
  quantity_tons: number;
  actual_costs: number;
  estimated_costs: number;
  total_costs: number;
  gross_margin: number;
  margin_pct: number;
  total_commission: number;
  net_margin: number;
  cost_breakdown: { cost_type: string; total: number; actual: number; estimated: number }[];
}

// ── Paginated Response ────────────────────────────────────────────────────────
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// ── Meeting ──────────────────────────────────────────────────────────────────
export type MeetingStatus =
  | 'scheduled'
  | 'in_progress'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'cancelled';

export interface MeetingParticipant {
  id: string;
  name: string;
  email: string | null;
  role: 'organizer' | 'attendee' | 'bot';
}

export interface MeetingSummary {
  id: string;
  summary_text: string;
  key_decisions: string[];
  market_intel: string[];
  created_at: string;
}

export interface ActionItem {
  id: string;
  meeting_id: string;
  title: string;
  description: string | null;
  assignee_name: string | null;
  assignee_email: string | null;
  due_date: string | null;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  status: 'open' | 'in_progress' | 'done' | 'cancelled';
  created_at: string;
}

export interface AiDealUpdate {
  id: string;
  meeting_id: string;
  deal_id: string;
  contract_id: string;
  field_name: string;
  current_value: string | null;
  proposed_value: string;
  confidence: number;
  reasoning: string;
  status: 'pending' | 'approved' | 'rejected';
}

export interface Meeting {
  id: string;
  title: string;
  status: MeetingStatus;
  scheduled_start: string | null;
  scheduled_end: string | null;
  actual_start: string | null;
  actual_end: string | null;
  google_calendar_event_id: string | null;
  google_meet_url: string | null;
  participants: MeetingParticipant[];
  summary: MeetingSummary | null;
  action_items: ActionItem[];
  created_at: string;
  updated_at: string;
}

export interface TranscriptSegment {
  id: string;
  speaker_name: string;
  text: string;
  start_ms: number;
  end_ms: number;
  confidence: number;
}

// ── AI Deal Update ───────────────────────────────────────────────────────────
export interface AiDealUpdateDetail {
  id: string;
  meeting_id: string;
  deal_id: string;
  contract_id: string;
  commodity: string;
  buyer: string;
  seller: string;
  meeting_title: string;
  meeting_date: string | null;
  field_name: string;
  old_value: string | null;
  proposed_value: string;
  confidence: number;
  reasoning: string;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
}

// ── Memory Search ────────────────────────────────────────────────────────────
export interface MemorySearchResult {
  meeting_id: string;
  meeting_title: string;
  chunk_text: string;
  chunk_type: string;
  similarity: number;
  scheduled_start: string | null;
}

// ── Pre-Meeting Briefing ─────────────────────────────────────────────────────
export interface PreMeetingBriefing {
  executive_summary: string;
  key_topics: string[];
  talking_points: string[];
  open_questions: string[];
  deal_status_snapshot: { contract_id: string; status: string; key_concern: string }[];
  preparation_notes: string;
}

// ── WebSocket ─────────────────────────────────────────────────────────────────
export interface WsVesselUpdate {
  type: 'vessel_update';
  data: {
    vessel_id: string;
    lat: number;
    lon: number;
    speed: number;
    heading: number;
    timestamp: string;
  };
}

export interface WsNewAlert {
  type: 'new_alert';
  data: Alert;
}

export interface WsShipmentUpdate {
  type: 'shipment_update';
  data: {
    shipment_id: string;
    status: ShipmentStatus;
    risk_level: RiskLevel;
  };
}

export type WsMessage = WsVesselUpdate | WsNewAlert | WsShipmentUpdate;
