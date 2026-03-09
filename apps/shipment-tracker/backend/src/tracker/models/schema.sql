-- Charcoal Shipment Intelligence Platform - Database Schema
-- Requires PostgreSQL 14+ with PostGIS extension

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ENUM TYPES
CREATE TYPE deal_status AS ENUM ('draft','confirmed','loading','in_transit','arrived','completed','cancelled');
CREATE TYPE shipment_status AS ENUM ('loading','departed','in_transit','arriving','arrived','discharged');
CREATE TYPE risk_level AS ENUM ('low','medium','high','critical');
CREATE TYPE zone_type AS ENUM ('piracy','conflict','restricted','insurance');
CREATE TYPE alert_type AS ENUM ('risk_zone_entry','delay','route_deviation','email_received','milestone');
CREATE TYPE alert_severity AS ENUM ('info','warning','critical');
CREATE TYPE email_category AS ENUM ('charter','bol','notification','broker','other');
CREATE TYPE incoterm AS ENUM ('FOB','CIF','CFR','EXW','FCA','CPT','CIP','DAP','DPU','DDP');

-- PORTS
CREATE TABLE ports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    country TEXT NOT NULL,
    unlocode TEXT UNIQUE NOT NULL,  -- e.g. "BRSSZ"
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    timezone TEXT DEFAULT 'UTC',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_ports_location ON ports USING GIST(location);

-- VESSELS
CREATE TABLE vessels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    imo_number TEXT UNIQUE NOT NULL,
    mmsi TEXT UNIQUE NOT NULL,
    vessel_type TEXT DEFAULT 'bulk_carrier',
    flag TEXT,
    dwt INTEGER,  -- deadweight tonnage
    current_position GEOGRAPHY(POINT, 4326),
    current_speed REAL DEFAULT 0,
    current_heading REAL DEFAULT 0,
    last_ais_update TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- DEALS (commercial contracts)
CREATE TABLE deals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contract_id TEXT UNIQUE NOT NULL,  -- e.g. "CHR-2026-0042"
    commodity TEXT NOT NULL DEFAULT 'charcoal',
    buyer TEXT NOT NULL,
    seller TEXT NOT NULL,
    quantity_tons NUMERIC(12,2) NOT NULL,
    price_per_ton NUMERIC(10,2) NOT NULL,
    contract_value NUMERIC(14,2) GENERATED ALWAYS AS (quantity_tons * price_per_ton) STORED,
    incoterms incoterm NOT NULL DEFAULT 'FOB',
    load_port_id UUID NOT NULL REFERENCES ports(id),
    discharge_port_id UUID NOT NULL REFERENCES ports(id),
    status deal_status NOT NULL DEFAULT 'draft',
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- SHIPMENTS (physical cargo movements)
CREATE TABLE shipments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    deal_id UUID NOT NULL REFERENCES deals(id),
    vessel_id UUID REFERENCES vessels(id),
    cargo_quantity_tons NUMERIC(12,2) NOT NULL,
    bill_of_lading TEXT,
    load_date DATE,
    departure_date TIMESTAMPTZ,
    eta TIMESTAMPTZ,
    actual_arrival TIMESTAMPTZ,
    status shipment_status NOT NULL DEFAULT 'loading',
    current_risk_level risk_level DEFAULT 'low',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- VOYAGE TRACKS (AIS historical positions)
CREATE TABLE voyage_tracks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vessel_id UUID NOT NULL REFERENCES vessels(id),
    position GEOGRAPHY(POINT, 4326) NOT NULL,
    speed REAL,
    heading REAL,
    recorded_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_voyage_tracks_vessel ON voyage_tracks(vessel_id, recorded_at DESC);
CREATE INDEX idx_voyage_tracks_position ON voyage_tracks USING GIST(position);

-- RISK ZONES (geographic areas with risk levels)
CREATE TABLE risk_zones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    zone_type zone_type NOT NULL,
    risk_level risk_level NOT NULL,
    geometry GEOGRAPHY(MULTIPOLYGON, 4326) NOT NULL,
    description TEXT,
    source TEXT,
    active BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_risk_zones_geometry ON risk_zones USING GIST(geometry);

-- INCIDENTS (specific events in risk zones)
CREATE TABLE incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    risk_zone_id UUID REFERENCES risk_zones(id),
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    incident_type TEXT NOT NULL,
    description TEXT,
    occurred_at TIMESTAMPTZ NOT NULL,
    source TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- EMAILS (linked to deals/shipments)
CREATE TABLE emails (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    shipment_id UUID REFERENCES shipments(id),
    deal_id UUID REFERENCES deals(id),
    gmail_id TEXT UNIQUE,
    subject TEXT NOT NULL,
    sender TEXT NOT NULL,
    recipients TEXT[] DEFAULT '{}',
    body_text TEXT,
    received_at TIMESTAMPTZ NOT NULL,
    category email_category DEFAULT 'other',
    parsed_data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ATTACHMENTS
CREATE TABLE attachments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email_id UUID NOT NULL REFERENCES emails(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    content_type TEXT,
    storage_path TEXT NOT NULL,
    size_bytes INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ALERTS
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    shipment_id UUID REFERENCES shipments(id),
    vessel_id UUID REFERENCES vessels(id),
    deal_id UUID REFERENCES deals(id),
    alert_type alert_type NOT NULL,
    severity alert_severity NOT NULL DEFAULT 'info',
    title TEXT NOT NULL,
    message TEXT,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_alerts_unack ON alerts(acknowledged, created_at DESC) WHERE NOT acknowledged;

-- VIEWS for common queries
CREATE OR REPLACE VIEW active_shipments AS
SELECT
    s.id, s.cargo_quantity_tons, s.status, s.eta, s.current_risk_level,
    s.bill_of_lading, s.load_date, s.departure_date,
    d.contract_id, d.buyer, d.seller, d.contract_value, d.commodity, d.incoterms,
    v.name AS vessel_name, v.imo_number, v.mmsi,
    ST_Y(v.current_position::geometry) AS vessel_lat,
    ST_X(v.current_position::geometry) AS vessel_lon,
    v.current_speed, v.current_heading, v.last_ais_update,
    lp.name AS load_port_name, lp.unlocode AS load_port_code,
    ST_Y(lp.location::geometry) AS load_port_lat,
    ST_X(lp.location::geometry) AS load_port_lon,
    dp.name AS discharge_port_name, dp.unlocode AS discharge_port_code,
    ST_Y(dp.location::geometry) AS discharge_port_lat,
    ST_X(dp.location::geometry) AS discharge_port_lon
FROM shipments s
JOIN deals d ON s.deal_id = d.id
LEFT JOIN vessels v ON s.vessel_id = v.id
JOIN ports lp ON d.load_port_id = lp.id
JOIN ports dp ON d.discharge_port_id = dp.id
WHERE s.status NOT IN ('arrived', 'discharged');

CREATE OR REPLACE VIEW dashboard_metrics AS
SELECT
    COUNT(*) AS active_shipments,
    COALESCE(SUM(s.cargo_quantity_tons), 0) AS total_tons_at_sea,
    COALESCE(SUM(d.contract_value), 0) AS total_value_at_sea,
    COUNT(*) FILTER (WHERE s.current_risk_level IN ('high','critical')) AS vessels_in_risk_zones,
    COUNT(DISTINCT v.id) AS active_vessels
FROM shipments s
JOIN deals d ON s.deal_id = d.id
LEFT JOIN vessels v ON s.vessel_id = v.id
WHERE s.status NOT IN ('arrived', 'discharged');
