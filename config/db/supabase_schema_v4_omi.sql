-- ═══════════════════════════════════════════════════════════════
-- JARVIS 1.5 — OMI Wearable Integration Schema v4
-- Tables for OMI memory processing, entity tracking, and
-- continuous intelligence building.
-- Run AFTER supabase_schema_v3.sql
-- ═══════════════════════════════════════════════════════════════

-- ─── 1. OMI MEMORIES — Raw memories from OMI device ───
CREATE TABLE IF NOT EXISTS omi_memories (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    omi_memory_id VARCHAR(128) UNIQUE,
    uid VARCHAR(128) NOT NULL DEFAULT 'default',
    title VARCHAR(500),
    overview TEXT,
    category VARCHAR(64),
    transcript TEXT,
    raw_data JSONB DEFAULT '{}',
    memory_type VARCHAR(32) DEFAULT 'conversation',
    source VARCHAR(32) DEFAULT 'omi_device',
    importance INTEGER DEFAULT 5,
    content TEXT,
    processed BOOLEAN DEFAULT false,
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_omi_memories_uid ON omi_memories(uid);
CREATE INDEX IF NOT EXISTS idx_omi_memories_category ON omi_memories(category);
CREATE INDEX IF NOT EXISTS idx_omi_memories_importance ON omi_memories(importance DESC);
CREATE INDEX IF NOT EXISTS idx_omi_memories_created ON omi_memories(created_at DESC);

-- ─── 2. OMI TRANSCRIPTS — Real-time transcript segments ───
CREATE TABLE IF NOT EXISTS omi_transcripts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    uid VARCHAR(128) NOT NULL DEFAULT 'default',
    session_id VARCHAR(128),
    speaker VARCHAR(64),
    speaker_name VARCHAR(128),
    text TEXT NOT NULL,
    is_user BOOLEAN DEFAULT false,
    start_time FLOAT,
    end_time FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_omi_transcripts_session ON omi_transcripts(session_id);
CREATE INDEX IF NOT EXISTS idx_omi_transcripts_uid ON omi_transcripts(uid);
CREATE INDEX IF NOT EXISTS idx_omi_transcripts_created ON omi_transcripts(created_at DESC);

-- ─── 3. OMI ENTITIES — Extracted people, dates, contacts ───
CREATE TABLE IF NOT EXISTS omi_entities (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    uid VARCHAR(128) NOT NULL DEFAULT 'default',
    entity_type VARCHAR(50) NOT NULL,
    name VARCHAR(256) NOT NULL,
    context TEXT,
    mention_count INTEGER DEFAULT 1,
    first_mentioned TIMESTAMPTZ DEFAULT NOW(),
    last_mentioned TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(uid, entity_type, name)
);

CREATE INDEX IF NOT EXISTS idx_omi_entities_uid ON omi_entities(uid);
CREATE INDEX IF NOT EXISTS idx_omi_entities_type ON omi_entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_omi_entities_mentions ON omi_entities(mention_count DESC);

-- ─── 4. OMI EVENTS — Birthdays, meetings, deadlines ───
CREATE TABLE IF NOT EXISTS omi_events (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    uid VARCHAR(128) NOT NULL DEFAULT 'default',
    title VARCHAR(500) NOT NULL,
    event_date VARCHAR(64),
    duration_min INTEGER DEFAULT 0,
    recurring BOOLEAN DEFAULT false,
    source VARCHAR(32) DEFAULT 'omi_memory',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_omi_events_uid ON omi_events(uid);
CREATE INDEX IF NOT EXISTS idx_omi_events_date ON omi_events(event_date);

-- ─── 5. OMI CONVERSATION PATTERNS — Topic tracking over time ───
CREATE TABLE IF NOT EXISTS omi_conversation_patterns (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    uid VARCHAR(128) NOT NULL DEFAULT 'default',
    category VARCHAR(64),
    entity_types TEXT[] DEFAULT '{}',
    topic_keywords TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_omi_patterns_uid ON omi_conversation_patterns(uid);
CREATE INDEX IF NOT EXISTS idx_omi_patterns_category ON omi_conversation_patterns(category);

-- ─── 6. OMI DAY SUMMARIES — End of day summaries ───
CREATE TABLE IF NOT EXISTS omi_day_summaries (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    uid VARCHAR(128) NOT NULL DEFAULT 'default',
    summary_date DATE DEFAULT CURRENT_DATE,
    summary TEXT,
    conversations_count INTEGER DEFAULT 0,
    entities_count INTEGER DEFAULT 0,
    tasks_created INTEGER DEFAULT 0,
    knowledge_added INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(uid, summary_date)
);

-- ─── 7. DASHBOARD VIEWS for OMI ───

-- Recent OMI activity
CREATE OR REPLACE VIEW v_omi_activity AS
SELECT
    m.uid,
    m.title,
    m.category,
    m.importance,
    m.created_at,
    COALESCE(
        (SELECT COUNT(*) FROM omi_entities e
         WHERE e.uid = m.uid AND e.last_mentioned > m.created_at - INTERVAL '1 hour'),
        0
    ) as entities_extracted
FROM omi_memories m
ORDER BY m.created_at DESC
LIMIT 50;

-- Entity frequency (most mentioned people, companies, etc.)
CREATE OR REPLACE VIEW v_omi_top_entities AS
SELECT
    entity_type,
    name,
    mention_count,
    first_mentioned,
    last_mentioned,
    context
FROM omi_entities
WHERE mention_count > 1
ORDER BY mention_count DESC
LIMIT 100;

-- Daily conversation stats
CREATE OR REPLACE VIEW v_omi_daily_stats AS
SELECT
    DATE(created_at) as day,
    COUNT(*) as conversations,
    COUNT(DISTINCT category) as categories,
    AVG(importance) as avg_importance,
    SUM(CASE WHEN importance >= 7 THEN 1 ELSE 0 END) as high_importance
FROM omi_memories
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY day DESC;
