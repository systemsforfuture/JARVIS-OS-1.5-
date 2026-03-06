---
summary: "ARCHI Langzeit-Gedächtnis — Deliveries, Stack, Issues, Architektur"
read_when:
  - Every session start
  - Before architecture decisions
  - Before new features
last_updated: "2026-02-26"
---

# MEMORY.md — Was ich weiß

## 🏗️ DELIVERY HISTORY

### Mission Control V2.1 — Agent Monitoring Dashboard (26.02.2026)
- **Status:** ✅ DEPLOYED & LIVE
- **Was:** Real-Time Agent Monitoring mit Mindmap, Stats, Auto-Refresh
- **Component:** `AgentMonitoringPage.tsx` (485 Zeilen, 16.6 KB)
- **API:** `GET /api/agents/live-status` (< 500ms)
- **Features:** 4-Card Stats, SVG Mindmap, Agent Status List, Filter, Auto-Refresh 5s
- **Tech:** React/TypeScript, Tailwind, Dark Mode, Mobile Responsive
- **Files:** `/data/mission-control/repo/src/pages/AgentMonitoringPage.tsx`

### Sales Dashboard Fix + Leads Filter (26.02.2026)
- **Status:** ✅ COMPLETED
- **Problem:** DEALIO kaputte Directory-Struktur, kein Firmen-Filter
- **Fix:** Directory repariert, Real-time Dropdown-Filter, API-Filterung
- **API:** `GET /api/leads?company=[FIRMA]&stage=[STAGE]`
- **Test-Daten:** 4 Sample-Leads erstellt (DEALIO, DEVCODE, WRANA-CAPITAL)

### Brain System (25.02.2026) — by ELON
- **Status:** ✅ LIVE
- **Was:** Vector Memory Service für alle Agents
- **Port:** 7700 (FastAPI + Qdrant)
- **Mein Beitrag:** Infrastruktur-Support, Container-Management

### A2A Communication System — Design (24.02.2026)
- **Status:** 📋 DESIGN COMPLETE, Implementation ausstehend
- **Was:** File-Based Message Bus für Agent-to-Agent Kommunikation
- **Struktur:** `/data/agents/_COMMS/` (direct/, channels/, _registry.json)
- **CLI:** `a2a send/reply/inbox/channel/status`
- **Effort:** ~12h über 3 Tage
- **Key Decision:** File-based statt DB (Zero Infrastructure, sofort einsetzbar)

---

## 🛠️ TECH STACK

### Mission Control Dashboard
- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS
- **Backend:** Node.js (server.js) auf Port 3001
- **Production:** http://187.77.75.92:8888/
- **Repo:** `/data/mission-control/repo/`
- **Build:** `npm run build` → `dist/`
- **Vite:** 2290 Module, Build ~12-16s

### Infrastruktur
- **VPS:** Hostinger
- **Container Runtime:** Docker
- **OpenClaw:** Agent-Plattform (Container: openclaw-3h0q-openclaw-1)
- **Gateway:** OpenClaw Gateway API (localhost:5555)
- **N8N:** Automation (n8n-main:5678)
- **Postiz:** Social Media (postiz-main, 1.4GB RAM ⚠️)
- **Brain:** FastAPI + Qdrant (Port 7700, 172.17.0.5:6333)
- **Elasticsearch:** Postiz-Search (309MB RAM — evtl. abschalten)

### Datenbank / Storage
- **Supabase:** CRM, Rechnungen, Tasks, Journal
- **Qdrant:** Vector DB für Brain System
- **Filesystem:** Agent-Dateien, Configs, Queues

### Git / GitHub
- Mission Control Repo
- Firmen-Projekte (13 Firmen, diverse Repos)

---

## ⚠️ BEKANNTE ISSUES (von ELON's OPTIMIZATION-LIST)

| ID | Problem | Impact | Mein Beitrag |
|---|---|---|---|
| OPT-001 | 🔴 API-Keys im Plaintext | Security-Risiko | Vault-Migration implementieren |
| OPT-003 | 🟠 Postiz Memory 69.7% | OOM-Kill Risiko | Memory-Limit oder Leak fixen |
| OPT-004 | 🟠 Swap 60% | Performance | Container-Limits optimieren |
| OPT-007 | 🟠 N8N Workflow-Inventar inkonsistent | Zombie-Workflows | Audit + Cleanup |
| OPT-008 | 🟠 Elasticsearch unnötig? | 300MB RAM verschwendet | Usage prüfen, ggf. deaktivieren |
| OPT-009 | 🟡 Disk 72% | 4-6 Wochen bis kritisch | Cleanup-Script |
| OPT-012 | 🟡 DEV Queue 155 Lines | Bottleneck | Queue Review + Tasks zusammenfassen |

---

## 📐 ARCHITEKTUR-ENTSCHEIDUNGEN (ADR Log)

| Datum | Entscheidung | Begründung |
|-------|-------------|------------|
| 2026-02-26 | Agent Monitoring als React Component, nicht separates Tool | Einheitliches Dashboard, kein zusätzlicher Service |
| 2026-02-26 | Polling (5s) statt WebSocket für Agent Status | Simpler, Phase 2 kann WS nachrüsten |
| 2026-02-24 | A2A File-Based statt DB | Zero Infrastructure, alle Agents haben Filesystem-Access |
| 2026-02-24 | Bash CLI für A2A statt HTTP API | Agents nutzen `exec` nativ, kein Server nötig |

---

## 🏛️ FIRMEN-TECHNISCHER STATUS

| Firma | Website | Tech | Status |
|-------|---------|------|--------|
| SYSTEMS™ | ❌ | Needs Build | Priorität |
| DWMUC | ❌ | Needs Build | Cedrik-Projekt |
| Deal.io | ✅ getmydeal.de | Live | 39 User |
| Systemfrei Exit | ✅ | Live | 2.000+ User |
| WAC | ❌ | Dashboard Konzept | Tier 3 |
| DEVCode | ❌ | Template only | Evtl. in SYSTEMS™ |
| SNIP bis ÉlanSÉVEN | ❌ | Needs Setup | Pending |

---

## 🤖 TEAM

```
DOM → JARVIS → ARCHI (ich)
                  ├── TECH-EXECUTOR ⚙️
                  ├── MONITOR 📡
                  ├── TESTER 🧪
                  └── QUALITY-GUARDIAN 🛡️
```

Parallel: ELON (Analyst), STEVE (Marketing), DONALD (Sales), DONNA (Backoffice), IRIS (Design), SATOSHI (Crypto), FELIX/ANDREAS (Customer)

---

## 📝 DOM-ENTSCHEIDUNGEN (Log)

| Datum | Entscheidung |
|-------|-------------|
| 2026-02-26 | ARCHITECT → ARCHI umbenannt (Dashboard wird angepasst) |
| 2026-02-26 | Extra Dashboard-Agents (ORACLE, GHOST etc.) → später klären |

---

## 🔄 UPDATE-PROTOKOLL

[2026-02-26] [DELIVERY] Mission Control V2.1 — Agent Monitoring Dashboard deployed
[2026-02-26] [DELIVERY] Sales Dashboard Fix + Leads Filter completed
[2026-02-26] [SETUP] ARCHI-Dateien komplett neu gebaut (modulare Architektur)
[2026-02-25] [INFRA] Brain System deployed (ELON, Infra-Support ARCHI)
[2026-02-24] [DESIGN] A2A Communication System designed (Implementation pending)
[2026-02-24] [SCAN] ELON System-Scan: 13 Issues, mehrere DEV-relevant

_MEMORY.md wird nach jeder Delivery und wichtigen Session aktualisiert._
