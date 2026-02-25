-- Scrapper database schema
-- Run: scrapper init-db

CREATE TABLE IF NOT EXISTS candidates (
    id              SERIAL PRIMARY KEY,
    company_name    TEXT NOT NULL,
    source          TEXT NOT NULL,
    hint_text       TEXT DEFAULT '',
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(source, company_name)
);

CREATE TABLE IF NOT EXISTS enrichment_tasks (
    id              SERIAL PRIMARY KEY,
    candidate_id    INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    state           TEXT NOT NULL DEFAULT 'NEW'
                        CHECK (state IN ('NEW','FETCHING','PARSED','DONE','FAILED')),
    attempts        INTEGER NOT NULL DEFAULT 0,
    profile_url     TEXT,
    error_message   TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tasks_state ON enrichment_tasks(state);

CREATE TABLE IF NOT EXISTS raw_pages (
    id              SERIAL PRIMARY KEY,
    task_id         INTEGER NOT NULL REFERENCES enrichment_tasks(id) ON DELETE CASCADE,
    url             TEXT NOT NULL,
    file_path       TEXT NOT NULL,
    fetched_at      TIMESTAMPTZ DEFAULT NOW(),
    http_status     INTEGER,
    content_length  INTEGER
);

CREATE TABLE IF NOT EXISTS leads (
    id                  SERIAL PRIMARY KEY,
    task_id             INTEGER UNIQUE REFERENCES enrichment_tasks(id) ON DELETE SET NULL,
    company_name        TEXT NOT NULL,
    inn                 VARCHAR(12),
    ogrn                VARCHAR(15),
    kpp                 VARCHAR(9),
    address             TEXT,
    ceo                 TEXT,
    phone               TEXT,
    email               TEXT,
    website             TEXT,
    revenue             TEXT,
    employees           TEXT,
    status              TEXT,
    okved               TEXT,
    registration_date   TEXT,
    raw_data            JSONB,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_leads_inn ON leads(inn) WHERE inn IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_leads_company ON leads(company_name);
