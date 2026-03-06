// ═══════════════════════════════════════════════════════════
// JARVIS 1.5 — Mission Control Dashboard Server
// SYSTEMS™ · architectofscale.com
//
// Features:
//   - Agent Management (CRUD + OpenClaw Sync)
//   - Task Pipeline Monitoring
//   - Learning Journal & Self-Improvement Tracking
//   - Conversation History
//   - System Health (Docker, OpenClaw, N8N, LiteLLM)
//   - Real-time WebSocket Updates
// ═══════════════════════════════════════════════════════════

const express = require('express');
const http = require('http');
const https = require('https');
const WebSocket = require('ws');
const { Pool } = require('pg');
const Redis = require('ioredis');
const helmet = require('helmet');
const cors = require('cors');
const jwt = require('jsonwebtoken');
const path = require('path');

// ── CONFIG ──────────────────────────────────────────────────
const PORT = process.env.PORT || 3000;
const JWT_SECRET = process.env.JWT_SECRET || 'jarvis-dev-secret';
const DATABASE_URL = process.env.DATABASE_URL || 'postgresql://jarvis:jarvis@localhost:5432/jarvis';
const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379/0';
const OPENCLAW_URL = process.env.OPENCLAW_URL || 'http://localhost:8080';
const N8N_URL = process.env.N8N_URL || 'http://localhost:5678';
const LITELLM_URL = process.env.LITELLM_URL || 'http://jarvis-litellm:4000';

// ── DATABASE ────────────────────────────────────────────────
const pool = new Pool({ connectionString: DATABASE_URL });

// ── REDIS ───────────────────────────────────────────────────
let redis;
try {
  redis = new Redis(REDIS_URL, { lazyConnect: true, maxRetriesPerRequest: 3 });
  redis.connect().catch(() => console.log('[REDIS] Not available, running without cache'));
} catch {
  console.log('[REDIS] Not available, running without cache');
  redis = null;
}

// ── EXPRESS ─────────────────────────────────────────────────
const app = express();
const server = http.createServer(app);

app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'unsafe-inline'"],
      styleSrc: ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
      fontSrc: ["'self'", "https://fonts.gstatic.com"],
      imgSrc: ["'self'", "data:"],
      connectSrc: ["'self'", "ws:", "wss:"]
    }
  }
}));
app.use(cors());
app.use(express.json({ limit: '1mb' }));
app.use(express.static(path.join(__dirname, 'public')));

// ── WEBSOCKET ───────────────────────────────────────────────
const wss = new WebSocket.Server({ server, path: '/ws' });

const broadcast = (data) => {
  const msg = JSON.stringify(data);
  wss.clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(msg);
    }
  });
};

wss.on('connection', (ws) => {
  console.log('[WS] Client connected');
  ws.send(JSON.stringify({ type: 'connected', version: '1.5.0' }));

  ws.on('message', async (message) => {
    try {
      const data = JSON.parse(message);
      if (data.type === 'chat') {
        broadcast({ type: 'chat', agent: 'jarvis', content: data.content, timestamp: new Date().toISOString() });
      }
    } catch (err) {
      console.error('[WS] Message error:', err.message);
    }
  });

  ws.on('close', () => console.log('[WS] Client disconnected'));
});

// ── AUTH MIDDLEWARE ──────────────────────────────────────────
const authenticate = (req, res, next) => {
  const token = req.headers.authorization?.replace('Bearer ', '');
  if (!token) {
    return res.status(401).json({ error: 'Authentication required' });
  }
  try {
    req.user = jwt.verify(token, JWT_SECRET);
    next();
  } catch {
    return res.status(401).json({ error: 'Invalid token' });
  }
};

// ── HTTP HELPER (for OpenClaw/N8N/LiteLLM calls) ───────────
function httpRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const parsed = new URL(url);
    const client = parsed.protocol === 'https:' ? https : http;
    const req = client.request(url, {
      method: options.method || 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      timeout: 5000,
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, data: JSON.parse(data) });
        } catch {
          resolve({ status: res.statusCode, data });
        }
      });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
    if (options.body) req.write(JSON.stringify(options.body));
    req.end();
  });
}

// ════════════════════════════════════════════════════════════
// API ROUTES
// ════════════════════════════════════════════════════════════

// ── Auth ────────────────────────────────────────────────────
app.post('/api/auth/login', (req, res) => {
  const { password } = req.body;
  if (password === (process.env.DASHBOARD_SECRET || 'jarvis')) {
    const token = jwt.sign({ role: 'admin', iat: Date.now() }, JWT_SECRET, { expiresIn: '24h' });
    res.json({ token, expiresIn: '24h' });
  } else {
    res.status(401).json({ error: 'Invalid password' });
  }
});

// ── Health ──────────────────────────────────────────────────
app.get('/api/health', async (req, res) => {
  const checks = { server: 'ok', database: 'unknown', redis: 'unknown' };
  try {
    await pool.query('SELECT 1');
    checks.database = 'ok';
  } catch {
    checks.database = 'error';
  }
  try {
    if (redis) { await redis.ping(); checks.redis = 'ok'; }
    else { checks.redis = 'disabled'; }
  } catch {
    checks.redis = 'error';
  }
  const status = Object.values(checks).every(v => v === 'ok' || v === 'disabled') ? 200 : 503;
  res.status(status).json({ status: status === 200 ? 'healthy' : 'degraded', checks, version: '1.5.0' });
});

// ── System Services Status ──────────────────────────────────
app.get('/api/system/services', async (req, res) => {
  const services = {};

  // PostgreSQL
  try {
    const r = await pool.query('SELECT version(), pg_database_size(current_database()) as db_size');
    services.database = { status: 'ok', version: r.rows[0].version?.split(' ')[1], size_mb: Math.round(r.rows[0].db_size / 1024 / 1024) };
  } catch { services.database = { status: 'error' }; }

  // Redis
  try {
    if (redis) {
      await redis.ping();
      const info = await redis.info('memory');
      const usedMem = info.match(/used_memory_human:(.+)/)?.[1]?.trim();
      services.redis = { status: 'ok', memory: usedMem };
    } else {
      services.redis = { status: 'disabled' };
    }
  } catch { services.redis = { status: 'error' }; }

  // OpenClaw
  try {
    const r = await httpRequest(`${OPENCLAW_URL}/api/health`);
    services.openclaw = { status: r.status < 400 ? 'ok' : 'error', url: OPENCLAW_URL };
  } catch {
    try {
      const r = await httpRequest(`${OPENCLAW_URL}/health`);
      services.openclaw = { status: r.status < 400 ? 'ok' : 'error', url: OPENCLAW_URL };
    } catch {
      services.openclaw = { status: 'unreachable', url: OPENCLAW_URL };
    }
  }

  // N8N
  try {
    const r = await httpRequest(`${N8N_URL}/healthz`);
    services.n8n = { status: r.status < 400 ? 'ok' : 'error', url: N8N_URL };
  } catch {
    services.n8n = { status: 'unreachable', url: N8N_URL };
  }

  // LiteLLM
  try {
    const r = await httpRequest(`${LITELLM_URL}/health`);
    services.litellm = { status: r.status < 400 ? 'ok' : 'error', url: LITELLM_URL };
  } catch {
    services.litellm = { status: 'unreachable', url: LITELLM_URL };
  }

  res.json(services);
});

// ════════════════════════════════════════════════════════════
// AGENTS — Full CRUD + OpenClaw Sync
// ════════════════════════════════════════════════════════════

app.get('/api/agents', async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM agents ORDER BY tier, name');
    res.json(result.rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.get('/api/agents/:slug', async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM agents WHERE slug = $1', [req.params.slug]);
    if (result.rows.length === 0) return res.status(404).json({ error: 'Agent not found' });
    res.json(result.rows[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Update agent configuration
app.put('/api/agents/:slug', authenticate, async (req, res) => {
  try {
    const { slug } = req.params;
    const { name, role, model, tier, team, status, system_prompt, tools, temperature, max_tokens } = req.body;

    const fields = [];
    const values = [];
    let idx = 1;

    if (name !== undefined) { fields.push(`name = $${idx++}`); values.push(name); }
    if (role !== undefined) { fields.push(`role = $${idx++}`); values.push(role); }
    if (model !== undefined) { fields.push(`model = $${idx++}`); values.push(model); }
    if (tier !== undefined) { fields.push(`tier = $${idx++}`); values.push(tier); }
    if (team !== undefined) { fields.push(`team = $${idx++}`); values.push(team); }
    if (status !== undefined) { fields.push(`status = $${idx++}`); values.push(status); }
    if (system_prompt !== undefined) { fields.push(`system_prompt = $${idx++}`); values.push(system_prompt); }
    if (tools !== undefined) { fields.push(`tools = $${idx++}`); values.push(JSON.stringify(tools)); }
    if (temperature !== undefined) { fields.push(`temperature = $${idx++}`); values.push(temperature); }
    if (max_tokens !== undefined) { fields.push(`max_tokens = $${idx++}`); values.push(max_tokens); }

    if (fields.length === 0) return res.status(400).json({ error: 'No fields to update' });

    fields.push(`updated_at = NOW()`);
    values.push(slug);

    const query = `UPDATE agents SET ${fields.join(', ')} WHERE slug = $${idx} RETURNING *`;
    const result = await pool.query(query, values);

    if (result.rows.length === 0) return res.status(404).json({ error: 'Agent not found' });

    broadcast({ type: 'agent_updated', agent: result.rows[0] });
    res.json(result.rows[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Toggle agent status
app.patch('/api/agents/:slug/status', authenticate, async (req, res) => {
  try {
    const { status } = req.body;
    if (!['active', 'standby', 'disabled'].includes(status)) {
      return res.status(400).json({ error: 'Status must be: active, standby, or disabled' });
    }
    const result = await pool.query(
      'UPDATE agents SET status = $1, updated_at = NOW() WHERE slug = $2 RETURNING *',
      [status, req.params.slug]
    );
    if (result.rows.length === 0) return res.status(404).json({ error: 'Agent not found' });
    broadcast({ type: 'agent_status_changed', agent: result.rows[0] });
    res.json(result.rows[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Sync agent to OpenClaw
app.post('/api/agents/:slug/sync-openclaw', authenticate, async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM agents WHERE slug = $1', [req.params.slug]);
    if (result.rows.length === 0) return res.status(404).json({ error: 'Agent not found' });

    const agent = result.rows[0];
    const payload = {
      slug: agent.slug,
      name: agent.name,
      role: agent.role,
      model: agent.model,
      system_prompt: agent.system_prompt || '',
      tools: agent.tools ? (typeof agent.tools === 'string' ? JSON.parse(agent.tools) : agent.tools) : [],
      config: {
        temperature: agent.temperature || 0.5,
        max_tokens: agent.max_tokens || 4096,
        litellm_url: LITELLM_URL,
      }
    };

    // Try multiple OpenClaw API patterns
    let synced = false;
    const endpoints = [
      { method: 'PUT', url: `${OPENCLAW_URL}/api/agents/${agent.slug}` },
      { method: 'POST', url: `${OPENCLAW_URL}/api/agents` },
      { method: 'PUT', url: `${OPENCLAW_URL}/agents/${agent.slug}` },
      { method: 'POST', url: `${OPENCLAW_URL}/api/v1/agents` },
    ];

    for (const ep of endpoints) {
      try {
        const r = await httpRequest(ep.url, { method: ep.method, body: payload });
        if (r.status < 400) {
          synced = true;
          await pool.query(
            'UPDATE agents SET openclaw_synced = true, openclaw_synced_at = NOW() WHERE slug = $1',
            [agent.slug]
          );
          res.json({ synced: true, endpoint: ep.url, response: r.data });
          return;
        }
      } catch { continue; }
    }

    res.json({ synced: false, message: 'OpenClaw not reachable or API format unknown. Agent saved locally.' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Sync ALL agents to OpenClaw
app.post('/api/agents/sync-all', authenticate, async (req, res) => {
  try {
    const agents = await pool.query('SELECT slug FROM agents WHERE status != $1', ['disabled']);
    const results = [];

    for (const agent of agents.rows) {
      try {
        const agentData = await pool.query('SELECT * FROM agents WHERE slug = $1', [agent.slug]);
        const a = agentData.rows[0];
        const payload = {
          slug: a.slug, name: a.name, role: a.role, model: a.model,
          system_prompt: a.system_prompt || '',
          config: { temperature: a.temperature || 0.5, max_tokens: a.max_tokens || 4096 }
        };

        const r = await httpRequest(`${OPENCLAW_URL}/api/agents/${a.slug}`, { method: 'PUT', body: payload }).catch(() => null);
        results.push({ slug: a.slug, synced: r && r.status < 400 });
      } catch {
        results.push({ slug: agent.slug, synced: false });
      }
    }

    res.json({ results, total: results.length, synced: results.filter(r => r.synced).length });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Agent stats (tasks, tokens, costs)
app.get('/api/agents/:slug/stats', async (req, res) => {
  try {
    const { slug } = req.params;
    const [tasks, learning, conversations] = await Promise.all([
      pool.query(`
        SELECT COUNT(*) as total,
               COUNT(*) FILTER (WHERE status = 'completed') as completed,
               COUNT(*) FILTER (WHERE status = 'failed') as failed,
               COALESCE(SUM(tokens_used), 0) as total_tokens,
               COALESCE(SUM(cost_cents), 0) as total_cost_cents
        FROM tasks WHERE agent_slug = $1`, [slug]),
      pool.query(`
        SELECT COUNT(*) as total,
               COALESCE(AVG(impact_score), 0) as avg_impact
        FROM learning_journal WHERE agent_slug = $1`, [slug]),
      pool.query(`
        SELECT COUNT(DISTINCT conversation_id) as conversations,
               COUNT(*) as messages
        FROM messages WHERE agent_slug = $1`, [slug]),
    ]);

    res.json({
      tasks: tasks.rows[0],
      learning: learning.rows[0],
      conversations: conversations.rows[0],
    });
  } catch (err) {
    // Graceful fallback if tables don't exist yet
    res.json({ tasks: { total: 0 }, learning: { total: 0 }, conversations: { conversations: 0 } });
  }
});

// ════════════════════════════════════════════════════════════
// TASKS
// ════════════════════════════════════════════════════════════

app.get('/api/tasks', async (req, res) => {
  try {
    const { status, agent, limit = 50 } = req.query;
    let query = 'SELECT * FROM tasks';
    const conditions = [];
    const params = [];

    if (status) { params.push(status); conditions.push(`status = $${params.length}`); }
    if (agent) { params.push(agent); conditions.push(`agent_slug = $${params.length}`); }

    if (conditions.length) query += ' WHERE ' + conditions.join(' AND ');
    query += ' ORDER BY created_at DESC';
    params.push(parseInt(limit));
    query += ` LIMIT $${params.length}`;

    const result = await pool.query(query, params);
    res.json(result.rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/tasks', authenticate, async (req, res) => {
  try {
    const { title, description, agent_slug, priority = 2 } = req.body;
    const result = await pool.query(
      'INSERT INTO tasks (title, description, agent_slug, priority) VALUES ($1, $2, $3, $4) RETURNING *',
      [title, description, agent_slug, priority]
    );
    broadcast({ type: 'task_created', task: result.rows[0] });
    res.status(201).json(result.rows[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ════════════════════════════════════════════════════════════
// SKILLS
// ════════════════════════════════════════════════════════════

app.get('/api/skills', async (req, res) => {
  try {
    const { category } = req.query;
    let query = 'SELECT * FROM skills';
    const params = [];
    if (category) { params.push(category); query += ` WHERE category = $1`; }
    query += ' ORDER BY category, name';
    const result = await pool.query(query, params);
    res.json(result.rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.patch('/api/skills/:slug/toggle', authenticate, async (req, res) => {
  try {
    const result = await pool.query(
      'UPDATE skills SET enabled = NOT enabled WHERE slug = $1 RETURNING *',
      [req.params.slug]
    );
    if (result.rows.length === 0) return res.status(404).json({ error: 'Skill not found' });
    res.json(result.rows[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ════════════════════════════════════════════════════════════
// MEMORY
// ════════════════════════════════════════════════════════════

app.get('/api/memory', async (req, res) => {
  try {
    const { agent, type, limit = 100 } = req.query;
    let query = 'SELECT * FROM memory';
    const conditions = [];
    const params = [];

    if (agent) { params.push(agent); conditions.push(`agent_slug = $${params.length}`); }
    if (type) { params.push(type); conditions.push(`type = $${params.length}`); }

    if (conditions.length) query += ' WHERE ' + conditions.join(' AND ');
    query += ' ORDER BY created_at DESC';
    params.push(parseInt(limit));
    query += ` LIMIT $${params.length}`;

    const result = await pool.query(query, params);
    res.json(result.rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/memory', authenticate, async (req, res) => {
  try {
    const { agent_slug, type, key, value, metadata = {} } = req.body;
    const result = await pool.query(
      'INSERT INTO memory (agent_slug, type, key, value, metadata) VALUES ($1, $2, $3, $4, $5) RETURNING *',
      [agent_slug, type, key, value, JSON.stringify(metadata)]
    );
    res.status(201).json(result.rows[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ════════════════════════════════════════════════════════════
// LEARNING & SELF-IMPROVEMENT
// ════════════════════════════════════════════════════════════

app.get('/api/learning', async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM learning ORDER BY score_avg DESC LIMIT 50');
    res.json(result.rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Learning Journal entries
app.get('/api/learning/journal', async (req, res) => {
  try {
    const { agent, event_type, limit = 50 } = req.query;
    let query = 'SELECT * FROM learning_journal';
    const conditions = [];
    const params = [];

    if (agent) { params.push(agent); conditions.push(`agent_slug = $${params.length}`); }
    if (event_type) { params.push(event_type); conditions.push(`event_type = $${params.length}`); }

    if (conditions.length) query += ' WHERE ' + conditions.join(' AND ');
    query += ' ORDER BY created_at DESC';
    params.push(parseInt(limit));
    query += ` LIMIT $${params.length}`;

    const result = await pool.query(query, params);
    res.json(result.rows);
  } catch {
    res.json([]);
  }
});

// Learning stats summary
app.get('/api/learning/stats', async (req, res) => {
  try {
    const [journal, improvements, patterns] = await Promise.all([
      pool.query(`
        SELECT event_type, COUNT(*) as count,
               COALESCE(AVG(impact_score), 0) as avg_impact
        FROM learning_journal
        GROUP BY event_type ORDER BY count DESC`),
      pool.query(`
        SELECT status, COUNT(*) as count
        FROM improvement_queue
        GROUP BY status`),
      pool.query(`
        SELECT pattern_type, COUNT(*) as count
        FROM patterns
        GROUP BY pattern_type ORDER BY count DESC`).catch(() => ({ rows: [] })),
    ]);

    res.json({
      journal_by_type: journal.rows,
      improvements: improvements.rows,
      patterns: patterns.rows,
    });
  } catch {
    res.json({ journal_by_type: [], improvements: [], patterns: [] });
  }
});

// Improvement Queue
app.get('/api/improvements', async (req, res) => {
  try {
    const { status, limit = 30 } = req.query;
    let query = 'SELECT * FROM improvement_queue';
    const params = [];
    if (status) { params.push(status); query += ' WHERE status = $1'; }
    query += ' ORDER BY created_at DESC';
    params.push(parseInt(limit));
    query += ` LIMIT $${params.length}`;
    const result = await pool.query(query, params);
    res.json(result.rows);
  } catch {
    res.json([]);
  }
});

// Approve/reject improvement
app.patch('/api/improvements/:id', authenticate, async (req, res) => {
  try {
    const { status } = req.body;
    if (!['approved', 'rejected'].includes(status)) {
      return res.status(400).json({ error: 'Status must be: approved or rejected' });
    }
    const result = await pool.query(
      'UPDATE improvement_queue SET status = $1, reviewed_at = NOW() WHERE id = $2 RETURNING *',
      [status, req.params.id]
    );
    if (result.rows.length === 0) return res.status(404).json({ error: 'Improvement not found' });
    res.json(result.rows[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ════════════════════════════════════════════════════════════
// CONVERSATIONS
// ════════════════════════════════════════════════════════════

app.get('/api/conversations', async (req, res) => {
  try {
    const { limit = 20 } = req.query;
    const result = await pool.query(`
      SELECT conversation_id, channel,
             MIN(created_at) as started_at,
             MAX(created_at) as last_message_at,
             COUNT(*) as message_count,
             array_agg(DISTINCT agent_slug) as agents
      FROM messages
      GROUP BY conversation_id, channel
      ORDER BY MAX(created_at) DESC
      LIMIT $1`, [parseInt(limit)]);
    res.json(result.rows);
  } catch {
    res.json([]);
  }
});

app.get('/api/conversations/:id', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT * FROM messages WHERE conversation_id = $1 ORDER BY created_at ASC',
      [req.params.id]
    );
    res.json(result.rows);
  } catch {
    res.json([]);
  }
});

// ════════════════════════════════════════════════════════════
// KNOWLEDGE BASE
// ════════════════════════════════════════════════════════════

app.get('/api/knowledge', async (req, res) => {
  try {
    const { category, search, limit = 50 } = req.query;
    let query = 'SELECT * FROM knowledge WHERE valid_until IS NULL OR valid_until > NOW()';
    const params = [];

    if (category) { params.push(category); query += ` AND category = $${params.length}`; }
    if (search) { params.push(`%${search}%`); query += ` AND (subject ILIKE $${params.length} OR predicate ILIKE $${params.length} OR object ILIKE $${params.length})`; }

    query += ' ORDER BY confidence DESC, created_at DESC';
    params.push(parseInt(limit));
    query += ` LIMIT $${params.length}`;

    const result = await pool.query(query, params);
    res.json(result.rows);
  } catch {
    res.json([]);
  }
});

// ════════════════════════════════════════════════════════════
// STATS & KEYS
// ════════════════════════════════════════════════════════════

app.get('/api/keys', async (req, res) => {
  try {
    const result = await pool.query('SELECT service, key_name, is_set, last_check FROM api_keys ORDER BY service');
    res.json(result.rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.get('/api/stats', async (req, res) => {
  try {
    const [agents, tasks, skills, memory] = await Promise.all([
      pool.query("SELECT COUNT(*) as count, COUNT(*) FILTER (WHERE status = 'active') as active FROM agents"),
      pool.query("SELECT COUNT(*) as total, COUNT(*) FILTER (WHERE status = 'completed') as completed, COUNT(*) FILTER (WHERE status = 'pending') as pending, COALESCE(SUM(tokens_used), 0) as total_tokens, COALESCE(SUM(cost_cents), 0) as total_cost FROM tasks"),
      pool.query('SELECT COUNT(*) as total, COUNT(*) FILTER (WHERE enabled = true) as enabled FROM skills'),
      pool.query('SELECT COUNT(*) as total FROM memory')
    ]);

    // Try to get learning stats
    let learningCount = 0;
    let conversationCount = 0;
    try {
      const lr = await pool.query('SELECT COUNT(*) as count FROM learning_journal');
      learningCount = lr.rows[0].count;
    } catch {}
    try {
      const cr = await pool.query('SELECT COUNT(DISTINCT conversation_id) as count FROM messages');
      conversationCount = cr.rows[0].count;
    } catch {}

    res.json({
      agents: agents.rows[0],
      tasks: tasks.rows[0],
      skills: skills.rows[0],
      memory: memory.rows[0],
      learnings: learningCount,
      conversations: conversationCount,
      version: '1.5.0'
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Audit Log
app.get('/api/audit', authenticate, async (req, res) => {
  try {
    const { limit = 100 } = req.query;
    const result = await pool.query('SELECT * FROM audit_log ORDER BY created_at DESC LIMIT $1', [parseInt(limit)]);
    res.json(result.rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ════════════════════════════════════════════════════════════
// ONBOARDING — Setup Wizard
// ════════════════════════════════════════════════════════════

// Get onboarding status
app.get('/api/onboarding/status', async (req, res) => {
  try {
    const result = await pool.query(
      "SELECT key, value FROM memory WHERE type = 'config' AND key LIKE 'onboarding_%' ORDER BY key"
    );
    const config = {};
    for (const row of result.rows) {
      config[row.key.replace('onboarding_', '')] = typeof row.value === 'string' ? JSON.parse(row.value) : row.value;
    }

    // Check if onboarding is complete
    const completed = await pool.query(
      "SELECT value FROM memory WHERE type = 'config' AND key = 'onboarding_completed'"
    );
    config.completed = completed.rows.length > 0 && completed.rows[0].value === 'true';

    res.json(config);
  } catch {
    res.json({ completed: false });
  }
});

// Save onboarding data
app.post('/api/onboarding/save', authenticate, async (req, res) => {
  try {
    const {
      company_name, company_domain, language,
      social_accounts, api_keys, model_config,
      integrations, telegram_config
    } = req.body;

    const configs = [
      ['onboarding_company', JSON.stringify({ name: company_name, domain: company_domain, language })],
      ['onboarding_social', JSON.stringify(social_accounts || {})],
      ['onboarding_apis', JSON.stringify(api_keys || {})],
      ['onboarding_models', JSON.stringify(model_config || {})],
      ['onboarding_integrations', JSON.stringify(integrations || {})],
      ['onboarding_telegram', JSON.stringify(telegram_config || {})],
      ['onboarding_completed', 'true'],
    ];

    for (const [key, value] of configs) {
      await pool.query(
        `INSERT INTO memory (agent_slug, type, key, value, metadata)
         VALUES ('system', 'config', $1, $2, '{}')
         ON CONFLICT (type, key) DO UPDATE SET value = $2, updated_at = NOW()`,
        [key, value]
      ).catch(() => {
        // Fallback without ON CONFLICT
        pool.query(
          `DELETE FROM memory WHERE type = 'config' AND key = $1`, [key]
        ).then(() => pool.query(
          `INSERT INTO memory (agent_slug, type, key, value, metadata) VALUES ('system', 'config', $1, $2, '{}')`,
          [key, value]
        ));
      });
    }

    // Push config to OpenClaw
    let openclawSync = false;
    try {
      const openclawPayload = {
        company: { name: company_name, domain: company_domain, language },
        models: model_config,
        integrations,
      };
      const r = await httpRequest(`${OPENCLAW_URL}/api/config`, {
        method: 'PUT',
        body: openclawPayload,
      });
      openclawSync = r.status < 400;
    } catch {}

    broadcast({ type: 'onboarding_complete', company: company_name });
    res.json({ saved: true, openclaw_synced: openclawSync });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ════════════════════════════════════════════════════════════
// DEPENDENCY CHECKER — Required Services
// ════════════════════════════════════════════════════════════

app.get('/api/dependencies/check', async (req, res) => {
  const dependencies = {
    openclaw: {
      name: 'OpenClaw',
      description: 'AI Agent Platform — Required for agent orchestration',
      required: true,
      status: 'checking',
      url: OPENCLAW_URL,
    },
    n8n: {
      name: 'N8N',
      description: 'Workflow Automation — Required for automation skills',
      required: false,
      required_for: ['automation'],
      status: 'checking',
      url: N8N_URL,
    },
    postiz: {
      name: 'Postiz',
      description: 'Social Media Management — Required for social media skills',
      required: false,
      required_for: ['social_media'],
      status: 'checking',
      url: process.env.POSTIZ_URL || 'http://localhost:4200',
      install_url: 'https://postiz.com',
      docker_image: 'ghcr.io/gitroomhq/postiz-app',
    },
    litellm: {
      name: 'LiteLLM',
      description: 'LLM Proxy — Required for model routing',
      required: true,
      status: 'checking',
      url: LITELLM_URL,
    },
    ollama: {
      name: 'Ollama',
      description: 'Local LLM — Required for free background jobs',
      required: true,
      status: 'checking',
      url: process.env.OLLAMA_URL || 'http://localhost:11434',
    },
    hubspot: {
      name: 'HubSpot CRM',
      description: 'CRM Integration — Required for CRM skills',
      required: false,
      required_for: ['crm', 'sales'],
      type: 'api',
      status: process.env.HUBSPOT_API_KEY ? 'configured' : 'not_configured',
    },
  };

  // Check each HTTP service
  const checks = Object.entries(dependencies).map(async ([key, dep]) => {
    if (dep.type === 'api') return; // API keys checked via env
    const endpoints = ['/api/health', '/health', '/healthz', '/api/tags', '/'];
    for (const ep of endpoints) {
      try {
        const r = await httpRequest(`${dep.url}${ep}`);
        if (r.status < 500) {
          dependencies[key].status = 'running';
          return;
        }
      } catch { continue; }
    }
    dependencies[key].status = 'not_installed';
  });

  await Promise.all(checks);

  // Build warnings
  const warnings = [];
  for (const [key, dep] of Object.entries(dependencies)) {
    if (dep.status === 'not_installed' || dep.status === 'not_configured') {
      warnings.push({
        service: dep.name,
        key,
        message: dep.required
          ? `${dep.name} is REQUIRED but not running on this server!`
          : `${dep.name} is not installed. Skills ${(dep.required_for || []).join(', ')} will be disabled.`,
        required: dep.required,
        install_url: dep.install_url,
        docker_image: dep.docker_image,
      });
    }
  }

  res.json({ dependencies, warnings, all_ok: warnings.filter(w => w.required).length === 0 });
});

// ════════════════════════════════════════════════════════════
// OMI WEARABLE — Webhook Endpoints
// Receives data from OMI device: memories, transcripts, audio
// ════════════════════════════════════════════════════════════

// Accept raw body for audio bytes
app.use('/omi/audio', express.raw({ type: 'application/octet-stream', limit: '10mb' }));

// OMI: Memory Created (conversation finished)
app.post('/omi/memory', async (req, res) => {
  const uid = req.query.uid || 'default';
  const data = req.body;
  console.log(`[OMI] Memory received: ${data?.structured?.title || 'untitled'}`);

  try {
    const structured = data.structured || {};
    const segments = data.transcript_segments || [];
    const transcript = segments.map(s => {
      const label = s.is_user ? 'DOM' : `Speaker_${s.speaker_id || 0}`;
      return `[${label}] ${s.text || ''}`;
    }).join('\n');

    // Store memory
    await pool.query(
      `INSERT INTO omi_memories (omi_memory_id, uid, title, overview, category, transcript, raw_data, importance, created_at)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
       ON CONFLICT (omi_memory_id) DO UPDATE SET overview = $4, processed_at = NOW()`,
      [
        data.id || `omi_${Date.now()}`, uid,
        structured.title || 'Untitled', structured.overview || '',
        structured.category || 'other', transcript,
        JSON.stringify(data),
        Math.min(10, 5 + (structured.action_items?.length || 0)),
        data.created_at || new Date().toISOString(),
      ]
    );

    // Create tasks from action items
    for (const item of (structured.action_items || [])) {
      const desc = typeof item === 'string' ? item : (item.description || '');
      if (desc) {
        await pool.query(
          `INSERT INTO tasks (title, description, agent_slug, priority, status, channel)
           VALUES ($1, $2, 'jarvis', 3, 'pending', 'omi')`,
          [desc.substring(0, 200), `Auto-created from OMI. UID: ${uid}`]
        ).catch(() => {});
      }
    }

    // Extract and store entities
    const entities = [];
    const emailRegex = /[\w.+-]+@[\w-]+\.[\w.]+/g;
    const phoneRegex = /(?:\+\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}/g;

    const fullText = `${structured.overview || ''} ${transcript}`;
    (fullText.match(emailRegex) || []).forEach(e => entities.push({ type: 'contact_info', name: e, context: 'email' }));
    (fullText.match(phoneRegex) || []).filter(p => p.replace(/\D/g, '').length >= 8)
      .forEach(p => entities.push({ type: 'contact_info', name: p.trim(), context: 'phone' }));

    for (const seg of segments) {
      if (seg.speaker_name && !seg.speaker_name.startsWith('Speaker')) {
        entities.push({ type: 'person', name: seg.speaker_name, context: 'conversation_participant' });
      }
    }

    for (const ent of entities) {
      await pool.query(
        `INSERT INTO omi_entities (uid, entity_type, name, context, mention_count, created_at)
         VALUES ($1, $2, $3, $4, 1, NOW())
         ON CONFLICT (uid, entity_type, name)
         DO UPDATE SET mention_count = omi_entities.mention_count + 1, last_mentioned = NOW()`,
        [uid, ent.type, ent.name.substring(0, 200), ent.context]
      ).catch(() => {});
    }

    // Store events (birthdays, meetings)
    for (const event of (structured.events || [])) {
      const title = typeof event === 'string' ? event : (event.title || '');
      if (title) {
        await pool.query(
          `INSERT INTO omi_events (uid, title, event_date, duration_min, source)
           VALUES ($1, $2, $3, $4, 'omi_memory')`,
          [uid, title, event.start || null, event.duration || 0]
        ).catch(() => {});
      }
    }

    broadcast({ type: 'omi_memory', title: structured.title, category: structured.category });
    res.json({ status: 'ok' });
  } catch (err) {
    console.error('[OMI] Memory processing error:', err.message);
    res.json({ status: 'ok' }); // Always return 200 to OMI
  }
});

// OMI: Real-time transcript segments
app.post('/omi/transcript', async (req, res) => {
  const uid = req.query.uid || 'default';
  const sessionId = req.query.session_id || '';
  const segments = req.body.segments || req.body || [];

  try {
    for (const seg of (Array.isArray(segments) ? segments : [])) {
      const text = (seg.text || '').trim();
      if (!text) continue;

      await pool.query(
        `INSERT INTO omi_transcripts (uid, session_id, speaker, speaker_name, text, is_user, start_time, end_time)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
        [uid, sessionId, seg.speaker || 'unknown', seg.speaker_name || null,
         text, seg.is_user || false, seg.start || null, seg.end || null]
      ).catch(() => {});
    }

    // Check for voice commands in user speech
    const userSegments = (Array.isArray(segments) ? segments : [])
      .filter(s => s.is_user && s.text);
    const triggers = ['jarvis', 'hey jarvis', 'erstell', 'mach', 'erinner'];
    const command = userSegments.find(s =>
      triggers.some(t => s.text.toLowerCase().includes(t))
    );

    if (command) {
      // Return notification message so OMI shows it
      return res.json({ message: `JARVIS hat gehört: "${command.text.substring(0, 100)}"` });
    }
  } catch (err) {
    console.error('[OMI] Transcript error:', err.message);
  }

  res.json({ status: 'ok' });
});

// OMI: Audio bytes (raw PCM16)
app.post('/omi/audio', (req, res) => {
  const uid = req.query.uid || 'default';
  const sampleRate = parseInt(req.query.sample_rate || '16000');
  console.log(`[OMI] Audio: ${req.body?.length || 0} bytes, ${sampleRate}Hz, uid=${uid}`);
  res.json({ status: 'ok' });
});

// OMI: Chat Tool calls (voice commands → JARVIS actions)
app.post('/omi/chat-tool', async (req, res) => {
  const { tool_name, uid } = req.body;
  console.log(`[OMI] Chat tool: ${tool_name}, uid=${uid}`);

  try {
    if (tool_name === 'jarvis_remember') {
      const info = req.body.information || '';
      await pool.query(
        `INSERT INTO omi_memories (uid, memory_type, content, source, importance, title, created_at)
         VALUES ($1, 'explicit', $2, 'voice_command', 8, $3, NOW())`,
        [uid || 'default', info, info.substring(0, 200)]
      );
      await pool.query(
        `INSERT INTO knowledge (subject, predicate, object, category, confidence, source)
         VALUES ($1, 'remembered', $2, 'personal', 0.95, 'omi_voice')
         ON CONFLICT DO NOTHING`,
        [info.substring(0, 200), info]
      ).catch(() => {});
      return res.json({ result: `Gemerkt: ${info.substring(0, 100)}` });
    }

    if (tool_name === 'jarvis_create_task') {
      const title = req.body.title || 'OMI Task';
      const agent = req.body.agent || 'jarvis';
      const priority = req.body.priority || 3;
      await pool.query(
        `INSERT INTO tasks (title, agent_slug, priority, status, channel)
         VALUES ($1, $2, $3, 'pending', 'omi')`,
        [title, agent, priority]
      );
      return res.json({ result: `Task erstellt: ${title}` });
    }

    if (tool_name === 'jarvis_status') {
      const stats = await pool.query(
        `SELECT COUNT(*) as agents FROM agents WHERE status = 'active'`
      );
      const tasks = await pool.query(
        `SELECT COUNT(*) FILTER (WHERE status = 'pending') as pending,
                COUNT(*) FILTER (WHERE status = 'completed') as done
         FROM tasks`
      );
      return res.json({
        result: `JARVIS online. ${stats.rows[0].agents} Agents aktiv. ` +
                `${tasks.rows[0].pending} Tasks offen, ${tasks.rows[0].done} erledigt.`
      });
    }

    if (tool_name === 'jarvis_execute' || tool_name === 'jarvis_agents') {
      const task = req.body.task || req.body.query || '';
      const agent = req.body.agent || 'jarvis';
      // Store as task for processing
      await pool.query(
        `INSERT INTO tasks (title, agent_slug, priority, status, channel, description)
         VALUES ($1, $2, 2, 'pending', 'omi', $3)`,
        [task.substring(0, 200), agent, `Voice command from OMI. UID: ${uid}`]
      );
      broadcast({ type: 'omi_task', agent, task: task.substring(0, 200) });
      return res.json({ result: `${agent.toUpperCase()} arbeitet daran: ${task.substring(0, 100)}` });
    }

    res.json({ result: 'JARVIS hat den Befehl empfangen.' });
  } catch (err) {
    console.error('[OMI] Chat tool error:', err.message);
    res.json({ error: 'Verarbeitung fehlgeschlagen' });
  }
});

// OMI: Setup status check
app.get('/omi/setup-status', (req, res) => {
  res.json({ is_setup_completed: true });
});

// OMI: Tools manifest
app.get('/.well-known/omi-tools.json', (req, res) => {
  res.json({
    tools: [
      {
        name: 'jarvis_execute',
        description: 'Execute any task through JARVIS AI team. Write content, analyze data, manage tasks, or delegate work.',
        endpoint: '/omi/chat-tool',
        parameters: {
          type: 'object',
          properties: {
            task: { type: 'string', description: 'The task to execute' },
            agent: { type: 'string', enum: ['jarvis','elon','steve','donald','archi','donna','iris','satoshi','felix','andreas'], description: 'Agent to handle this' }
          },
          required: ['task']
        },
        auth_required: false,
        status_message: 'JARVIS arbeitet daran...'
      },
      {
        name: 'jarvis_remember',
        description: 'Remember important information permanently. Birthdays, preferences, contacts, ideas, decisions.',
        endpoint: '/omi/chat-tool',
        parameters: {
          type: 'object',
          properties: { information: { type: 'string', description: 'What to remember' } },
          required: ['information']
        },
        auth_required: false,
        status_message: 'Wird gespeichert...'
      },
      {
        name: 'jarvis_agents',
        description: 'Ask a specific JARVIS agent. ELON=analysis, STEVE=marketing, DONALD=sales, ARCHI=tech, DONNA=ops, IRIS=design.',
        endpoint: '/omi/chat-tool',
        parameters: {
          type: 'object',
          properties: {
            query: { type: 'string', description: 'Your question' },
            agent: { type: 'string', enum: ['elon','steve','donald','archi','donna','iris','felix','andreas'] }
          },
          required: ['query', 'agent']
        },
        auth_required: false,
        status_message: 'Agent wird befragt...'
      },
      {
        name: 'jarvis_create_task',
        description: 'Create a task for the JARVIS team. Add to-dos, schedule work, assign agents.',
        endpoint: '/omi/chat-tool',
        parameters: {
          type: 'object',
          properties: {
            title: { type: 'string', description: 'Task title' },
            agent: { type: 'string', description: 'Agent to assign' },
            priority: { type: 'integer', description: '1=highest, 5=lowest' }
          },
          required: ['title']
        },
        auth_required: false,
        status_message: 'Task wird erstellt...'
      },
      {
        name: 'jarvis_status',
        description: 'Get JARVIS system status, active tasks, and team overview.',
        endpoint: '/omi/chat-tool',
        parameters: { type: 'object', properties: {} },
        auth_required: false,
        status_message: 'Status wird abgerufen...'
      }
    ]
  });
});

// OMI Dashboard API — Recent OMI activity
app.get('/api/omi/memories', async (req, res) => {
  try {
    const { uid, category, limit = 30 } = req.query;
    let query = 'SELECT * FROM omi_memories';
    const conditions = [];
    const params = [];
    if (uid) { params.push(uid); conditions.push(`uid = $${params.length}`); }
    if (category) { params.push(category); conditions.push(`category = $${params.length}`); }
    if (conditions.length) query += ' WHERE ' + conditions.join(' AND ');
    query += ' ORDER BY created_at DESC';
    params.push(parseInt(limit));
    query += ` LIMIT $${params.length}`;
    const result = await pool.query(query, params);
    res.json(result.rows);
  } catch { res.json([]); }
});

app.get('/api/omi/entities', async (req, res) => {
  try {
    const { type, limit = 50 } = req.query;
    let query = 'SELECT * FROM omi_entities';
    const params = [];
    if (type) { params.push(type); query += ' WHERE entity_type = $1'; }
    query += ' ORDER BY mention_count DESC, last_mentioned DESC';
    params.push(parseInt(limit));
    query += ` LIMIT $${params.length}`;
    const result = await pool.query(query, params);
    res.json(result.rows);
  } catch { res.json([]); }
});

app.get('/api/omi/stats', async (req, res) => {
  try {
    const [memories, entities, events, transcripts] = await Promise.all([
      pool.query('SELECT COUNT(*) as total, AVG(importance) as avg_importance FROM omi_memories'),
      pool.query('SELECT COUNT(*) as total, SUM(mention_count) as total_mentions FROM omi_entities'),
      pool.query('SELECT COUNT(*) as total FROM omi_events'),
      pool.query('SELECT COUNT(*) as total, COUNT(DISTINCT session_id) as sessions FROM omi_transcripts'),
    ]);
    res.json({
      memories: memories.rows[0],
      entities: entities.rows[0],
      events: events.rows[0],
      transcripts: transcripts.rows[0],
    });
  } catch {
    res.json({ memories: { total: 0 }, entities: { total: 0 }, events: { total: 0 }, transcripts: { total: 0 } });
  }
});

// ── SPA fallback ────────────────────────────────────────────
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// ── START ───────────────────────────────────────────────────
server.listen(PORT, '0.0.0.0', () => {
  console.log(`
  ═══════════════════════════════════════════════════
   JARVIS 1.5 — Mission Control Dashboard
   SYSTEMS™ · architectofscale.com
  ═══════════════════════════════════════════════════
   Port:      ${PORT}
   Mode:      ${process.env.NODE_ENV || 'development'}
   DB:        ${DATABASE_URL ? 'configured' : 'not set'}
   OpenClaw:  ${OPENCLAW_URL}
   N8N:       ${N8N_URL}
   LiteLLM:   ${LITELLM_URL}
  ═══════════════════════════════════════════════════
  `);
});

module.exports = { app, server };
