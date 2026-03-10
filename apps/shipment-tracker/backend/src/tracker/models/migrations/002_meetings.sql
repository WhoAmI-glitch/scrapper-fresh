-- Migration 002: Meeting Intelligence tables
-- Full meeting capture, transcription, and AI extraction support

-- ============================================================================
-- MEETINGS
-- ============================================================================
CREATE TABLE IF NOT EXISTS meetings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    scheduled_start TIMESTAMPTZ NOT NULL,
    scheduled_end TIMESTAMPTZ,
    actual_duration_seconds INTEGER,
    google_calendar_event_id TEXT UNIQUE,
    google_meet_url TEXT,
    status TEXT NOT NULL DEFAULT 'scheduled',
    -- scheduled, in_progress, processing, completed, failed
    recording_url TEXT,
    recording_storage_path TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- MEETING PARTICIPANTS
-- ============================================================================
CREATE TABLE IF NOT EXISTS meeting_participants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    email TEXT,
    role TEXT DEFAULT 'attendee',
    counterparty_id UUID REFERENCES counterparties(id),
    talk_time_seconds INTEGER DEFAULT 0,
    sentiment_score REAL
);
CREATE INDEX IF NOT EXISTS idx_meeting_participants_meeting ON meeting_participants(meeting_id);

-- ============================================================================
-- MEETING TRANSCRIPTS
-- ============================================================================
CREATE TABLE IF NOT EXISTS meeting_transcripts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    speaker_name TEXT NOT NULL,
    speaker_email TEXT,
    text TEXT NOT NULL,
    start_ms INTEGER NOT NULL,
    end_ms INTEGER NOT NULL,
    confidence REAL,
    sentiment TEXT
);
CREATE INDEX IF NOT EXISTS idx_transcript_meeting ON meeting_transcripts(meeting_id, start_ms);

-- ============================================================================
-- MEETING SUMMARIES (AI-generated)
-- ============================================================================
CREATE TABLE IF NOT EXISTS meeting_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    summary_text TEXT NOT NULL,
    decisions JSONB DEFAULT '[]',
    market_intelligence JSONB DEFAULT '[]',
    model_used TEXT NOT NULL,
    prompt_version TEXT,
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- ACTION ITEMS
-- ============================================================================
CREATE TABLE IF NOT EXISTS action_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID REFERENCES meetings(id),
    deal_id UUID REFERENCES deals(id),
    shipment_id UUID REFERENCES shipments(id),
    title TEXT NOT NULL,
    description TEXT,
    assignee_name TEXT,
    assignee_email TEXT,
    due_date DATE,
    status TEXT NOT NULL DEFAULT 'open',  -- open, in_progress, done, cancelled
    source TEXT DEFAULT 'ai',
    confidence REAL,
    transcript_start_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_action_items_status ON action_items(status) WHERE status != 'done';

-- ============================================================================
-- AI DEAL UPDATES (proposed changes from meeting AI)
-- ============================================================================
CREATE TABLE IF NOT EXISTS ai_deal_updates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID NOT NULL REFERENCES meetings(id),
    deal_id UUID NOT NULL REFERENCES deals(id),
    field_name TEXT NOT NULL,
    old_value TEXT,
    proposed_value TEXT NOT NULL,
    confidence REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    -- pending, approved, rejected, auto_applied
    reviewed_by TEXT,
    reviewed_at TIMESTAMPTZ,
    applied_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ai_updates_pending ON ai_deal_updates(status) WHERE status = 'pending';

-- ============================================================================
-- MEETING-DEAL LINKS
-- ============================================================================
CREATE TABLE IF NOT EXISTS meeting_deals (
    meeting_id UUID NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
    PRIMARY KEY (meeting_id, deal_id)
);

-- ============================================================================
-- MEETING EMBEDDINGS (pgvector for AI memory)
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS meeting_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meeting_id UUID NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    context_prefix TEXT,
    embedding vector(1536) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_embeddings_meeting ON meeting_embeddings(meeting_id);

-- ============================================================================
-- REPORT SCHEDULES
-- ============================================================================
CREATE TABLE IF NOT EXISTS report_schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    report_type TEXT NOT NULL,
    cron_expression TEXT NOT NULL,
    recipients TEXT[] DEFAULT '{}',
    last_run_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ,
    active BOOLEAN DEFAULT TRUE,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- USERS & AUTH
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'viewer',  -- admin, trader, operations, viewer
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens(user_id);

-- ============================================================================
-- MEETING INTELLIGENCE VIEW
-- ============================================================================
CREATE OR REPLACE VIEW meeting_intelligence AS
SELECT
    m.id,
    m.title,
    m.scheduled_start,
    m.actual_duration_seconds,
    m.status,
    ms.summary_text,
    ms.decisions,
    ms.market_intelligence,
    COALESCE(
        (SELECT json_agg(json_build_object(
            'id', ai.id, 'title', ai.title, 'assignee', ai.assignee_name,
            'due_date', ai.due_date, 'status', ai.status
        )) FROM action_items ai WHERE ai.meeting_id = m.id),
        '[]'
    ) AS action_items,
    COALESCE(
        (SELECT json_agg(json_build_object(
            'deal_id', md.deal_id
        )) FROM meeting_deals md WHERE md.meeting_id = m.id),
        '[]'
    ) AS linked_deals,
    (SELECT COUNT(*) FROM ai_deal_updates adu
     WHERE adu.meeting_id = m.id AND adu.status = 'pending') AS pending_updates
FROM meetings m
LEFT JOIN meeting_summaries ms ON ms.meeting_id = m.id;

-- ============================================================================
-- SEED: Default admin user (password: admin123)
-- ============================================================================
INSERT INTO users (id, email, password_hash, full_name, role)
VALUES (
    'u0000000-0000-0000-0000-000000000001',
    'admin@charcoal-intel.com',
    -- bcrypt hash of 'admin123'
    '$2b$12$LJ3m4yPP0FiGMoNbVJXQF.cVIS6eSqG0F3McfUnUhDxMT8vvPFhYa',
    'Admin User',
    'admin'
) ON CONFLICT (email) DO NOTHING;

-- Seed report schedules
INSERT INTO report_schedules (name, report_type, cron_expression, recipients) VALUES
    ('Weekly Trading Summary', 'trading_book', '0 8 * * 1', ARRAY['admin@charcoal-intel.com']),
    ('Monthly Exposure Report', 'shipment_progress', '0 9 1 * *', ARRAY['admin@charcoal-intel.com'])
ON CONFLICT DO NOTHING;
