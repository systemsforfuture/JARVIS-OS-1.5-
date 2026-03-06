# JARVIS 1.5 — Quick Start Guide

## Voraussetzungen

- VPS mit Ubuntu 22.04+ oder Debian 12+
- Minimum 4GB RAM, 2 vCPU, 40GB Disk
- Root-Zugang (SSH)
- Anthropic API Key (https://console.anthropic.com)

## Installation

### 1. One-Command Install

```bash
curl -fsSL https://raw.githubusercontent.com/systems-tm/jarvis-15/main/installer/install.sh | sudo bash
```

Die Installation dauert ca. 15-20 Minuten und installiert automatisch:
- Docker + Docker Compose
- PostgreSQL 16
- Redis 7
- LiteLLM (Model Router)
- N8N (Workflow Engine)
- Mission Control Dashboard
- Nginx (Reverse Proxy)

### 2. API Keys eintragen

Nach der Installation, bearbeite die `.env` Datei:

```bash
nano /opt/jarvis/.env
```

**Pflicht:**
- `ANTHROPIC_API_KEY` — dein Claude API Key

**Optional (aber empfohlen):**
- `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` — fur Benachrichtigungen
- `OPENAI_API_KEY` — als Fallback-Modell

### 3. Starten

```bash
cd /opt/jarvis
docker compose up -d
```

### 4. Dashboard offnen

Offne im Browser: `http://DEINE-SERVER-IP:80`

Passwort: steht in deiner `.env` unter `DASHBOARD_SECRET`

## Erste Schritte im Dashboard

1. **Login** — mit dem Dashboard-Passwort
2. **Agents prufen** — alle 10 Agents sollten als "active" angezeigt werden
3. **Chat** — schreibe JARVIS eine Nachricht
4. **Skills** — prufe welche Skills aktiv sind (abhaengig von API Keys)
5. **Settings** — API Key Status uberprufen

## Taegliche Nutzung

JARVIS arbeitet autonom. Du gibst Aufgaben uber:
- **Dashboard Chat** — direkte Kommunikation
- **Telegram** — wenn Telegram-Bot konfiguriert
- **Tasks** — Aufgaben im Dashboard erstellen

## Wartung

```bash
# Health Check
bash /opt/jarvis/scripts/health-check.sh

# Update
bash /opt/jarvis/scripts/update.sh

# Backup
bash /opt/jarvis/scripts/backup.sh

# Logs ansehen
docker logs jarvis-dashboard --tail 100
docker logs jarvis-litellm --tail 100
```

## Hilfe

- GitHub Issues: https://github.com/systems-tm/jarvis-15/issues
- SYSTEMS™: https://architectofscale.com
