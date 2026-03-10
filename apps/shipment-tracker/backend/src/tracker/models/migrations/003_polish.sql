-- Phase 5: Polish, Auth, Scheduling, Scale
-- Generated reports storage, performance indexes, analytics views

-- ── Generated Reports ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS generated_reports (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schedule_id UUID REFERENCES report_schedules(id),
    report_type VARCHAR(100) NOT NULL,
    file_data   BYTEA,
    file_name   VARCHAR(500),
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    downloaded_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_generated_reports_schedule ON generated_reports(schedule_id);
CREATE INDEX IF NOT EXISTS idx_generated_reports_type ON generated_reports(report_type, generated_at DESC);

-- ── Performance Indexes ──────────────────────────────────────────────────────
-- Deals
CREATE INDEX IF NOT EXISTS idx_deals_status ON deals(status) WHERE status NOT IN ('cancelled', 'completed');
CREATE INDEX IF NOT EXISTS idx_deals_buyer ON deals(buyer_id) WHERE buyer_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_deals_seller ON deals(seller_id) WHERE seller_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_deals_created ON deals(created_at DESC);

-- Meetings
CREATE INDEX IF NOT EXISTS idx_meetings_status ON meetings(status);
CREATE INDEX IF NOT EXISTS idx_meetings_scheduled ON meetings(scheduled_start DESC);
CREATE INDEX IF NOT EXISTS idx_meetings_calendar_event ON meetings(google_calendar_event_id) WHERE google_calendar_event_id IS NOT NULL;

-- Action items
CREATE INDEX IF NOT EXISTS idx_action_items_meeting ON action_items(meeting_id);
CREATE INDEX IF NOT EXISTS idx_action_items_status ON action_items(status) WHERE status IN ('open', 'in_progress');
CREATE INDEX IF NOT EXISTS idx_action_items_assignee ON action_items(assignee_email) WHERE assignee_email IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_action_items_due ON action_items(due_date) WHERE due_date IS NOT NULL AND status IN ('open', 'in_progress');

-- AI deal updates
CREATE INDEX IF NOT EXISTS idx_ai_updates_status ON ai_deal_updates(status);
CREATE INDEX IF NOT EXISTS idx_ai_updates_deal ON ai_deal_updates(deal_id);
CREATE INDEX IF NOT EXISTS idx_ai_updates_meeting ON ai_deal_updates(meeting_id);

-- Counterparties
CREATE INDEX IF NOT EXISTS idx_counterparties_type ON counterparties(type);
CREATE INDEX IF NOT EXISTS idx_counterparties_email ON counterparties(primary_contact_email) WHERE primary_contact_email IS NOT NULL;

-- Audit log
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_log(created_at DESC);

-- Users
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Refresh tokens
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires ON refresh_tokens(expires_at) WHERE revoked_at IS NULL;

-- ── Analytics Views ──────────────────────────────────────────────────────────

-- Platform health overview
CREATE OR REPLACE VIEW platform_health AS
SELECT
    (SELECT COUNT(*) FROM deals WHERE status NOT IN ('cancelled', 'completed')) as active_deals,
    (SELECT COUNT(*) FROM shipments WHERE status NOT IN ('discharged')) as active_shipments,
    (SELECT COUNT(*) FROM meetings WHERE status = 'scheduled') as upcoming_meetings,
    (SELECT COUNT(*) FROM action_items WHERE status IN ('open', 'in_progress')) as open_action_items,
    (SELECT COUNT(*) FROM action_items WHERE due_date < CURRENT_DATE AND status IN ('open', 'in_progress')) as overdue_actions,
    (SELECT COUNT(*) FROM ai_deal_updates WHERE status = 'pending') as pending_ai_updates,
    (SELECT COUNT(*) FROM alerts WHERE acknowledged = FALSE) as unread_alerts,
    (SELECT COUNT(*) FROM users WHERE is_active = TRUE) as active_users;

-- Weekly meeting activity
CREATE OR REPLACE VIEW weekly_meeting_activity AS
SELECT
    date_trunc('week', scheduled_start) as week_start,
    COUNT(*) as meeting_count,
    COUNT(*) FILTER (WHERE status = 'completed') as completed,
    AVG(actual_duration_seconds) FILTER (WHERE actual_duration_seconds > 0) as avg_duration_secs,
    COUNT(DISTINCT mp.name) as unique_participants
FROM meetings m
LEFT JOIN meeting_participants mp ON mp.meeting_id = m.id
WHERE scheduled_start >= CURRENT_DATE - INTERVAL '12 weeks'
GROUP BY date_trunc('week', scheduled_start)
ORDER BY week_start DESC;

-- Deal pipeline value by status
CREATE OR REPLACE VIEW deal_pipeline AS
SELECT
    status,
    COUNT(*) as deal_count,
    SUM(contract_value) as total_value,
    SUM(quantity_tons) as total_tons,
    AVG(price_per_ton) as avg_price_per_ton
FROM deals
WHERE status != 'cancelled'
GROUP BY status
ORDER BY
    CASE status
        WHEN 'draft' THEN 1
        WHEN 'confirmed' THEN 2
        WHEN 'loading' THEN 3
        WHEN 'in_transit' THEN 4
        WHEN 'arrived' THEN 5
        WHEN 'completed' THEN 6
    END;
