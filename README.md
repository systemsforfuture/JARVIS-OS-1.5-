<div align="center">

# JARVIS 1.5
### Autonomes KI-Betriebssystem by SYSTEMS™

[![Version](https://img.shields.io/badge/version-1.5-white?style=flat-square)](https://github.com/systems-tm/jarvis-15/releases)
[![Status](https://img.shields.io/badge/status-production-brightgreen?style=flat-square)](.)
[![License](https://img.shields.io/badge/license-proprietary-red?style=flat-square)](.)
[![SYSTEMS™](https://img.shields.io/badge/by-SYSTEMS™-black?style=flat-square)](https://architectofscale.com)

**Ein Command. 20 Minuten. JARVIS lauft.**

</div>

---

## Quick Install

```bash
curl -fsSL https://raw.githubusercontent.com/systems-tm/jarvis-15/main/installer/install.sh | sudo bash
```

## Was ist JARVIS?

JARVIS 1.5 ist ein autonomes KI-Betriebssystem fur Unternehmen. Ein Team aus 10 spezialisierten AI-Agents erledigt Marketing, Sales, Development, Operations, Analytics und mehr — vollautomatisch.

**Fur wen?** Unternehmer und Unternehmen die ihr gesamtes operatives Business mit KI automatisieren wollen.

## Agent Team

```
  JARVIS   Chief Intelligence Operator
  |-- ELON     Analyst & Systemoptimierer
  |-- STEVE    Marketing & Content
  |-- DONALD   Sales & Revenue
  |-- ARCHI    Dev & Infrastructure
  |-- DONNA    Backoffice & Operations
  |-- IRIS     Design & Creative
  |-- SATOSHI  Crypto & Trading
  |-- FELIX    Customer Success
  +-- ANDREAS  Customer Success SFE
```

## Was wird installiert?

| Komponente | Beschreibung |
|-----------|-------------|
| 10 AI Agents | Spezialisierte Agents mit eigener Identitat und Skills |
| 60+ Skills | Marketing, Sales, Dev, Ops, Analytics, Crypto |
| Smart Routing | Automatische Modell-Auswahl (Opus/Sonnet/Haiku) |
| Self-Learning | Agents lernen aus jedem Task und werden besser |
| Dashboard | Dark Mode Mission Control mit Live-Chat |
| PostgreSQL | 8-Tabellen Schema mit Memory, Tasks, Learning |
| Redis | Caching und Real-time Events |
| LiteLLM | Model Router mit Budget-Management |
| N8N | Workflow Automation Engine |
| Nginx | Reverse Proxy mit SSL |

## Tech Stack

- **AI**: Claude Opus / Sonnet / Haiku via LiteLLM
- **Backend**: Node.js + Express + WebSocket
- **Database**: PostgreSQL 16 + Redis 7
- **Orchestration**: Docker Compose
- **Workflows**: N8N
- **Proxy**: Nginx
- **CI/CD**: GitHub Actions

## Repository Struktur

```
jarvis-15/
|-- installer/          # One-Command Installer + Scripts
|-- agents/             # 10 Agent Identity Files
|-- config/             # LiteLLM, OpenClaw, Nginx, DB
|-- dashboard/          # Mission Control (Node.js)
|-- skills/             # 7 Skill-Kategorien (60+ Skills)
|-- docs/               # Architektur, API, Onboarding
|-- tests/              # Installer, Agent, Dashboard Tests
|-- .github/            # Actions, Issue Templates
+-- docker-compose.yml  # 6 Services
```

## Nach der Installation

1. API Keys eintragen: `nano /opt/jarvis/.env`
2. Services starten: `cd /opt/jarvis && docker compose up -d`
3. Dashboard offnen: `http://DEINE-IP:80`
4. Agents konfigurieren und Aufgaben erstellen

## Wartung

```bash
# Health Check
bash /opt/jarvis/scripts/health-check.sh

# Update
bash /opt/jarvis/scripts/update.sh

# Backup
bash /opt/jarvis/scripts/backup.sh
```

## Pakete

| | JARVIS 1.5 | Custom AI | Enterprise |
|--|-----------|-----------|------------|
| Setup | EUR 20.000 | ab EUR 50.000 | EUR 97.000 |
| Monatlich | EUR 4K-8K | EUR 5K-15K | EUR 5K-8K |

---

<div align="center">

**SYSTEMS™** · [architectofscale.com](https://architectofscale.com)

JARVIS 1.5 ist production-ready.

</div>
