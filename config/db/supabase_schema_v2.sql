-- ═══════════════════════════════════════════════════════════════
-- JARVIS 1.5 — Extended Schema v2
-- Conversation Memory + Knowledge Base + Relationships
-- Run AFTER supabase_schema.sql
-- ═══════════════════════════════════════════════════════════════

-- ─── 1. MESSAGES — jede einzelne Nachricht wird gespeichert ───
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    agent_slug TEXT NOT NULL DEFAULT 'jarvis',
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    tokens_used INT DEFAULT 0,
    model_used TEXT,
    parent_message_id UUID REFERENCES messages(id),
    embedding_vector TEXT,  -- serialized embedding for semantic search
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at);
CREATE INDEX idx_messages_agent ON messages(agent_slug, created_at DESC);
CREATE INDEX idx_messages_role ON messages(role, created_at DESC);
CREATE INDEX idx_messages_content_search ON messages USING gin(to_tsvector('german', content));
CREATE INDEX idx_messages_created ON messages(created_at DESC);

-- ─── 2. KNOWLEDGE — Langzeit-Wissen, Fakten, Entscheidungen ───
CREATE TABLE IF NOT EXISTS knowledge (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category TEXT NOT NULL CHECK (category IN (
        'fact', 'decision', 'preference', 'procedure',
        'contact', 'product', 'client', 'project',
        'rule', 'insight', 'goal', 'metric'
    )),
    subject TEXT NOT NULL,         -- worum geht es (z.B. "SYSTEMS Website")
    predicate TEXT NOT NULL,       -- was ist die Aussage (z.B. "URL ist")
    object TEXT NOT NULL,          -- der Wert (z.B. "https://systems.fm")
    confidence FLOAT DEFAULT 1.0,  -- 0-1 wie sicher
    source TEXT,                   -- woher kommt das Wissen
    source_message_id UUID REFERENCES messages(id),
    valid_from TIMESTAMPTZ DEFAULT now(),
    valid_until TIMESTAMPTZ,       -- NULL = ewig gueltig
    superseded_by UUID REFERENCES knowledge(id),
    tags TEXT[] DEFAULT '{}',
    agent_slug TEXT,               -- NULL = globales Wissen
    access_count INT DEFAULT 0,
    last_accessed TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_knowledge_category ON knowledge(category);
CREATE INDEX idx_knowledge_subject ON knowledge(subject);
CREATE INDEX idx_knowledge_tags ON knowledge USING gin(tags);
CREATE INDEX idx_knowledge_agent ON knowledge(agent_slug);
CREATE INDEX idx_knowledge_search ON knowledge USING gin(
    to_tsvector('german', subject || ' ' || predicate || ' ' || object)
);
CREATE INDEX idx_knowledge_valid ON knowledge(valid_from, valid_until)
    WHERE superseded_by IS NULL;

-- ─── 3. RELATIONSHIPS — Beziehungen zwischen Entitäten ───
CREATE TABLE IF NOT EXISTS entity_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_a TEXT NOT NULL,        -- z.B. "SYSTEMS™"
    entity_a_type TEXT NOT NULL,   -- z.B. "company"
    relation TEXT NOT NULL,        -- z.B. "hat_produkt"
    entity_b TEXT NOT NULL,        -- z.B. "JARVIS 1.5"
    entity_b_type TEXT NOT NULL,   -- z.B. "product"
    strength FLOAT DEFAULT 1.0,   -- 0-1 Beziehungsstärke
    metadata JSONB DEFAULT '{}',
    source TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_relationships_a ON entity_relationships(entity_a, relation);
CREATE INDEX idx_relationships_b ON entity_relationships(entity_b, relation);
CREATE INDEX idx_relationships_type ON entity_relationships(entity_a_type, entity_b_type);
CREATE UNIQUE INDEX idx_relationships_unique ON entity_relationships(entity_a, relation, entity_b);

-- ─── 4. LEARNING_JOURNAL — detailliertes Lern-Tagebuch ───
CREATE TABLE IF NOT EXISTS learning_journal (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_slug TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN (
        'success', 'failure', 'correction', 'discovery',
        'optimization', 'pattern_found', 'skill_learned',
        'mistake_prevented', 'escalation_avoided'
    )),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    context JSONB DEFAULT '{}',      -- task details, input, output
    lesson_learned TEXT,              -- was wurde gelernt
    applies_to TEXT[] DEFAULT '{}',   -- fuer welche Situationen
    impact_score FLOAT DEFAULT 0.5,   -- wie wichtig 0-1
    times_applied INT DEFAULT 0,      -- wie oft angewendet
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_journal_agent ON learning_journal(agent_slug, created_at DESC);
CREATE INDEX idx_journal_type ON learning_journal(event_type);
CREATE INDEX idx_journal_applies ON learning_journal USING gin(applies_to);
CREATE INDEX idx_journal_impact ON learning_journal(impact_score DESC);

-- ─── 5. CONTEXT_SNAPSHOTS — gespeicherte Kontexte für Wiederherstellung ───
CREATE TABLE IF NOT EXISTS context_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    agent_slug TEXT NOT NULL,
    snapshot_type TEXT NOT NULL CHECK (snapshot_type IN (
        'session_start', 'session_end', 'checkpoint', 'handoff'
    )),
    active_context JSONB NOT NULL,    -- aktueller Kontext
    memory_refs UUID[] DEFAULT '{}',  -- referenzierte Memories
    knowledge_refs UUID[] DEFAULT '{}', -- referenziertes Wissen
    summary TEXT,                     -- Zusammenfassung
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_snapshots_conversation ON context_snapshots(conversation_id);
CREATE INDEX idx_snapshots_agent ON context_snapshots(agent_slug, created_at DESC);

-- ─── 6. IMPROVEMENT_QUEUE — automatische Verbesserungsvorschläge ───
CREATE TABLE IF NOT EXISTS improvement_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category TEXT NOT NULL CHECK (category IN (
        'prompt_fix', 'model_switch', 'workflow_change',
        'new_skill', 'config_update', 'knowledge_gap',
        'performance_issue', 'cost_optimization'
    )),
    priority INT DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    affected_agents TEXT[] DEFAULT '{}',
    proposed_change JSONB,
    estimated_impact TEXT,
    status TEXT DEFAULT 'proposed' CHECK (status IN (
        'proposed', 'approved', 'implementing', 'testing',
        'deployed', 'rejected', 'reverted'
    )),
    implemented_at TIMESTAMPTZ,
    result_metrics JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_improvements_status ON improvement_queue(status, priority DESC);
CREATE INDEX idx_improvements_category ON improvement_queue(category);
CREATE INDEX idx_improvements_agents ON improvement_queue USING gin(affected_agents);

-- ─── FUNCTIONS ───

-- Volltext-Suche über Nachrichten
CREATE OR REPLACE FUNCTION search_messages(
    search_query TEXT,
    agent_filter TEXT DEFAULT NULL,
    max_results INT DEFAULT 20
) RETURNS TABLE(
    id UUID,
    conversation_id UUID,
    agent_slug TEXT,
    role TEXT,
    content TEXT,
    created_at TIMESTAMPTZ,
    rank FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        m.id, m.conversation_id, m.agent_slug, m.role, m.content,
        m.created_at,
        ts_rank(to_tsvector('german', m.content), plainto_tsquery('german', search_query)) AS rank
    FROM messages m
    WHERE to_tsvector('german', m.content) @@ plainto_tsquery('german', search_query)
      AND (agent_filter IS NULL OR m.agent_slug = agent_filter)
    ORDER BY rank DESC, m.created_at DESC
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- Wissen suchen
CREATE OR REPLACE FUNCTION search_knowledge(
    search_query TEXT,
    cat_filter TEXT DEFAULT NULL,
    max_results INT DEFAULT 20
) RETURNS TABLE(
    id UUID,
    category TEXT,
    subject TEXT,
    predicate TEXT,
    object TEXT,
    confidence FLOAT,
    created_at TIMESTAMPTZ,
    rank FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        k.id, k.category, k.subject, k.predicate, k.object,
        k.confidence, k.created_at,
        ts_rank(
            to_tsvector('german', k.subject || ' ' || k.predicate || ' ' || k.object),
            plainto_tsquery('german', search_query)
        ) AS rank
    FROM knowledge k
    WHERE to_tsvector('german', k.subject || ' ' || k.predicate || ' ' || k.object)
          @@ plainto_tsquery('german', search_query)
      AND (cat_filter IS NULL OR k.category = cat_filter)
      AND k.superseded_by IS NULL
      AND (k.valid_until IS NULL OR k.valid_until > now())
    ORDER BY rank DESC, k.confidence DESC
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- Konversations-Historie laden
CREATE OR REPLACE FUNCTION get_conversation_history(
    conv_id UUID,
    max_messages INT DEFAULT 50
) RETURNS TABLE(
    id UUID,
    role TEXT,
    content TEXT,
    agent_slug TEXT,
    model_used TEXT,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT m.id, m.role, m.content, m.agent_slug, m.model_used, m.created_at
    FROM messages m
    WHERE m.conversation_id = conv_id
    ORDER BY m.created_at ASC
    LIMIT max_messages;
END;
$$ LANGUAGE plpgsql;

-- Trigger für updated_at auf neuen Tabellen
CREATE TRIGGER update_knowledge_updated_at BEFORE UPDATE ON knowledge
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_relationships_updated_at BEFORE UPDATE ON entity_relationships
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_improvements_updated_at BEFORE UPDATE ON improvement_queue
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
