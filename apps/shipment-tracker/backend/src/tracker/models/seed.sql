-- Seed data for Charcoal Shipment Intelligence Platform
-- Run after schema.sql

-- PORTS
INSERT INTO ports (id, name, country, unlocode, location, timezone) VALUES
(
    'a1000000-0000-0000-0000-000000000001',
    'Port of Santos',
    'Brazil',
    'BRSSZ',
    ST_GeogFromText('POINT(-46.3042 -23.9608)'),
    'America/Sao_Paulo'
),
(
    'a1000000-0000-0000-0000-000000000002',
    'Port of Durban',
    'South Africa',
    'ZADUR',
    ST_GeogFromText('POINT(31.0292 -29.8687)'),
    'Africa/Johannesburg'
),
(
    'a1000000-0000-0000-0000-000000000003',
    'Port of Tema',
    'Ghana',
    'GHTEM',
    ST_GeogFromText('POINT(-0.0174 5.6378)'),
    'Africa/Accra'
),
(
    'a1000000-0000-0000-0000-000000000004',
    'Port of Paranagua',
    'Brazil',
    'BRPNG',
    ST_GeogFromText('POINT(-48.5093 -25.5005)'),
    'America/Sao_Paulo'
),
(
    'a1000000-0000-0000-0000-000000000005',
    'Apapa Port',
    'Nigeria',
    'NGAPP',
    ST_GeogFromText('POINT(3.3590 6.4480)'),
    'Africa/Lagos'
);

-- VESSELS (bulk carriers)
INSERT INTO vessels (id, name, imo_number, mmsi, vessel_type, flag, dwt, current_position, current_speed, current_heading, last_ais_update) VALUES
(
    'b2000000-0000-0000-0000-000000000001',
    'MV African Pioneer',
    '9876543',
    '636092587',
    'bulk_carrier',
    'Liberia',
    58000,
    ST_GeogFromText('POINT(-10.5 2.3)'),
    11.2,
    215.0,
    NOW() - INTERVAL '15 minutes'
),
(
    'b2000000-0000-0000-0000-000000000002',
    'MV Santos Trader',
    '9765432',
    '538006712',
    'bulk_carrier',
    'Marshall Islands',
    45000,
    ST_GeogFromText('POINT(-46.2 -23.9)'),
    0.0,
    0.0,
    NOW() - INTERVAL '5 minutes'
),
(
    'b2000000-0000-0000-0000-000000000003',
    'MV Durban Star',
    '9654321',
    '371234567',
    'bulk_carrier',
    'Panama',
    52000,
    ST_GeogFromText('POINT(28.5 -25.8)'),
    12.8,
    195.0,
    NOW() - INTERVAL '10 minutes'
);

-- DEALS (charcoal contracts)
INSERT INTO deals (id, contract_id, commodity, buyer, seller, quantity_tons, price_per_ton, incoterms, load_port_id, discharge_port_id, status, notes) VALUES
(
    'c3000000-0000-0000-0000-000000000001',
    'CHR-2026-0042',
    'charcoal',
    'West Africa Fuels Ltd',
    'Brasil Carvao Exportadora SA',
    12000.00,
    285.50,
    'FOB',
    'a1000000-0000-0000-0000-000000000001',  -- Santos
    'a1000000-0000-0000-0000-000000000005',  -- Apapa
    'in_transit',
    'Premium hardwood charcoal, lump grade A. Delivery within 30 days of B/L date.'
),
(
    'c3000000-0000-0000-0000-000000000002',
    'CHR-2026-0055',
    'charcoal',
    'Ghana Industrial Commodities',
    'Paranagua Carbon Trade Ltda',
    8500.00,
    310.00,
    'CIF',
    'a1000000-0000-0000-0000-000000000004',  -- Paranagua
    'a1000000-0000-0000-0000-000000000003',  -- Tema
    'loading',
    'Mixed charcoal grades, bagged 50kg. Letter of credit confirmed.'
),
(
    'c3000000-0000-0000-0000-000000000003',
    'CHR-2026-0061',
    'charcoal',
    'Durban Energy Holdings (Pty) Ltd',
    'Brasil Carvao Exportadora SA',
    15000.00,
    275.00,
    'CFR',
    'a1000000-0000-0000-0000-000000000001',  -- Santos
    'a1000000-0000-0000-0000-000000000002',  -- Durban
    'in_transit',
    'Eucalyptus charcoal, industrial grade. Second shipment under framework agreement.'
);

-- SHIPMENTS
INSERT INTO shipments (id, deal_id, vessel_id, cargo_quantity_tons, bill_of_lading, load_date, departure_date, eta, actual_arrival, status, current_risk_level) VALUES
(
    'd4000000-0000-0000-0000-000000000001',
    'c3000000-0000-0000-0000-000000000001',
    'b2000000-0000-0000-0000-000000000001',
    12000.00,
    'BRSSZ-2026-88431',
    '2026-02-15',
    '2026-02-18 14:00:00+00',
    '2026-03-14 08:00:00+00',
    NULL,
    'in_transit',
    'high'
),
(
    'd4000000-0000-0000-0000-000000000002',
    'c3000000-0000-0000-0000-000000000002',
    'b2000000-0000-0000-0000-000000000002',
    8500.00,
    NULL,
    '2026-03-08',
    NULL,
    '2026-04-02 12:00:00+00',
    NULL,
    'loading',
    'low'
),
(
    'd4000000-0000-0000-0000-000000000003',
    'c3000000-0000-0000-0000-000000000003',
    'b2000000-0000-0000-0000-000000000003',
    15000.00,
    'BRSSZ-2026-88502',
    '2026-02-20',
    '2026-02-23 10:00:00+00',
    '2026-03-10 06:00:00+00',
    NULL,
    'arriving',
    'low'
);

-- RISK ZONES
-- Gulf of Guinea piracy zone
INSERT INTO risk_zones (id, name, zone_type, risk_level, geometry, description, source, active) VALUES
(
    'e5000000-0000-0000-0000-000000000001',
    'Gulf of Guinea High Risk Area',
    'piracy',
    'critical',
    ST_GeogFromText('MULTIPOLYGON(((-5.0 -2.0, 10.0 -2.0, 10.0 7.0, -5.0 7.0, -5.0 -2.0)))'),
    'IMB-designated high-risk area for piracy and armed robbery against ships. Frequent incidents involving kidnapping of crew for ransom.',
    'IMB Piracy Reporting Centre',
    TRUE
),
-- Strait of Hormuz
(
    'e5000000-0000-0000-0000-000000000002',
    'Strait of Hormuz',
    'conflict',
    'high',
    ST_GeogFromText('MULTIPOLYGON(((54.0 24.5, 57.5 24.5, 57.5 27.0, 54.0 27.0, 54.0 24.5)))'),
    'Strategic chokepoint with elevated risk due to regional tensions. Periodic military incidents and vessel seizures.',
    'UKMTO',
    TRUE
),
-- Somali Basin
(
    'e5000000-0000-0000-0000-000000000003',
    'Somali Basin Extended Risk Area',
    'piracy',
    'high',
    ST_GeogFromText('MULTIPOLYGON(((41.0 -2.0, 58.0 -2.0, 58.0 14.0, 41.0 14.0, 41.0 -2.0)))'),
    'Extended piracy risk area covering the Somali Basin and western Indian Ocean. Best Management Practices (BMP5) apply.',
    'EUNAVFOR',
    TRUE
),
-- Red Sea (Bab el-Mandeb)
(
    'e5000000-0000-0000-0000-000000000004',
    'Red Sea / Bab el-Mandeb',
    'conflict',
    'critical',
    ST_GeogFromText('MULTIPOLYGON(((42.0 12.0, 45.0 12.0, 45.0 15.5, 42.0 15.5, 42.0 12.0)))'),
    'Active conflict zone with missile and drone attacks on commercial shipping. Multiple incidents since late 2023.',
    'UKMTO',
    TRUE
),
-- Suez Canal
(
    'e5000000-0000-0000-0000-000000000005',
    'Suez Canal Zone',
    'restricted',
    'medium',
    ST_GeogFromText('MULTIPOLYGON(((32.0 29.8, 33.0 29.8, 33.0 31.3, 32.0 31.3, 32.0 29.8)))'),
    'Regulated transit zone. Vessels must comply with Suez Canal Authority regulations. Potential for delays and congestion.',
    'Suez Canal Authority',
    TRUE
);

-- ALERTS
INSERT INTO alerts (id, shipment_id, vessel_id, deal_id, alert_type, severity, title, message, acknowledged) VALUES
(
    'f6000000-0000-0000-0000-000000000001',
    'd4000000-0000-0000-0000-000000000001',
    'b2000000-0000-0000-0000-000000000001',
    'c3000000-0000-0000-0000-000000000001',
    'risk_zone_entry',
    'critical',
    'MV African Pioneer entered Gulf of Guinea High Risk Area',
    'Vessel MV African Pioneer (IMO 9876543) has entered the Gulf of Guinea High Risk Area at position 2.3N, 10.5W. This zone has critical piracy risk. Recommend contacting vessel master to confirm security measures are in place per BMP West Africa guidelines.',
    FALSE
),
(
    'f6000000-0000-0000-0000-000000000002',
    'd4000000-0000-0000-0000-000000000003',
    'b2000000-0000-0000-0000-000000000003',
    'c3000000-0000-0000-0000-000000000003',
    'milestone',
    'info',
    'MV Durban Star approaching discharge port',
    'Vessel MV Durban Star (IMO 9654321) is approximately 450 NM from Port of Durban. ETA 2026-03-10 06:00 UTC. Current speed 12.8 knots. Recommend notifying port agent and arranging berth.',
    FALSE
),
(
    'f6000000-0000-0000-0000-000000000003',
    'd4000000-0000-0000-0000-000000000002',
    'b2000000-0000-0000-0000-000000000002',
    'c3000000-0000-0000-0000-000000000002',
    'email_received',
    'info',
    'Loading update received for CHR-2026-0055',
    'Email received from broker@paranaguacarbontrade.com regarding deal CHR-2026-0055. Subject: "Loading progress update - MV Santos Trader". Loading operations commenced on 2026-03-08. Estimated completion in 3 days.',
    TRUE
);

-- Sample voyage track points for MV African Pioneer (crossing Atlantic)
INSERT INTO voyage_tracks (vessel_id, position, speed, heading, recorded_at) VALUES
('b2000000-0000-0000-0000-000000000001', ST_GeogFromText('POINT(-42.0 -18.0)'), 11.5, 340.0, '2026-02-25 00:00:00+00'),
('b2000000-0000-0000-0000-000000000001', ST_GeogFromText('POINT(-38.0 -14.0)'), 11.3, 338.0, '2026-02-27 00:00:00+00'),
('b2000000-0000-0000-0000-000000000001', ST_GeogFromText('POINT(-33.0 -9.5)'),  11.4, 335.0, '2026-03-01 00:00:00+00'),
('b2000000-0000-0000-0000-000000000001', ST_GeogFromText('POINT(-27.0 -5.0)'),  11.0, 330.0, '2026-03-03 00:00:00+00'),
('b2000000-0000-0000-0000-000000000001', ST_GeogFromText('POINT(-20.0 -1.5)'),  11.1, 320.0, '2026-03-05 00:00:00+00'),
('b2000000-0000-0000-0000-000000000001', ST_GeogFromText('POINT(-15.0 0.8)'),   11.2, 310.0, '2026-03-07 00:00:00+00'),
('b2000000-0000-0000-0000-000000000001', ST_GeogFromText('POINT(-10.5 2.3)'),   11.2, 215.0, '2026-03-09 00:00:00+00');

-- Sample voyage track points for MV Durban Star (approaching Durban)
INSERT INTO voyage_tracks (vessel_id, position, speed, heading, recorded_at) VALUES
('b2000000-0000-0000-0000-000000000003', ST_GeogFromText('POINT(-35.0 -15.0)'), 12.5, 120.0, '2026-02-27 00:00:00+00'),
('b2000000-0000-0000-0000-000000000003', ST_GeogFromText('POINT(-25.0 -18.0)'), 12.7, 130.0, '2026-03-01 00:00:00+00'),
('b2000000-0000-0000-0000-000000000003', ST_GeogFromText('POINT(-12.0 -20.5)'), 12.6, 135.0, '2026-03-03 00:00:00+00'),
('b2000000-0000-0000-0000-000000000003', ST_GeogFromText('POINT(5.0 -23.0)'),   12.9, 145.0, '2026-03-05 00:00:00+00'),
('b2000000-0000-0000-0000-000000000003', ST_GeogFromText('POINT(18.0 -24.5)'),  12.8, 160.0, '2026-03-07 00:00:00+00'),
('b2000000-0000-0000-0000-000000000003', ST_GeogFromText('POINT(28.5 -25.8)'),  12.8, 195.0, '2026-03-09 00:00:00+00');
