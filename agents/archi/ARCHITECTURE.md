---
summary: "ARCHI System-Architektur — Empire Infrastructure, Service Map, Data Flow, Decisions"
read_when:
  - Before architecture decisions
  - When adding new services
  - When debugging cross-service issues
  - When onboarding to a project
---

# ARCHITECTURE.md — Das technische Empire

## System-Übersicht

```
┌─────────────────────────────────────────────────────────────┐
│                    HOSTINGER VPS                             │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │ Mission  │  │ OpenClaw │  │   N8N    │  │  Postiz   │  │
│  │ Control  │  │ (Agents) │  │ (Auto)   │  │ (Social)  │  │
│  │ :8888    │  │ Gateway  │  │ :5678    │  │           │  │
│  │ React+TS │  │ :5555    │  │          │  │ 1.4GB RAM │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───────────┘  │
│       │              │              │                        │
│  ┌────┴──────────────┴──────────────┴────────────────────┐  │
│  │                    Docker Network                      │  │
│  └───────────────────────┬───────────────────────────────┘  │
│                          │                                   │
│  ┌──────────┐  ┌────────┴───┐  ┌──────────┐  ┌─────────┐  │
│  │  Brain   │  │   JAMES    │  │  Qdrant  │  │ Elastic │  │
│  │ FastAPI  │  │   Bridge   │  │ VectorDB │  │ Search  │  │
│  │ :7700    │  │   :9001    │  │ :6333    │  │ 309MB   │  │
│  └──────────┘  └────────────┘  └──────────┘  └─────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                 Filesystem                            │  │
│  │  /data/agents/     Agent-Dateien, Queues, Scripts    │  │
│  │  /data/unternehmen/ Firmen-Daten, Sales Pipeline     │  │
│  │  /data/mission-control/ Dashboard Codebase           │  │
│  │  /data/.openclaw/   Agent Config + Workspaces        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

          ┌─────────┐         ┌──────────┐
          │ Supabase│         │ External │
          │ (CRM,   │         │  APIs    │
          │  Tasks, │         │ (Stripe, │
          │  Data)  │         │  Gmail,  │
          │ CLOUD   │         │  GCal)   │
          └─────────┘         └──────────┘
```

---

## 1. SERVICE MAP

### Mission Control Dashboard
- **Was:** Zentrales Dashboard für das gesamte Empire
- **Stack:** React 18 + TypeScript + Vite + Tailwind CSS + Node.js Backend
- **Port:** 8888 (Frontend Proxy) / 3001 (Backend API)
- **Repo:** `/data/mission-control/repo/`
- **Owner:** ARCHI
- **Abhängigkeiten:** OpenClaw Gateway (Agent Status), Filesystem (Queues, Leads)
- **Kritikalität:** 🟡 MITTEL — Intern, kein Kunden-Traffic

### OpenClaw Agent Platform
- **Was:** Orchestriert alle AI-Agents (JARVIS, ELON, DONNA, ARCHI, etc.)
- **Container:** openclaw-3h0q-openclaw-1
- **Gateway:** localhost:5555
- **Config:** `/data/.openclaw/openclaw.json`
- **Workspaces:** `/data/.openclaw/workspace-[agent]/`
- **Kritikalität:** 🔴 KRITISCH — Ohne OpenClaw keine Agents

### Brain System (Vector Memory)
- **Was:** Geteiltes Gedächtnis für alle Agents. Semantische Suche.
- **Stack:** FastAPI + BAAI/bge-small-en-v1.5 (384 dim) + Qdrant
- **Port:** 7700 (API) + 6333 (Qdrant)
- **Collections:** agent_memory, tasks, decisions, knowledge, conversations
- **Scripts:** brain-store.sh, brain-search.sh, brain-broadcast.sh, brain-stats.sh
- **Kritikalität:** 🟡 MITTEL — Agents funktionieren auch ohne, aber schlechter

### N8N Automation
- **Was:** Workflow-Automation (Email-Trigger, Crons, Webhooks)
- **Port:** 5678
- **Workflows:** 44 Exports (OPT-007: Inventar inkonsistent!)
- **Key Workflows:** Daily Report Trigger (17:00), JARVIS Executive Summary (18:00)
- **Kritikalität:** 🟠 HOCH — Automatisierte Prozesse fallen aus

### Postiz (Social Media)
- **Was:** Social Media Scheduling & Automation
- **RAM:** 1.4GB (⚠️ OPT-003: Memory Leak Risiko)
- **Elasticsearch:** 309MB (⚠️ OPT-008: Brauchen wir das?)
- **Kritikalität:** 🟡 MITTEL — Nicht Revenue-kritisch

### JAMES Bridge
- **Was:** System-Fixer. Kann Docker, N8N, Files, Crons steuern.
- **Port:** 9001
- **Auth:** Bearer Token (JAMES_BRIDGE_TOKEN aus .env)
- **Wer nutzt:** Alle Agents direkt (kein JARVIS-Umweg nötig)
- **Kritikalität:** 🟡 MITTEL — Convenience, nicht kritisch

---

## 2. DATA FLOW

### Agent Communication
```
DOM → Telegram → JARVIS (Main Session)
                    ↓
              Task Queue (/data/agents/[TEAM]/[LEAD]/tasks/QUEUE.md)
                    ↓
              Agent Heartbeat liest Queue
                    ↓
              Agent führt aus → schreibt Ergebnis
                    ↓
              tg-send.sh → Telegram Gruppe → DOM sieht's
```

### Lead Pipeline
```
Marketing (STEVE) generiert Lead
    ↓
Lead-File: /data/unternehmen/[FIRMA]/_SALES/PIPELINE/NEW/lead-XXX.json
    ↓
DONNA qualifiziert (BANT)
    ↓
Pipeline-Stage: NEW → QUALIFIED → PROPOSAL → NEGOTIATION → WON/LOST
    ↓
Mission Control Dashboard zeigt Status
    ↓
API: GET /api/leads?company=X&stage=Y
```

### Daily Report Chain
```
17:00  N8N triggert alle Team-Chiefs
       ↓
       STEVE → /data/agents/_DAILY-REPORTS/MARKETING/[DATUM].md
       DONALD → /data/agents/_DAILY-REPORTS/SALES/[DATUM].md
       DONNA → /data/agents/_DAILY-REPORTS/BACKOFFICE/[DATUM].md
       ARCHI → /data/agents/_DAILY-REPORTS/DEV/[DATUM].md
       IRIS → /data/agents/_DAILY-REPORTS/DESIGN/[DATUM].md
       FELIX → /data/agents/_DAILY-REPORTS/FULFILLMENT/[DATUM].md
       ↓
18:00  N8N triggert JARVIS
       ↓
       JARVIS liest ALLE Reports → Executive Daily Summary → DOM via Telegram
```

---

## 3. ARCHITEKTUR-PRINZIPIEN

### P1: Filesystem First
Queues, Configs, Reports, Agent-Dateien = alles Filesystem. Kein Extra-Service nötig. Human-readable, debuggable, `cat`-able.

### P2: Zero New Infrastructure
Bevor ein neuer Service gestartet wird: Geht es mit existierenden Tools? File-based Lösung > neuer Container > neue Datenbank > externer Service.

### P3: Resource Awareness
VPS hat begrenzte Ressourcen. Jeder Container braucht RAM. Disk füllt sich. Swap ist langsam. Immer messen vor dem Deployen.

```
AKTUELLE RESOURCE-LIMITS (bekannt):
- Postiz:         ~1.4GB RAM (zu viel)
- Elasticsearch:  ~309MB RAM (evtl. unnötig)
- Swap:           ~60% genutzt (OPT-004)
- Disk:           ~72% (OPT-009, 4-6 Wochen bis kritisch)
```

### P4: Fail Graceful
Kein Service-Ausfall darf das ganze System lahmlegen. Brain down? Agents arbeiten weiter (ohne Memory). Dashboard down? Agents arbeiten weiter (über Telegram). Ein Service = ein Failure Domain.

### P5: Zero Downtime
Rolling Updates. Blue-Green wenn nötig. N8N, Mission Control, Brain — alles muss 24/7 laufen. Keine Maintenance Windows ohne Plan B.

### P6: Observable
Jeder Service muss beobachtbar sein: Health Endpoints, Logs, Metriken. Wenn ich nicht messen kann ob es läuft, läuft es nicht.

---

## 4. TECHNOLOGIE-ENTSCHEIDUNGEN (ADR)

| # | Datum | Entscheidung | Begründung | Status |
|---|---|---|---|---|
| ADR-001 | 2026-02 | React + Vite (nicht Next.js) | Simpler, kein SSR nötig für internes Dashboard | ✅ |
| ADR-002 | 2026-02 | Tailwind (nicht CSS Modules) | Schneller, konsistenter, Dark Mode built-in | ✅ |
| ADR-003 | 2026-02 | File-based Queues (nicht DB) | Zero Infrastructure, alle Agents können lesen/schreiben | ✅ |
| ADR-004 | 2026-02 | Polling (nicht WebSocket) | Simpler für Phase 1, WS kommt in Phase 2 | ✅ |
| ADR-005 | 2026-02 | A2A File-based (nicht HTTP) | Agents nutzen exec nativ, kein Server nötig | 📋 Design |
| ADR-006 | 2026-02 | Qdrant (nicht Pinecone/Weaviate) | Self-hosted, keine laufenden Kosten, gut genug | ✅ |
| ADR-007 | 2026-02 | Node.js Backend (nicht Python) | Gleiche Sprache wie Frontend, schneller Entwicklung | ✅ |

### Entscheidungs-Framework für neue Tech
```
1. Brauchen wir das WIRKLICH?          → Nein? → Nicht bauen.
2. Geht es mit dem was wir haben?      → Ja? → Kein neuer Service.
3. Self-hosted oder Cloud?             → Self-hosted wenn RAM/Disk reicht.
4. Wie viel RAM/Disk braucht es?       → Messen BEVOR deployen.
5. Was passiert wenn es ausfällt?      → Graceful Degradation planen.
6. Wer maintained es langfristig?      → Kein Maintainer? → Nicht einführen.
```

---

## 5. PROJEKT-STRUKTUR

### Mission Control Repo
```
/data/mission-control/repo/
├── src/
│   ├── pages/                 # Route-Components
│   │   ├── AgentMonitoringPage.tsx
│   │   ├── SalesPage.tsx
│   │   ├── LeadsPage.tsx
│   │   └── ...
│   ├── components/            # Shared Components
│   │   ├── DesktopSidebar.tsx
│   │   ├── TabBar.tsx
│   │   └── ...
│   ├── api/                   # API Client Functions
│   ├── App.tsx                # Router + Layout
│   └── main.tsx               # Entry Point
├── server.js                  # Express Backend (Port 3001)
├── dist/                      # Build Output
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── vite.config.ts
```

### Agent Filesystem
```
/data/agents/
├── scripts/                   # Shared Scripts (tg-send, brain-*, pipeline-manager)
├── _DAILY-REPORTS/            # Team Daily Reports für JARVIS
│   ├── MARKETING/
│   ├── SALES/
│   ├── DEV/
│   ├── BACKOFFICE/
│   ├── DESIGN/
│   └── FULFILLMENT/
├── _COMMS/                    # A2A Communication (Design fertig, Implementation pending)
├── BRAIN/                     # Brain System Files
├── DEV/ARCHITECT/tasks/       # DEV Team Queue
├── BACKOFFICE/DONNA/tasks/    # Backoffice Queue
├── JARVIS/                    # JARVIS Master-Board
└── WORKFLOWS/                 # N8N Workflow Exports
```

### Firmen-Daten
```
/data/unternehmen/
├── DEALIO/
│   └── _SALES/PIPELINE/       # NEW, QUALIFIED, PROPOSAL-SENT, etc.
├── DEVCODE/
│   └── _SALES/PIPELINE/
├── WRANA-CAPITAL/
│   └── _SALES/PIPELINE/
├── SYSTEMS/
├── SFE/
└── ... (pro Firma)
```

---

## 6. SCALING ROADMAP

### Phase 1: JETZT (0-50K MRR)
- Alles auf einem VPS
- File-based Queues, Filesystem Storage
- Manual Deployments, Docker Compose
- Monitoring: Docker Stats + Health Endpoints

### Phase 2: WACHSTUM (50-250K MRR)
- Separate DB-Server (Supabase dedicated)
- CDN für Static Assets
- Automated Backups
- Basic CI/CD Pipeline
- WebSocket für Real-Time Updates

### Phase 3: SCALE (250K-1M MRR)
- Multi-Server Setup (Load Balancer)
- Kubernetes oder Docker Swarm
- Centralized Logging (ELK oder Loki)
- APM (Application Performance Monitoring)
- Auto-Scaling für High-Traffic Services
- Disaster Recovery Plan

**Regel:** Nicht über-engineeren. Phase 1 Features in Phase 1 Stack. Erst skalieren wenn's nötig ist.

---

## 7. INCIDENT RESPONSE

### Severity Levels
```
SEV-1 KRITISCH: Production komplett down, Datenverlust
  → Sofort fixen. Alles andere stoppen. DOM + JARVIS informieren.
  → Max Time-to-Fix: 30 Minuten

SEV-2 MAJOR: Service degradiert, Feature kaputt, Performance-Einbruch
  → Innerhalb 2h fixen. DOM informieren.
  → Max Time-to-Fix: 2 Stunden

SEV-3 MINOR: Kosmetisch, Edge Case, nicht-kritischer Bug
  → In Queue. Nächster Sprint.

SEV-4 NICE-TO-HAVE: Improvement, Refactoring
  → Backlog.
```

### Incident Checklist
```
1. ERKENNEN:   Was genau ist kaputt? (Nicht raten — verifizieren)
2. EINGRENZEN: Seit wann? Was hat sich geändert? Welcher Service?
3. ISOLIEREN:  Kann ich den Impact begrenzen? (Feature Flag, Rollback)
4. FIXEN:      Root Cause → Minimaler Fix → Deploy
5. VERIFYEN:   Funktioniert es wirklich? (Nicht "sollte gehen")
6. MELDEN:     Telegram + Delivery Report
7. LERNEN:     Was hat zum Bug geführt? Wie verhindern wir's?
```

_ARCHITECTURE.md wird bei jeder Infrastruktur-Änderung aktualisiert._
