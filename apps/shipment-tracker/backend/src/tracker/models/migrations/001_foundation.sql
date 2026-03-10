-- Migration 001: Foundation Enhancement
-- Adds counterparties, deal_costs, deal_commissions, audit_log tables
-- Extends deals with buyer_id, seller_id, broker_id, payment_terms, laycan, risk_notes

-- ============================================================================
-- COUNTERPARTIES
-- ============================================================================
CREATE TABLE IF NOT EXISTS counterparties (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    short_name TEXT,
    type TEXT NOT NULL DEFAULT 'buyer',  -- buyer, seller, broker, agent
    country TEXT,
    tax_id TEXT,
    primary_contact_name TEXT,
    primary_contact_email TEXT,
    primary_contact_phone TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_counterparties_type ON counterparties(type);
CREATE INDEX IF NOT EXISTS idx_counterparties_name ON counterparties(name);

-- ============================================================================
-- DEAL COSTS (line items for P&L calculation)
-- ============================================================================
CREATE TABLE IF NOT EXISTS deal_costs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
    cost_type TEXT NOT NULL,
    -- freight, insurance, port_charges, inspection, customs,
    -- brokerage, finance, demurrage, other
    description TEXT NOT NULL,
    amount NUMERIC(14,2) NOT NULL,
    currency TEXT DEFAULT 'USD',
    is_estimated BOOLEAN DEFAULT TRUE,
    invoice_ref TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_deal_costs_deal ON deal_costs(deal_id);

-- ============================================================================
-- DEAL COMMISSIONS
-- ============================================================================
CREATE TABLE IF NOT EXISTS deal_commissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
    recipient TEXT NOT NULL,
    commission_type TEXT NOT NULL,  -- flat, per_ton, percentage
    rate NUMERIC(10,4) NOT NULL,
    paid BOOLEAN DEFAULT FALSE,
    paid_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_deal_commissions_deal ON deal_commissions(deal_id);

-- ============================================================================
-- AUDIT LOG
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type TEXT NOT NULL,
    entity_id UUID NOT NULL,
    action TEXT NOT NULL,  -- create, update, delete, status_change
    field_name TEXT,
    old_value TEXT,
    new_value TEXT,
    actor TEXT,  -- user email or 'system' or 'ai'
    source TEXT,  -- api, meeting_ai, email_parser, ais_poller
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log(entity_type, entity_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_log(created_at DESC);

-- ============================================================================
-- EXTEND DEALS TABLE
-- ============================================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='deals' AND column_name='buyer_id') THEN
        ALTER TABLE deals ADD COLUMN buyer_id UUID REFERENCES counterparties(id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='deals' AND column_name='seller_id') THEN
        ALTER TABLE deals ADD COLUMN seller_id UUID REFERENCES counterparties(id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='deals' AND column_name='broker_id') THEN
        ALTER TABLE deals ADD COLUMN broker_id UUID REFERENCES counterparties(id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='deals' AND column_name='payment_terms') THEN
        ALTER TABLE deals ADD COLUMN payment_terms TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='deals' AND column_name='laycan_start') THEN
        ALTER TABLE deals ADD COLUMN laycan_start DATE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='deals' AND column_name='laycan_end') THEN
        ALTER TABLE deals ADD COLUMN laycan_end DATE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='deals' AND column_name='risk_notes') THEN
        ALTER TABLE deals ADD COLUMN risk_notes TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='deals' AND column_name='ai_last_updated_at') THEN
        ALTER TABLE deals ADD COLUMN ai_last_updated_at TIMESTAMPTZ;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='deals' AND column_name='ai_update_count') THEN
        ALTER TABLE deals ADD COLUMN ai_update_count INTEGER DEFAULT 0;
    END IF;
END $$;

-- ============================================================================
-- DEAL P&L VIEW
-- ============================================================================
CREATE OR REPLACE VIEW deal_pnl AS
SELECT
    d.id,
    d.contract_id,
    d.contract_value AS revenue,
    COALESCE(SUM(dc.amount) FILTER (WHERE NOT dc.is_estimated), 0) AS actual_costs,
    COALESCE(SUM(dc.amount) FILTER (WHERE dc.is_estimated), 0) AS estimated_costs,
    COALESCE(SUM(dc.amount), 0) AS total_costs,
    d.contract_value - COALESCE(SUM(dc.amount), 0) AS gross_margin,
    CASE WHEN d.contract_value > 0
        THEN ((d.contract_value - COALESCE(SUM(dc.amount), 0)) / d.contract_value * 100)
        ELSE 0
    END AS margin_pct,
    COALESCE(comm.total_commission, 0) AS total_commission,
    d.contract_value - COALESCE(SUM(dc.amount), 0) - COALESCE(comm.total_commission, 0) AS net_margin
FROM deals d
LEFT JOIN deal_costs dc ON dc.deal_id = d.id
LEFT JOIN (
    SELECT
        deal_id,
        SUM(
            CASE commission_type
                WHEN 'flat' THEN rate
                WHEN 'per_ton' THEN rate * (SELECT quantity_tons FROM deals WHERE id = deal_commissions.deal_id)
                WHEN 'percentage' THEN rate * (SELECT contract_value FROM deals WHERE id = deal_commissions.deal_id)
                ELSE 0
            END
        ) AS total_commission
    FROM deal_commissions
    GROUP BY deal_id
) comm ON comm.deal_id = d.id
GROUP BY d.id, d.contract_id, d.contract_value, comm.total_commission;

-- ============================================================================
-- SEED COUNTERPARTIES (match existing deal buyers/sellers)
-- ============================================================================
INSERT INTO counterparties (id, name, short_name, type, country, notes) VALUES
    ('aa100000-0000-0000-0000-000000000001', 'West Africa Fuels Ltd', 'WAF', 'buyer', 'Nigeria', 'Primary Nigerian buyer'),
    ('aa100000-0000-0000-0000-000000000002', 'Brasil Carvao Exportadora SA', 'BCE', 'seller', 'Brazil', 'Major Brazilian exporter'),
    ('aa100000-0000-0000-0000-000000000003', 'Ghana Industrial Commodities', 'GIC', 'buyer', 'Ghana', 'Ghanaian industrial buyer'),
    ('aa100000-0000-0000-0000-000000000004', 'Paranagua Carbon Trade Ltda', 'PCT', 'seller', 'Brazil', 'Paranagua-based trader'),
    ('aa100000-0000-0000-0000-000000000005', 'Durban Energy Holdings (Pty) Ltd', 'DEH', 'buyer', 'South Africa', 'SA energy company'),
    ('aa100000-0000-0000-0000-000000000006', 'Atlantic Brokerage Services', 'ABS', 'broker', 'United Kingdom', 'London-based charcoal broker')
ON CONFLICT DO NOTHING;

-- Link existing deals to counterparties
UPDATE deals SET buyer_id = 'aa100000-0000-0000-0000-000000000001'
    WHERE contract_id = 'CHR-2026-0042' AND buyer_id IS NULL;
UPDATE deals SET seller_id = 'aa100000-0000-0000-0000-000000000002'
    WHERE contract_id = 'CHR-2026-0042' AND seller_id IS NULL;

UPDATE deals SET buyer_id = 'aa100000-0000-0000-0000-000000000003'
    WHERE contract_id = 'CHR-2026-0055' AND buyer_id IS NULL;
UPDATE deals SET seller_id = 'aa100000-0000-0000-0000-000000000004'
    WHERE contract_id = 'CHR-2026-0055' AND seller_id IS NULL;

UPDATE deals SET buyer_id = 'aa100000-0000-0000-0000-000000000005'
    WHERE contract_id = 'CHR-2026-0061' AND buyer_id IS NULL;
UPDATE deals SET seller_id = 'aa100000-0000-0000-0000-000000000002'
    WHERE contract_id = 'CHR-2026-0061' AND seller_id IS NULL;

-- Seed sample deal costs
INSERT INTO deal_costs (deal_id, cost_type, description, amount, is_estimated) VALUES
    ('c3000000-0000-0000-0000-000000000001', 'freight', 'Ocean freight Santos-Apapa', 180000.00, FALSE),
    ('c3000000-0000-0000-0000-000000000001', 'insurance', 'Cargo insurance (war risk included)', 45000.00, FALSE),
    ('c3000000-0000-0000-0000-000000000001', 'port_charges', 'Loading + discharge port fees', 35000.00, TRUE),
    ('c3000000-0000-0000-0000-000000000002', 'freight', 'Ocean freight Paranagua-Tema', 125000.00, TRUE),
    ('c3000000-0000-0000-0000-000000000002', 'insurance', 'Cargo insurance standard', 28000.00, TRUE),
    ('c3000000-0000-0000-0000-000000000003', 'freight', 'Ocean freight Santos-Durban', 195000.00, FALSE),
    ('c3000000-0000-0000-0000-000000000003', 'insurance', 'Cargo insurance standard', 52000.00, FALSE),
    ('c3000000-0000-0000-0000-000000000003', 'port_charges', 'Loading + discharge port fees', 42000.00, TRUE)
ON CONFLICT DO NOTHING;

-- Seed sample commissions
INSERT INTO deal_commissions (deal_id, recipient, commission_type, rate) VALUES
    ('c3000000-0000-0000-0000-000000000001', 'Atlantic Brokerage Services', 'per_ton', 3.50),
    ('c3000000-0000-0000-0000-000000000002', 'Atlantic Brokerage Services', 'percentage', 0.025),
    ('c3000000-0000-0000-0000-000000000003', 'Atlantic Brokerage Services', 'per_ton', 3.00)
ON CONFLICT DO NOTHING;
