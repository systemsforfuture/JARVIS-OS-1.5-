---
summary: "DONNA Tools — Gmail, Calendar, Stripe, Brain, Telegram, Pipeline, Scripts"
read_when:
  - When using APIs or tools
  - When checking system endpoints
---

# TOOLS.md — Meine Werkzeuge

## 1. TELEGRAM (Haupt-Kommunikation)

### Backoffice-Gruppe
- **Chat-ID:** -5214094648
- **Script:** `bash /data/agents/scripts/tg-send.sh donna "NACHRICHT"`

### Dom direkt
- **Dom's Telegram-ID:** 8512848532
- **Script:** `bash /data/agents/scripts/tg-send.sh donna "NACHRICHT"` (geht in Backoffice-Gruppe)

### Wann Telegram nutzen
- Morning Brief (06:00)
- Evening Brief (18:00)
- P1 Alerts (sofort)
- P2 Freigaben
- Weekly Brief (Mo 08:00)
- Monthly Finance Report (1. des Monats)

### 🚨 TELEGRAM-ROUTING REGEL (von JARVIS — KRITISCH!)
```bash
# ✅ RICHTIG — Donna nutzt eigenen Bot
bash /data/agents/scripts/tg-send.sh donna "📋 REPORT DONE..."

# ❌ FALSCH — Donna nutzt Team-Namen
bash /data/agents/scripts/tg-send.sh backoffice "..."  # Kommt von JARVIS statt DONNA
```

## 2. MISSION CONTROL DASHBOARD

**URL:** http://187.77.75.92:8888/

| Route | Was |
|---|---|
| /tasks | Task-Board, Pipeline |
| /leads | Lead-Tracking |
| /sales | Revenue, Deals |
| /companies | Firmen-Übersicht |
| /backoffice | Admin |
| /agent-monitoring | Live Agent Status |

## 3. EMAIL (Gmail API)

Alle 13 Firmen + Dom privat. Postfächer werden von DONNA eingetragen sobald Zugang besteht.

**Pro Postfach:**
- Alle 15 Min scannen
- Inbox Zero durchführen
- Label-Struktur pflegen (siehe PROCESSES.md)
- P1-P4 Priorisierung
- Autonom antworten (P3/P4) oder eskalieren (P1/P2)

### Gmail Label-Struktur (identisch pro Firma)
```
[FIRMA]/
  P1-SOFORT/ P2-HEUTE/ P3-WOCHE/ ERLEDIGT/
  LEADS/ (Neu/ Qualifiziert/ Angebot-raus/)
  KUNDEN/ (Aktiv/ Abgeschlossen/)
  RECHNUNGEN/ (Offen/ Bezahlt/ Überfällig/)
  INTERN/ RECHT/ SICHERHEIT/VERDACHT/ ARCHIV/
```

## 4. KALENDER (Google Calendar API)

- Dom's Hauptkalender + Firmen-Kalender
- Buffer: 15 Min zwischen Meetings
- Keine Meetings vor 09:00 oder nach 19:00 ohne Freigabe
- Briefings 30 Min vorher, Follow-ups 2h nachher

## 5. FINANZEN (Stripe / Buchhaltung)

- **Lese-Zugang:** Alle Firmen, alle Unteraccounts
- **Schreib-Zugang:** Nur Rechnungen erstellen, Mahnungen senden
- **VERBOTEN:** Refunds, Payouts, Käufe, Abo-Änderungen

## 6. BRAIN SYSTEM

- **API:** http://localhost:7700
- **Qdrant:** 172.17.0.5:6333

```bash
# Memory speichern
bash /data/agents/scripts/brain-store.sh DONNA [collection] [title] [content] [tags]

# Suchen (z.B. vor Kunden-Email: "Was wissen wir über diesen Kunden?")
bash /data/agents/scripts/brain-search.sh [query] [collection] DONNA [limit]

# Broadcast (an alle Agents)
bash /data/agents/scripts/brain-broadcast.sh DONNA [title] [content] [tags]

# Stats
bash /data/agents/scripts/brain-stats.sh
```

### Wann Brain nutzen?
- Nach jedem wichtigen Kundenkontakt → brain-store (knowledge)
- Vor Kunden-Email → brain-search (Kunden-Historie?)
- Neue Prozess-Learnings → brain-store (knowledge, tag: process)
- Wichtige Dom-Entscheidungen → brain-store (decisions)

## 7. PIPELINE-MANAGEMENT

```bash
# Queue lesen
cat /data/agents/BACKOFFICE/DONNA/tasks/QUEUE.md

# Task starten
bash /data/agents/scripts/pipeline-manager.sh start BACKOFFICE [TASK_ID]

# Task fertig → Review
bash /data/agents/scripts/pipeline-manager.sh review BACKOFFICE [TASK_ID] "[Ergebnis]"
```

### Daily Report für JARVIS
```
/data/agents/_DAILY-REPORTS/BACKOFFICE/[DATUM].md
```

### Conversation speichern
```bash
bash /data/agents/scripts/save-conversation.sh donna "[Dom]" "[Meine Antwort]"
```

## 8. JAMES — System-Fixer

**Kein Agent braucht Erlaubnis — JEDER kann JAMES direkt ansprechen.**

```bash
curl -s -X POST http://localhost:9001/task \
  -H "Authorization: Bearer JAMES_BRIDGE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"task": "Beschreibung", "priority": "high"}'
```

JAMES kann: Docker steuern, N8N Workflows, System-Fixes, Crons, Files.

## 9. N8N

- **URL:** http://n8n-main:5678
- **API Key:** in /docker/n8n-pp1b/.env (N8N_API_KEY)
- **JAMES Bridge:** http://localhost:9001

## 10. WEITERE TOOLS

- **Google Drive:** Ordner-Struktur pro Firma
- **Supabase:** CRM, Rechnungen, Tasks, Journal-Datenbank

## 11. MEINE DATEIEN

```
IDENTITY.md     — Wer ich bin
SOUL.md         — Was mich antreibt
USER.md         — Wer Dom ist
MEMORY.md       — Langzeit-Gedächtnis
SECURITY.md     — Identity + Cyber + Finanz-Schutz
PROCESSES.md    — Email, CRM, Rechnungen, Templates
HEARTBEAT.md    — Tagesrhythmus, Routinen
TOOLS.md        — Diese Datei
AGENTS.md       — Team-Übersicht
BOOTSTRAP.md    — Einmalig beim Start
memory/YYYY-MM-DD.md — Tages-Logs + Journal
```
