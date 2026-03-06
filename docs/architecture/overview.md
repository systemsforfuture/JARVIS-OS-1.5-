# JARVIS 1.5 — Architektur

## System-Architektur

```
                    +------------------+
                    |     NGINX        |
                    |   (Port 80/443)  |
                    +--------+---------+
                             |
              +--------------+--------------+
              |              |              |
     +--------v---+  +------v-----+  +----v------+
     |  Dashboard  |  |  LiteLLM   |  |    N8N    |
     |  (Port 3000)|  | (Port 4000)|  |(Port 5678)|
     +------+------+  +-----+------+  +-----+-----+
            |                |               |
            +--------+-------+-------+-------+
                     |               |
              +------v------+  +-----v-----+
              | PostgreSQL  |  |   Redis   |
              | (Port 5432) |  |(Port 6379)|
              +-------------+  +-----------+
```

## Komponenten

### Dashboard (Mission Control)
- Node.js + Express Server
- WebSocket fur Live-Updates
- Dark Mode UI
- Agent-Management, Tasks, Skills, Memory, Chat

### LiteLLM (Model Router)
- Smart Model Routing basierend auf Agent-Tier
- Budget-Management
- Caching uber Redis
- Fallback-Ketten: Opus -> Sonnet -> Haiku -> Groq

### PostgreSQL (Datenbank)
- 8 Tabellen: agents, tasks, memory, conversations, skills, learning, api_keys, audit_log
- Vollstandiges Schema mit Indexes

### Redis (Cache)
- Session-Cache
- LiteLLM Response-Cache
- Pub/Sub fur Real-time Events

### N8N (Workflow Engine)
- Automatisierte Workflows
- Cron-Jobs fur Reports
- Webhook-Integration

### Nginx (Reverse Proxy)
- SSL Termination
- WebSocket Proxy
- Rate Limiting
- Security Headers

## Model-Routing

| Tier | Modell | Agents | Use Case |
|------|--------|--------|----------|
| 1 | Claude Opus | JARVIS, ELON | Strategie, komplexe Analyse |
| 2 | Claude Sonnet | STEVE, DONALD, ARCHI, DONNA, IRIS, SATOSHI, FELIX | Ausfuhrung, Content, Code |
| 3 | Claude Haiku | ANDREAS | Schnelle, strukturierte Tasks |
| Fallback | Groq Llama | Alle | Bei API-Limits |

## Datenfluss

1. User -> Dashboard/Chat
2. Dashboard -> JARVIS (via OpenClaw)
3. JARVIS -> LiteLLM (Model-Auswahl)
4. LiteLLM -> Claude API
5. Response -> Memory speichern
6. Response -> User (via WebSocket)
