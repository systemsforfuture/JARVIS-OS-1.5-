---
summary: "ELON Tools & Endpoints — Brain System, Scripts, Infrastruktur"
read_when:
  - When running system scans
  - When using Brain scripts
  - When checking infrastructure
---

# TOOLS.md — Meine Werkzeuge

## 1. MISSION CONTROL DASHBOARD

**URL:** http://187.77.75.92:8888/

| Panel | URL | Was |
|-------|-----|-----|
| Home | /home | Übersicht |
| Tasks | /tasks | Task-Board, Pipeline |
| Leads | /leads | Lead-Tracking |
| Sales | /sales | Revenue, Deals |
| Design | /design | Design-Queue |
| Firmen | /companies | Firmen-Übersicht |
| Backoffice | /backoffice | Admin |
| Agents | /agents | Agent-Status |
| Monitor | /monitor | System-Health |
| Bots | /bots | Bot-Konfiguration |
| N8N | /n8n | Workflow-Status |
| Brain | /brain.html | Vector Memory Dashboard |
| Config | /config.html | System Config & Health |

## 2. BRAIN SYSTEM

### Service
- **Brain API:** http://localhost:7700
- **Qdrant:** 172.17.0.5:6333
- **Modell:** BAAI/bge-small-en-v1.5 (384 dim)
- **Container:** systems-brain

### Collections
```
agent_memory    — Agent-spezifische Erinnerungen
tasks           — Task-Logs und Ergebnisse
decisions       — Entscheidungs-Log
knowledge       — Geteiltes Wissen
conversations   — Gesprächs-Kontext
```

### Scripts
```bash
# Memory speichern
bash /data/agents/scripts/brain-store.sh [agent] [collection] [title] [content] [tags]

# Semantisch suchen
bash /data/agents/scripts/brain-search.sh [query] [collection] [agent] [limit]

# System-weit broadcasten
bash /data/agents/scripts/brain-broadcast.sh [agent] [title] [content] [tags]

# Stats abrufen
bash /data/agents/scripts/brain-stats.sh
```

### API Endpoints
```
GET  /api/brain/health
GET  /api/brain/stats
GET  /api/brain/collections
GET  /api/brain/agents
GET  /api/brain/recent?collection=...&limit=...
POST /api/brain/search     {query, collection, agent, limit}
POST /api/brain/store      {agent, collection, title, content, tags}
GET  /api/system/ping?port=...
```

## 3. SYSTEM-ANALYSE COMMANDS

### Server-Health
```bash
# CPU & Memory
free -h
top -bn1 | head -20
cat /proc/loadavg

# Swap
swapon --show
free -h | grep Swap

# Disk
df -h /
du -sh /data/* | sort -rh | head -20

# Container
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### Container-Spezifisch
```bash
# Postiz (Memory-Problem bekannt)
docker stats postiz-main --no-stream

# N8N
docker logs n8n-main --tail 50

# Brain
curl -s http://localhost:7700/health
curl -s http://localhost:7700/stats
```

### Log-Analyse
```bash
# Agent-Logs
ls -la /data/agents/logs/
cat /data/agents/logs/ELON.log

# N8N Workflows
cat /data/agents/workflows-summary.json
ls /data/agents/WORKFLOWS/
```

## 4. PIPELINE-MANAGEMENT

```bash
# Task starten
bash /data/agents/scripts/pipeline-manager.sh start [TEAM] [TASK_ID]

# Task reviewen
bash /data/agents/scripts/pipeline-manager.sh review [TEAM] [TASK_ID] "[Ergebnis]"

# Queue checken
cat /data/agents/JARVIS/tasks/QUEUE.md
cat /data/agents/DEV/ARCHITECT/QUEUE.md
```

## 5. FILE-SYSTEM

### Wichtige Pfade
```
/data/.openclaw/workspace/         — Shared Workspace
/data/.openclaw/agents/elon/       — Mein Agent-Verzeichnis
/data/agents/                      — Alle Agents
/data/agents/scripts/              — Shared Scripts
/data/agents/BRAIN/                — Brain System
/data/agents/_DAILY-REPORTS/       — Team-Reports (aktuell leer!)
/data/unternehmen/                 — Firmen-Dateien
```

### Meine Dateien
```
IDENTITY.md          — Wer ich bin
SOUL.md              — Was mich antreibt
USER.md              — Wer Dom ist
MEMORY.md            — Langzeit-Gedächtnis
HEARTBEAT.md         — Tägliche Checks
TOOLS.md             — Diese Datei
AGENTS.md            — Team-Übersicht
OPTIMIZATION-LIST.md — System-Issues
memory/YYYY-MM-DD.md — Tages-Logs
```

## 6. N8N

- **URL:** http://n8n-main:5678
- **Workflows:** 44 Exports, 7 im WORKFLOWS-Verzeichnis, 2 in Summary (OPT-007: Inkonsistenz!)
- **Daily Summary:** N8N triggert 18:00 → JARVIS schreibt Executive Summary

## 7. EXTERNE TOOLS

- **Whisper (Sprache→Text):** 172.18.0.1:9000
- **Anthropic API:** Haiku 4.5 (Standard), Sonnet 4.5 (Heavy), Opus 4.5 (Kritisch)
