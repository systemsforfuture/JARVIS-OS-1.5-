# JARVIS 1.5 — API Reference

Base URL: `http://localhost:3000/api`

## Authentication

```
POST /api/auth/login
Content-Type: application/json

{"password": "your-dashboard-secret"}
```

Response: `{"token": "jwt-token", "expiresIn": "24h"}`

Alle authentifizierten Endpoints benoetigen den Header:
```
Authorization: Bearer <token>
```

## Endpoints

### Health

```
GET /api/health
```

Response:
```json
{
  "status": "healthy",
  "checks": {
    "server": "ok",
    "database": "ok",
    "redis": "ok"
  },
  "version": "1.5.0"
}
```

### Agents

```
GET /api/agents              — Alle Agents
GET /api/agents/:slug        — Einzelner Agent
```

### Tasks

```
GET  /api/tasks              — Alle Tasks (query: ?status=pending&agent=jarvis&limit=50)
POST /api/tasks              — Task erstellen (auth required)
```

Body fur POST:
```json
{
  "title": "Wochenbericht erstellen",
  "description": "KPI-Analyse fur KW 10",
  "agent_slug": "elon",
  "priority": 1
}
```

### Skills

```
GET   /api/skills            — Alle Skills (query: ?category=marketing)
PATCH /api/skills/:slug/toggle — Skill aktivieren/deaktivieren (auth required)
```

### Memory

```
GET  /api/memory             — Memory-Eintraege (query: ?agent=jarvis&type=fact&limit=100)
POST /api/memory             — Memory-Eintrag erstellen (auth required)
```

Body fur POST:
```json
{
  "agent_slug": "jarvis",
  "type": "fact",
  "key": "company-name",
  "value": "SYSTEMS™",
  "metadata": {}
}
```

### API Keys

```
GET /api/keys                — Status aller API Keys
```

### Learning

```
GET /api/learning            — Self-Learning Patterns
```

### Stats

```
GET /api/stats               — System-Statistiken
```

### Audit Log

```
GET /api/audit               — Audit-Log (auth required, query: ?limit=100)
```

## WebSocket

```
ws://localhost:3000/ws
```

Events:
- `connected` — Verbindung hergestellt
- `chat` — Chat-Nachricht
- `task_created` — Neuer Task erstellt
