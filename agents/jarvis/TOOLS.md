---
summary: "JARVIS verfügbare Tools und wann welches nutzen"
read_when:
  - Before using a tool you haven't used recently
  - When a tool fails unexpectedly
  - When choosing between tools for a task
---

# TOOLS.md — Tools & Konfiguration

## Core Tools (immer verfügbar)

### Bash / Shell
- **Wann:** System-Tasks, File-Operationen, Docker-Befehle
- **Container-Kontext:** Homebrew verfügbar unter `/home/linuxbrew/.linuxbrew`
- **Wichtig:** Destructive Commands immer mit Dom bestätigen

### Browser
- **Status:** Aktiv (Chromium headless)
- **Wann:** Web-Scraping, Screenshots, Login-Flows, JS-rendered Sites
- **Profil:** `openclaw` (Standard)

### Memory / File System
- **Workspace:** `~/.openclaw/workspace/`
- **Daily Memory:** `memory/YYYY-MM-DD.md`
- **Langzeit:** `MEMORY.md` (nur Main Session)

---

## MCP Server (falls konfiguriert)

_Stand: Noch keine MCP Server konfiguriert._

Wenn MCP Server gebraucht wird → Dom fragen oder selbst konfigurieren.

---

## Sprachnachrichten (Voice → Text)

**Skill:** `openai-whisper-api` | **Server:** Lokal auf `172.18.0.1:9000` | **Kostenlos, kein API Key**

Wenn eine Sprachnachricht (`.ogg`, `.m4a`, `.mp3`) ankommt:
```bash
~/.openclaw/workspace/skills/openai-whisper-api/scripts/transcribe.sh /path/audio.ogg --language de
```
→ Gibt transkribierten Text direkt aus → wie normale Textnachricht verarbeiten → antworten.

**WICHTIG:** Kein `whisper`-CLI installieren, kein pip install — der lokale Server macht alles.

**Direkt via curl (Alternative):**
```bash
curl -sS http://172.18.0.1:9000/v1/audio/transcriptions \
  -F "file=@/path/audio.ogg" -F "model=whisper-1" -F "language=de" -F "response_format=json" \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['text'])"
```

**Automatisch:** Jede eingehende Voice-Message transkribieren bevor sie verarbeitet wird.

---

## Bildgenerierung (Text → Bild)

**Skill:** `openai-image-gen` | **API:** OpenAI DALL-E 3 | **Key:** OPENAI_API_KEY ✅

Wenn Dom ein Bild will ("generiere", "erstelle ein Bild", "zeichne"):
```bash
OPENAI_API_KEY=$OPENAI_API_KEY python3 ~/.openclaw/workspace/skills/openai-image-gen/scripts/gen.py --prompt "PROMPT" --size 1024x1024 --model dall-e-3
```
Ergebnis-URL zurück an Dom senden.

---

## ClawHub Skills

**Status:** 8 Skills installiert (Stand: 2026-02-21)
**Account:** @DomHub97

| Skill | Version | Zweck | API Key nötig? |
|---|---|---|---|
| `ddg-web-search` | 1.0.0 | Web-Suche via DuckDuckGo | Nein |
| `exa-web-search-free` | 1.0.1 | Web-Suche via Exa (free tier) | Nein |
| `agent-memory` | 1.0.0 | Erweiterte Memory-Tools | Nein |
| `openclaw-mem` | 2.1.0 | OpenClaw Native Memory | Nein |
| `elite-longterm-memory` | 1.2.3 | Vektor-Memory System | ⚠️ OPENAI_API_KEY nötig |
| `agent-browser` | 0.2.0 | Browser-Automation & Scraping | Nein |
| `github` | 1.0.0 | GitHub Integration | GitHub Token (optional) |
| `notion` | 1.0.0 | Notion Integration | Notion Token (optional) |

**Hinweis `elite-longterm-memory`:** Braucht `OPENAI_API_KEY` in `.env` — bis dahin `openclaw-mem` oder `agent-memory` nutzen.

**Neue Skills installieren:**
```bash
docker exec openclaw-3h0q-openclaw-1 clawhub install [SKILL] --workdir /data/.openclaw/workspace --no-input
# Bei suspicious-Flag: --force anhängen (normal für Skills mit externen API-Calls)
```

---

## Anthropic API

**Primary:** `anthropic/claude-sonnet-4-5-20250929`
**Heavy tasks:** `anthropic/claude-opus-4-6`
**Heartbeat/cheap:** `anthropic/claude-haiku-4-5-20251001`

**API Key:** In `.env` als `ANTHROPIC_API_KEY`

### Kosten-Referenz (ca.)
| Modell | Input /1K tokens | Output /1K tokens |
|---|---|---|
| Haiku 4.5 | ~$0.0008 | ~$0.001 |
| Sonnet 4.5 | ~$0.003 | ~$0.015 |
| Opus 4.6 | ~$0.015 | ~$0.075 |

---

## System-Infos

**Mission Control Dashboard:** http://187.77.75.92:8888/
**VPS:** Hostinger
**Container:** `openclaw-3h0q-openclaw-1`
**Docker Compose:** `/docker/openclaw-3h0q/docker-compose.yml`
**Config:** `/docker/openclaw-3h0q/data/.openclaw/openclaw.json`
**Port:** 44459

**Useful Commands (vom Host):**
```bash
# Container Status
docker ps | grep openclaw

# Logs
docker logs openclaw-3h0q-openclaw-1 --tail=50

# In Container
docker exec openclaw-3h0q-openclaw-1 openclaw [COMMAND]

# Restart
cd /docker/openclaw-3h0q && docker compose restart

# Config reload (restart)
cd /docker/openclaw-3h0q && docker compose up -d --force-recreate
```

---

## Kanäle

| Kanal | Bot/Account | Status |
|---|---|---|
| Telegram | @sysjarvbot | Aktiv |
| WhatsApp | +4915569006370 | Aktiv |
| Web-Chat | Port 44459 | Aktiv |

---

---

## N8N Automation (Token-sparend!)

**Stack:** PostgreSQL + Redis Queue + 1 Worker | **Port:** 5678 (intern) / `/n8n/` (nginx)
**Dashboard:** `http://187.77.75.92/n8n/` | User: `dom` | Passwort: in N8N.md

**Wann N8N nutzen (statt Claude):**
- Regelmäßige API-Calls (Monitoring, Email-Check, etc.) → **$0**
- Daten aggregieren, Wenn-Dann-Logik → **$0**
- Externe Services verbinden → **$0**
- Nur für **Analyse/Intelligenz** → Claude aufrufen

**Workflow erstellen via API:**
```bash
# GET all workflows
# Credentials aus Vault laden:
N8N_PASS=$(python3 -c "import json; print(json.load(open('/data/.openclaw/.vault/credentials.json'))['n8n']['password'])")
curl -u "dom:$N8N_PASS" http://127.0.0.1:5678/api/v1/workflows

# Run workflow
curl -u "dom:$N8N_PASS" -X POST http://127.0.0.1:5678/api/v1/workflows/{id}/run
```
→ Details: N8N.md

_Update wenn neue Tools / Skills / MCP Server konfiguriert werden._
