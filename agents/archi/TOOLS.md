---
summary: "ARCHI Tools — Tech Stack, Endpoints, Docker, Scripts, Git"
read_when:
  - When coding or deploying
  - When debugging infrastructure
  - When checking system status
---

# TOOLS.md — Mein Werkzeugkasten

## 1. MISSION CONTROL DASHBOARD

### Frontend
- **Production:** http://187.77.75.92:8888/
- **Dev Server:** http://localhost:8888 (Vite Proxy)
- **Repo:** `/data/mission-control/repo/`
- **Stack:** React 18 + TypeScript + Vite + Tailwind CSS
- **Build:** `cd /data/mission-control/repo && npm run build`
- **Output:** `dist/` (static files)

### Backend
- **Server:** `/data/mission-control/repo/server.js` (Node.js, Port 3001)
- **API:** `/data/mission-control/api/server.js`

### API Endpoints

| Endpoint | Method | Beschreibung |
|---|---|---|
| `/api/agents/live-status` | GET | Agent Monitoring (Status, Sessions, Tasks) |
| `/api/leads` | GET | Leads (Filter: `?company=X&stage=Y`) |
| `/api/brain/health` | GET | Brain Service Health |
| `/api/brain/stats` | GET | Brain Statistics |
| `/api/brain/collections` | GET | Brain Collections |
| `/api/brain/agents` | GET | Brain Agent Overview |
| `/api/brain/recent` | GET | Recent Memories (`?collection=X&limit=Y`) |
| `/api/brain/search` | POST | Semantic Search |
| `/api/brain/store` | POST | Store Memory |
| `/api/system/ping` | GET | Service Health (`?port=X`) |

### Pages/Routes

| Route | Component | Was |
|---|---|---|
| `/` | Home | Dashboard Übersicht |
| `/tasks` | Tasks | Task-Board |
| `/leads` | Leads | Lead-Pipeline |
| `/sales` | SalesPage | Sales + Firmen-Filter |
| `/design` | Design | Design-Queue |
| `/companies` | Companies | Firmen-Übersicht |
| `/backoffice` | Backoffice | Admin |
| `/agents` | Agents | Agent-Konfiguration |
| `/agent-monitoring` | AgentMonitoringPage | Live Agent Monitor |
| `/bots` | Bots | Bot-Config |
| `/n8n` | N8N | Workflow-Status |
| `/brain.html` | Brain Panel | Vector Memory |
| `/config.html` | Config Panel | System Config |

## 2. DOCKER / CONTAINER

### Container-Übersicht
```bash
# Alle Container
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Stats (CPU, Memory, Net)
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Logs
docker logs [CONTAINER] --tail=50
docker logs [CONTAINER] --tail=50 2>&1 | grep -i error
```

### Wichtige Container

| Container | Service | Port | RAM |
|---|---|---|---|
| openclaw-3h0q-openclaw-1 | OpenClaw | — | — |
| n8n-main | N8N Automation | 5678 | — |
| postiz-main | Social Media | — | 1.4GB ⚠️ |
| postiz-elasticsearch | Search (unnötig?) | — | 309MB |
| systems-brain | Vector Memory | 7700 | — |
| qdrant | Vector DB | 6333 | — |

### Docker Commands
```bash
# Container restart (Zero Downtime wo möglich)
docker restart [CONTAINER]

# Rebuild + Restart
docker-compose up -d --build [SERVICE]

# Container Logs live
docker logs -f [CONTAINER]

# Container Shell
docker exec -it [CONTAINER] /bin/bash
```

## 3. BRAIN SYSTEM

### Service
- **API:** http://localhost:7700
- **Qdrant:** 172.17.0.5:6333
- **Embeddings:** BAAI/bge-small-en-v1.5 (384 dim)

### Scripts
```bash
bash /data/agents/scripts/brain-store.sh ARCHI [collection] [title] [content] [tags]
bash /data/agents/scripts/brain-search.sh [query] [collection] ARCHI [limit]
bash /data/agents/scripts/brain-broadcast.sh ARCHI [title] [content] [tags]
bash /data/agents/scripts/brain-stats.sh
```

## 4. PIPELINE-MANAGEMENT

```bash
# Task starten
bash /data/agents/scripts/pipeline-manager.sh start DEV [TASK_ID]

# Task in Review
bash /data/agents/scripts/pipeline-manager.sh review DEV [TASK_ID] "[Ergebnis]"

# Queue lesen
cat /data/agents/DEV/ARCHITECT/tasks/QUEUE.md
```

## 5. TELEGRAM

```bash
# DEV-Gruppe (-5254235209)
bash /data/agents/scripts/tg-send.sh dev "NACHRICHT"

# Architect direkt
bash /data/agents/scripts/tg-send.sh architect "NACHRICHT"
```

## 6. GIT / GITHUB

```bash
# Standard Git Workflow
git status
git add -A
git commit -m "fix: [beschreibung]"
git push origin main

# Branching (für größere Features)
git checkout -b feature/[name]
# ... develop ...
git checkout main
git merge feature/[name]
git push
```

### Commit Message Convention
```
feat: Neues Feature
fix: Bug Fix
refactor: Code Refactoring
docs: Dokumentation
chore: Maintenance
hotfix: Production Hotfix
```

## 7. N8N

- **URL:** http://n8n-main:5678
- **Workflows:** 44 Exports (OPT-007: Inventar inkonsistent!)
- **Trigger:** Webhook, Cron, Manual

## 8. SYSTEM-DIAGNOSTIK

### Quick Health Check
```bash
# All-in-One
bash /data/agents/scripts/system-status.sh

# CPU Load
cat /proc/loadavg

# Memory + Swap
free -h

# Disk
df -h /
du -sh /data/* | sort -rh | head -10

# Network (Port Check)
curl -s http://localhost:7700/health  # Brain
curl -s http://localhost:3001/api/agents/live-status | head -1  # Mission Control
curl -s http://localhost:5555/api/sessions/list | head -1  # OpenClaw Gateway
```

## 9. A2A COMMUNICATION (Implementation Pending)

### Designed, noch nicht implementiert
```
/data/agents/_COMMS/
├── direct/           # 1:1 Messages
├── channels/         # Team Channels
└── _registry.json    # Agent Directory

CLI: /data/agents/_COMMS/_bin/a2a
Commands: send, reply, inbox, channel, status
```

**Effort:** ~12h über 3 Tage. Zero Infrastructure, file-based.

## 10. FILE-SYSTEM

### Wichtige Pfade
```
/data/mission-control/repo/          — Dashboard Codebase
/data/mission-control/repo/src/      — React Source
/data/mission-control/repo/server.js — Backend
/data/mission-control/api/           — API Server
/data/.openclaw/                     — OpenClaw Config
/data/.openclaw/openclaw.json        — Agent Config
/data/.openclaw/workspace-architect/ — Mein Workspace
/data/agents/DEV/ARCHITECT/          — Mein Agent-Verzeichnis
/data/agents/DEV/ARCHITECT/tasks/    — Meine Queue
/data/agents/scripts/                — Shared Scripts
/data/agents/BRAIN/                  — Brain System
/data/unternehmen/                   — Firmen-Dateien
/data/unternehmen/[FIRMA]/_SALES/    — Sales Pipeline Data
```

## 11. WHISPER + API

- **Whisper (Sprache→Text):** 172.18.0.1:9000
- **Anthropic API:** Haiku (Standard), Sonnet (Komplex), Opus (Kritisch)
- **OpenClaw Gateway:** localhost:5555
