-- ═══════════════════════════════════════════════════════════════
-- JARVIS 1.5 — Extended Schema v3
-- Agent Management + Dashboard Views
-- Run AFTER supabase_schema_v2.sql
-- ═══════════════════════════════════════════════════════════════

-- ─── 1. EXTEND AGENTS TABLE — Dashboard Agent Management ───
-- Add columns for model config, prompts, and OpenClaw sync

ALTER TABLE agents ADD COLUMN IF NOT EXISTS model VARCHAR(64) DEFAULT 'tier1-sonnet';
ALTER TABLE agents ADD COLUMN IF NOT EXISTS system_prompt TEXT DEFAULT '';
ALTER TABLE agents ADD COLUMN IF NOT EXISTS tools JSONB DEFAULT '[]';
ALTER TABLE agents ADD COLUMN IF NOT EXISTS temperature DECIMAL(3,2) DEFAULT 0.5;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS max_tokens INT DEFAULT 4096;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS openclaw_synced BOOLEAN DEFAULT false;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS openclaw_synced_at TIMESTAMPTZ;

-- Also add tokens_used + cost_cents to tasks if missing (for stats)
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS tokens_used INT DEFAULT 0;

-- ─── 2. UPDATE SEED AGENTS WITH MODEL ASSIGNMENTS ───
UPDATE agents SET model = 'tier0-kimi', temperature = 0.3 WHERE slug = 'jarvis' AND model IS NULL;
UPDATE agents SET model = 'tier1-sonnet', temperature = 0.4 WHERE slug = 'elon' AND model IS NULL;
UPDATE agents SET model = 'tier1-sonnet', temperature = 0.7 WHERE slug = 'steve' AND model IS NULL;
UPDATE agents SET model = 'tier1-sonnet', temperature = 0.5 WHERE slug = 'donald' AND model IS NULL;
UPDATE agents SET model = 'tier1-sonnet', temperature = 0.3 WHERE slug = 'archi' AND model IS NULL;
UPDATE agents SET model = 'tier1-haiku', temperature = 0.4 WHERE slug = 'donna' AND model IS NULL;
UPDATE agents SET model = 'tier1-sonnet', temperature = 0.8 WHERE slug = 'iris' AND model IS NULL;
UPDATE agents SET model = 'tier1-sonnet', temperature = 0.3 WHERE slug = 'satoshi' AND model IS NULL;
UPDATE agents SET model = 'tier1-haiku', temperature = 0.6 WHERE slug = 'felix' AND model IS NULL;
UPDATE agents SET model = 'tier1-haiku', temperature = 0.5 WHERE slug = 'andreas' AND model IS NULL;

-- ─── 3. CONVERSATIONS v2 — add channel + status columns ───
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS channel VARCHAR(32) DEFAULT 'dashboard';
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS status VARCHAR(16) DEFAULT 'active';

-- Add channel column to messages for conversations page
ALTER TABLE messages ADD COLUMN IF NOT EXISTS channel VARCHAR(32) DEFAULT 'dashboard';

-- ─── 4. DASHBOARD VIEWS — pre-built queries for fast dashboard ───

-- Agent overview with recent stats
CREATE OR REPLACE VIEW v_agent_overview AS
SELECT
    a.slug, a.name, a.role, a.emoji, a.tier, a.team, a.status,
    a.model, a.temperature, a.max_tokens,
    a.openclaw_synced, a.openclaw_synced_at,
    COALESCE(t.task_count, 0) as tasks_total,
    COALESCE(t.completed, 0) as tasks_completed,
    COALESCE(t.failed, 0) as tasks_failed,
    COALESCE(t.total_tokens, 0) as tokens_used,
    COALESCE(l.learning_count, 0) as learnings,
    a.created_at, a.updated_at
FROM agents a
LEFT JOIN LATERAL (
    SELECT
        COUNT(*) as task_count,
        COUNT(*) FILTER (WHERE status = 'completed') as completed,
        COUNT(*) FILTER (WHERE status = 'failed') as failed,
        COALESCE(SUM(tokens_used), 0) as total_tokens
    FROM tasks WHERE agent_slug = a.slug
) t ON true
LEFT JOIN LATERAL (
    SELECT COUNT(*) as learning_count
    FROM learning_journal WHERE agent_slug = a.slug
) l ON true
ORDER BY a.tier, a.name;

-- Daily stats for dashboard charts
CREATE OR REPLACE VIEW v_daily_stats AS
SELECT
    DATE(created_at) as day,
    COUNT(*) as tasks_total,
    COUNT(*) FILTER (WHERE status = 'completed') as completed,
    COUNT(*) FILTER (WHERE status = 'failed') as failed,
    COALESCE(SUM(tokens_used), 0) as tokens,
    COALESCE(SUM(cost_cents), 0) as cost_cents
FROM tasks
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY day DESC;

-- Learning summary
CREATE OR REPLACE VIEW v_learning_summary AS
SELECT
    agent_slug,
    event_type,
    COUNT(*) as count,
    COALESCE(AVG(impact_score), 0) as avg_impact,
    MAX(created_at) as latest
FROM learning_journal
GROUP BY agent_slug, event_type
ORDER BY count DESC;

-- ─── 5. PATTERNS TABLE — ELON Pattern Recognition ───
CREATE TABLE IF NOT EXISTS patterns (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    pattern_type VARCHAR(50) NOT NULL,
    agent_slug VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    occurrence_count INTEGER DEFAULT 1,
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'watching',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(pattern_type, agent_slug, description)
);

-- ─── 6. INDEXES for new columns ───
CREATE INDEX IF NOT EXISTS idx_agents_model ON agents(model);
CREATE INDEX IF NOT EXISTS idx_agents_status_model ON agents(status, model);
CREATE INDEX IF NOT EXISTS idx_messages_channel ON messages(channel);
CREATE INDEX IF NOT EXISTS idx_tasks_tokens ON tasks(tokens_used) WHERE tokens_used > 0;
CREATE INDEX IF NOT EXISTS idx_patterns_status ON patterns(status);
CREATE INDEX IF NOT EXISTS idx_patterns_agent ON patterns(agent_slug);
CREATE INDEX IF NOT EXISTS idx_patterns_count ON patterns(occurrence_count DESC);
