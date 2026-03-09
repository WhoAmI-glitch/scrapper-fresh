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
  status: DealStatus;
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
  | 'milestone';

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
