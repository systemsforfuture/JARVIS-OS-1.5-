-- ═══════════════════════════════════════════════════════════
-- JARVIS 1.5 — Supabase Database Schema
-- SYSTEMS™ · architectofscale.com
--
-- Dieses Schema wird in Supabase deployed.
-- Alle Tabellen haben Row Level Security (RLS).
-- Das Self-Learning System speichert ALLES hier.
-- ═══════════════════════════════════════════════════════════

-- ══════════════════════════════════════
-- 1. CORE TABLES
-- ══════════════════════════════════════

-- Agents
CREATE TABLE IF NOT EXISTS agents (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug        VARCHAR(32) UNIQUE NOT NULL,
    name        VARCHAR(64) NOT NULL,
    role        VARCHAR(128),
    emoji       VARCHAR(8),
    tier        INT DEFAULT 2,
    team        VARCHAR(32),
    status      VARCHAR(16) DEFAULT 'active',
    config      JSONB DEFAULT '{}',
    performance JSONB DEFAULT '{"score_avg": 0, "tasks_total": 0, "error_rate": 0}',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Tasks (jeder einzelne Task wird gespeichert)
CREATE TABLE IF NOT EXISTS tasks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title           VARCHAR(256) NOT NULL,
    description     TEXT,
    agent_slug      VARCHAR(32) REFERENCES agents(slug),
    status          VARCHAR(16) DEFAULT 'pending',
    priority        INT DEFAULT 2,
    task_type       VARCHAR(64),
    model_used      VARCHAR(64),
    input           JSONB DEFAULT '{}',
    output          JSONB DEFAULT '{}',
    tokens_input    INT DEFAULT 0,
    tokens_output   INT DEFAULT 0,
    duration_ms     INT DEFAULT 0,
    cost_cents      DECIMAL(10,4) DEFAULT 0,
    score           DECIMAL(5,4),
    score_source    VARCHAR(16) DEFAULT 'auto',
    quality_report  JSONB,
    parent_id       UUID REFERENCES tasks(id),
    retry_count     INT DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

-- ══════════════════════════════════════
-- 2. BRAIN / MEMORY SYSTEM
-- ══════════════════════════════════════

-- Memory (das Gehirn — alles wird hier gespeichert)
CREATE TABLE IF NOT EXISTS memory (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_slug      VARCHAR(32) REFERENCES agents(slug),
    memory_type     VARCHAR(32) NOT NULL,  -- fact, learning, preference, context, decision, error, pattern, relation
    key             VARCHAR(256),
    value           TEXT NOT NULL,
    priority        VARCHAR(16) DEFAULT 'normal',  -- critical, high, normal, low, ephemeral
    confidence      DECIMAL(3,2) DEFAULT 1.0,
    tags            TEXT[] DEFAULT '{}',
    metadata        JSONB DEFAULT '{}',
    related_ids     UUID[] DEFAULT '{}',
    access_count    INT DEFAULT 0,
    last_accessed   TIMESTAMPTZ DEFAULT NOW(),
    expires_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ══════════════════════════════════════
-- 3. SELF-LEARNING SYSTEM
-- ══════════════════════════════════════

-- Task Outcomes (jedes einzelne Ergebnis wird bewertet)
CREATE TABLE IF NOT EXISTS task_outcomes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id         UUID REFERENCES tasks(id),
    agent_slug      VARCHAR(32) REFERENCES agents(slug),
    task_type       VARCHAR(64) NOT NULL,
    model_used      VARCHAR(64) NOT NULL,
    prompt_hash     VARCHAR(64),           -- SHA256 fuer Deduplizierung
    prompt_preview  TEXT,                   -- Erste 500 Zeichen
    response_preview TEXT,                  -- Erste 500 Zeichen
    tokens_input    INT DEFAULT 0,
    tokens_output   INT DEFAULT 0,
    duration_ms     INT DEFAULT 0,
    cost_cents      DECIMAL(10,4) DEFAULT 0,
    score           DECIMAL(5,4) DEFAULT 0,
    score_source    VARCHAR(16) DEFAULT 'auto',
    error           TEXT,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Error Log (JEDER Fehler wird gespeichert — ELON analysiert)
CREATE TABLE IF NOT EXISTS error_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id         UUID REFERENCES tasks(id),
    agent_slug      VARCHAR(32) REFERENCES agents(slug),
    error_type      VARCHAR(64) NOT NULL,  -- model_error, timeout, quality_fail, validation_error, runtime_error
    error_message   TEXT NOT NULL,
    error_context   JSONB DEFAULT '{}',    -- task_type, model, prompt_preview, etc.
    severity        VARCHAR(16) DEFAULT 'medium',  -- critical, high, medium, low
    resolved        BOOLEAN DEFAULT false,
    resolution_id   UUID,                  -- Referenz auf error_solutions
    occurrences     INT DEFAULT 1,
    first_seen      TIMESTAMPTZ DEFAULT NOW(),
    last_seen       TIMESTAMPTZ DEFAULT NOW(),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Error Solutions (ELON entwickelt Loesungen fuer jeden Fehler)
CREATE TABLE IF NOT EXISTS error_solutions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    error_id        UUID REFERENCES error_log(id),
    error_type      VARCHAR(64) NOT NULL,
    root_cause      TEXT NOT NULL,          -- Was war die Ursache?
    solution         TEXT NOT NULL,          -- Was ist die Loesung?
    solution_type   VARCHAR(32) NOT NULL,   -- prompt_fix, model_change, config_update, process_change, code_fix
    implementation  JSONB DEFAULT '{}',     -- Konkrete Aenderungen (z.B. neuer Prompt-Text)
    applied         BOOLEAN DEFAULT false,  -- Wurde die Loesung umgesetzt?
    applied_at      TIMESTAMPTZ,
    applied_by      VARCHAR(32),            -- Agent oder DOM
    effectiveness   DECIMAL(5,4),           -- Wie effektiv war die Loesung? (0-1)
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Patterns (erkannte Muster aus dem Learning)
CREATE TABLE IF NOT EXISTS patterns (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_key     VARCHAR(128) UNIQUE NOT NULL,  -- agent:task_type
    agent_slug      VARCHAR(32) REFERENCES agents(slug),
    task_type       VARCHAR(64) NOT NULL,
    description     TEXT,
    best_model      VARCHAR(64),
    avg_score       DECIMAL(5,4) DEFAULT 0,
    avg_duration_ms INT DEFAULT 0,
    avg_cost_cents  DECIMAL(10,4) DEFAULT 0,
    occurrences     INT DEFAULT 1,
    model_scores    JSONB DEFAULT '{}',    -- {"tier1-sonnet": 0.85, "tier2-qwen": 0.72}
    recommendation  TEXT,
    status          VARCHAR(16) DEFAULT 'active',  -- active, superseded, invalid
    first_seen      TIMESTAMPTZ DEFAULT NOW(),
    last_seen       TIMESTAMPTZ DEFAULT NOW(),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ══════════════════════════════════════
-- 4. ELON OPTIMIZATION SYSTEM
-- ══════════════════════════════════════

-- Optimizations (ELON's Empfehlungen und umgesetzte Verbesserungen)
CREATE TABLE IF NOT EXISTS optimizations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_slug      VARCHAR(32) REFERENCES agents(slug),
    category        VARCHAR(32) NOT NULL,   -- model_routing, prompt_engineering, process, config, skill
    title           TEXT NOT NULL,
    current_state   TEXT NOT NULL,
    suggested_state TEXT NOT NULL,
    expected_impact TEXT,
    confidence      DECIMAL(5,4) DEFAULT 0,
    evidence        JSONB DEFAULT '[]',
    status          VARCHAR(16) DEFAULT 'proposed',  -- proposed, approved, applied, rejected, reverted
    approved_by     VARCHAR(32),
    applied_at      TIMESTAMPTZ,
    result_before   JSONB,                  -- Metriken VOR der Optimierung
    result_after    JSONB,                  -- Metriken NACH der Optimierung
    effectiveness   DECIMAL(5,4),           -- War es besser? (0-1, >0.5 = besser)
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Agent Performance History (woechentliche Snapshots)
CREATE TABLE IF NOT EXISTS agent_performance (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_slug      VARCHAR(32) REFERENCES agents(slug),
    period          VARCHAR(16) DEFAULT 'weekly',  -- daily, weekly, monthly
    period_start    TIMESTAMPTZ NOT NULL,
    period_end      TIMESTAMPTZ NOT NULL,
    tasks_total     INT DEFAULT 0,
    tasks_success   INT DEFAULT 0,
    tasks_failed    INT DEFAULT 0,
    avg_score       DECIMAL(5,4) DEFAULT 0,
    avg_duration_ms INT DEFAULT 0,
    total_cost_cents DECIMAL(10,4) DEFAULT 0,
    error_rate      DECIMAL(5,4) DEFAULT 0,
    ollama_ratio    DECIMAL(5,4) DEFAULT 0,     -- Wieviel % Ollama genutzt?
    model_usage     JSONB DEFAULT '{}',          -- {"tier1-sonnet": 45, "tier2-qwen": 120}
    top_errors      JSONB DEFAULT '[]',
    improvements    JSONB DEFAULT '[]',
    bottlenecks     JSONB DEFAULT '[]',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- KPI Snapshots (taeglich)
CREATE TABLE IF NOT EXISTS kpi_snapshots (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_date   DATE NOT NULL DEFAULT CURRENT_DATE,
    kpi_name        VARCHAR(64) NOT NULL,
    kpi_value       DECIMAL(12,4) NOT NULL,
    kpi_target      DECIMAL(12,4),
    kpi_unit        VARCHAR(16),
    kpi_trend       VARCHAR(8) DEFAULT 'stable',  -- up, down, stable
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(snapshot_date, kpi_name)
);

-- ══════════════════════════════════════
-- 5. SYSTEM TABLES
-- ══════════════════════════════════════

-- Conversations
CREATE TABLE IF NOT EXISTS conversations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id  VARCHAR(64) NOT NULL,
    agent_slug  VARCHAR(32) REFERENCES agents(slug),
    role        VARCHAR(16) NOT NULL,
    content     TEXT NOT NULL,
    tokens      INT DEFAULT 0,
    metadata    JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Skills
CREATE TABLE IF NOT EXISTS skills (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug        VARCHAR(64) UNIQUE NOT NULL,
    name        VARCHAR(128) NOT NULL,
    category    VARCHAR(32),
    description TEXT,
    config      JSONB DEFAULT '{}',
    enabled     BOOLEAN DEFAULT true,
    requires_key VARCHAR(64),
    usage_count INT DEFAULT 0,
    avg_score   DECIMAL(5,4) DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- API Keys Tracking
CREATE TABLE IF NOT EXISTS api_keys (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service     VARCHAR(64) UNIQUE NOT NULL,
    key_name    VARCHAR(128),
    is_set      BOOLEAN DEFAULT false,
    last_check  TIMESTAMPTZ,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Audit Log (unveraenderlich — alles wird protokolliert)
CREATE TABLE IF NOT EXISTS audit_log (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_slug  VARCHAR(32),
    action      VARCHAR(64) NOT NULL,
    category    VARCHAR(32),              -- task, error, optimization, config, security
    details     JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ══════════════════════════════════════
-- 6. INDEXES (Performance)
-- ══════════════════════════════════════

-- Tasks
CREATE INDEX IF NOT EXISTS idx_tasks_agent ON tasks(agent_slug);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_type ON tasks(task_type);
CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_score ON tasks(score);

-- Memory
CREATE INDEX IF NOT EXISTS idx_memory_agent ON memory(agent_slug);
CREATE INDEX IF NOT EXISTS idx_memory_type ON memory(memory_type);
CREATE INDEX IF NOT EXISTS idx_memory_key ON memory(key);
CREATE INDEX IF NOT EXISTS idx_memory_priority ON memory(priority);
CREATE INDEX IF NOT EXISTS idx_memory_tags ON memory USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_memory_expires ON memory(expires_at) WHERE expires_at IS NOT NULL;

-- Task Outcomes
CREATE INDEX IF NOT EXISTS idx_outcomes_agent ON task_outcomes(agent_slug);
CREATE INDEX IF NOT EXISTS idx_outcomes_type ON task_outcomes(task_type);
CREATE INDEX IF NOT EXISTS idx_outcomes_model ON task_outcomes(model_used);
CREATE INDEX IF NOT EXISTS idx_outcomes_score ON task_outcomes(score);
CREATE INDEX IF NOT EXISTS idx_outcomes_created ON task_outcomes(created_at DESC);

-- Error Log
CREATE INDEX IF NOT EXISTS idx_errors_agent ON error_log(agent_slug);
CREATE INDEX IF NOT EXISTS idx_errors_type ON error_log(error_type);
CREATE INDEX IF NOT EXISTS idx_errors_resolved ON error_log(resolved);
CREATE INDEX IF NOT EXISTS idx_errors_severity ON error_log(severity);
CREATE INDEX IF NOT EXISTS idx_errors_last_seen ON error_log(last_seen DESC);

-- Patterns
CREATE INDEX IF NOT EXISTS idx_patterns_agent ON patterns(agent_slug);
CREATE INDEX IF NOT EXISTS idx_patterns_type ON patterns(task_type);

-- Optimizations
CREATE INDEX IF NOT EXISTS idx_optimizations_agent ON optimizations(agent_slug);
CREATE INDEX IF NOT EXISTS idx_optimizations_status ON optimizations(status);
CREATE INDEX IF NOT EXISTS idx_optimizations_category ON optimizations(category);

-- Performance
CREATE INDEX IF NOT EXISTS idx_performance_agent ON agent_performance(agent_slug);
CREATE INDEX IF NOT EXISTS idx_performance_period ON agent_performance(period_start DESC);

-- KPIs
CREATE INDEX IF NOT EXISTS idx_kpi_date ON kpi_snapshots(snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_kpi_name ON kpi_snapshots(kpi_name);

-- Audit
CREATE INDEX IF NOT EXISTS idx_audit_agent ON audit_log(agent_slug);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_log(created_at DESC);

-- Conversations
CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_agent ON conversations(agent_slug);

-- Skills
CREATE INDEX IF NOT EXISTS idx_skills_category ON skills(category);

-- ══════════════════════════════════════
-- 7. DATABASE FUNCTIONS
-- ══════════════════════════════════════

-- Auto-Update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger fuer auto-update
CREATE TRIGGER tr_agents_updated BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER tr_memory_updated BEFORE UPDATE ON memory
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER tr_patterns_updated BEFORE UPDATE ON patterns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER tr_optimizations_updated BEFORE UPDATE ON optimizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Increment error occurrences (wenn gleicher Fehler nochmal kommt)
CREATE OR REPLACE FUNCTION increment_error_occurrence(p_agent_slug VARCHAR, p_error_type VARCHAR, p_error_message TEXT)
RETURNS UUID AS $$
DECLARE
    existing_id UUID;
BEGIN
    -- Suche nach gleichem Fehler (gleicher Agent + Typ + aehnliche Message)
    SELECT id INTO existing_id FROM error_log
    WHERE agent_slug = p_agent_slug
      AND error_type = p_error_type
      AND error_message = p_error_message
      AND resolved = false
    LIMIT 1;

    IF existing_id IS NOT NULL THEN
        UPDATE error_log SET
            occurrences = occurrences + 1,
            last_seen = NOW()
        WHERE id = existing_id;
        RETURN existing_id;
    END IF;

    RETURN NULL;  -- Kein existierender Fehler gefunden
END;
$$ LANGUAGE plpgsql;

-- Berechne Agent Performance Score (gewichteter Durchschnitt letzte 7 Tage)
CREATE OR REPLACE FUNCTION get_agent_score(p_agent_slug VARCHAR)
RETURNS DECIMAL AS $$
DECLARE
    score DECIMAL;
BEGIN
    SELECT COALESCE(AVG(to2.score), 0) INTO score
    FROM task_outcomes to2
    WHERE to2.agent_slug = p_agent_slug
      AND to2.created_at > NOW() - INTERVAL '7 days';
    RETURN score;
END;
$$ LANGUAGE plpgsql;

-- ══════════════════════════════════════
-- 8. SEED DATA
-- ══════════════════════════════════════

-- Agents
INSERT INTO agents (slug, name, role, emoji, tier, team) VALUES
    ('jarvis',  'JARVIS',   'Chief Intelligence Operator',     '🧠', 0, 'command'),
    ('elon',    'ELON',     'Analyst & Systemoptimierer',      '📊', 1, 'intelligence'),
    ('steve',   'STEVE',    'Marketing & Content Lead',        '📢', 1, 'marketing'),
    ('donald',  'DONALD',   'Sales & Revenue Lead',            '💰', 1, 'sales'),
    ('archi',   'ARCHI',    'Dev & Infrastructure Lead',       '🛠', 1, 'development'),
    ('donna',   'DONNA',    'Backoffice & Operations Lead',    '📋', 1, 'operations'),
    ('iris',    'IRIS',     'Design & Creative Lead',          '🎨', 1, 'marketing'),
    ('satoshi', 'SATOSHI',  'Crypto & Trading Specialist',     '₿',  1, 'crypto'),
    ('felix',   'FELIX',    'Customer Success Lead',           '🤝', 1, 'customer-success'),
    ('andreas', 'ANDREAS',  'Customer Success SFE Specialist', '🎯', 2, 'customer-success')
ON CONFLICT (slug) DO NOTHING;

-- API Key Tracking
INSERT INTO api_keys (service, key_name) VALUES
    ('supabase',   'SUPABASE_URL'),
    ('anthropic',  'ANTHROPIC_API_KEY'),
    ('openai',     'OPENAI_API_KEY'),
    ('groq',       'GROQ_API_KEY'),
    ('moonshot',   'MOONSHOT_API_KEY'),
    ('telegram',   'TELEGRAM_BOT_TOKEN'),
    ('instagram',  'INSTAGRAM_TOKEN'),
    ('linkedin',   'LINKEDIN_TOKEN'),
    ('twitter',    'TWITTER_BEARER_TOKEN'),
    ('facebook',   'FACEBOOK_TOKEN'),
    ('hubspot',    'HUBSPOT_API_KEY'),
    ('airtable',   'AIRTABLE_API_KEY')
ON CONFLICT (service) DO NOTHING;
