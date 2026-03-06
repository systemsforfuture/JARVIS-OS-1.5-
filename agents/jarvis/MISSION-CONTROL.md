---
summary: "JARVIS Mission Control — Tasks, Pipeline, Quality, KPIs, Learning, Healing"
read_when:
  - When creating or managing tasks
  - When checking pipeline or bugs
  - When delivering output to Dom
  - When reviewing quality or KPIs
---

# MISSION-CONTROL.md — Die zentrale Wahrheit

**Dashboard:** http://187.77.75.92:8888/

### Dashboard-Navigation
| Sektion | URL | Was dort ist |
|---|---|---|
| Home | `/` | Umsatz, Container-Status, Tasks in Queue, Leads, Teams, Unternehmen, Agent-Aktivität, System |
| Tasks | `/tasks` | Kanban-Board: BACKLOG → AKTIV → REVIEW → DONE |
| Leads | `/leads` | Lead-Pipeline: Verhandlung/Angebot/Qualifiziert/Kontaktiert/Neu, Filter per Firma |
| Sales | `/sales` | Umsatz, Kunden, Pipeline, Conversion, Donald's Workspace |
| Design | `/design` | IRIS Queue, Workspace-Dateien |
| Firmen | `/firmen` | Firmenliste mit Status, Dateien pro Firma |
| Backoffice | `/backoffice` | Office-Manager Queue, Workspace |
| Agents | `/agents` | 42 Agents in 7 Teams, Skills pro Agent |
| Monitor | `/monitor` | Live Agent-Status: Aktiv/Bereit/Idle, Sessions, Skills |
| Bots | `/bots` | Bot-Konfiguration |
| N8N | `/n8n` | N8N Workflow-Übersicht |
| Setup | `/setup` | System-Konfiguration |

## 0. GRUNDPRINZIP

**Mission Control ist ein ECHTES DASHBOARD auf dem VPS — keine Datei.**

Alles existiert in Mission Control. Wenn es nicht dort steht, existiert es nicht.

Jede Aufgabe, jeder Bug, jeder Status-Wechsel, jede KPI, jedes Learning → Mission Control Dashboard.
Memory, Telegram, Dateien sind Werkzeuge. Das Dashboard ist die Wahrheit.

---

## 1. AUFGABEN-SYSTEM

```
🎯 TASK-ID:        [FIRMA]-[TEAM]-[YYYY-MM-DD]-[NR]
                    Beispiel: SNIP-MKT-2026-02-26-001

📋 Titel:          [Kurzer, klarer Name]
📝 Beschreibung:   [Was genau gemacht werden muss]
🏢 Firma:          [Welche Firma]
👤 Erstellt von:   [Dom | JARVIS | Teamleiter]
📅 Erstellt am:    [Datum + Uhrzeit]
⏰ Deadline:       [Exaktes Datum]
🔴 Priorität:      CRITICAL | HIGH | MEDIUM | LOW
🔄 Release-Typ:    AUTO | DOM-APPROVAL
📊 Status:         BACKLOG | AKTIV | REVIEW | DONE

👥 Zugewiesene Agents (Hauptverantwortlich + Beteiligte)
📎 Unteraufgaben mit Status
💬 Team-Kommunikation (geloggt)
✅ Done-Kriterium (messbar)
📊 Ergebnis (nach Abschluss)
🧠 Learning (nach Abschluss)
```

---

## 2. PIPELINE — 4 Stages

```
BACKLOG → AKTIV → REVIEW → DONE
                    │
                    ↓ QA Mängel?
              ZURÜCK AN AKTIV (mit Notiz)
```

**BACKLOG:** Noch nicht zugewiesen. Max 4h oder Alarm.
**AKTIV:** Agents arbeiten dran. Mindestens 1x/Tag Status-Update wenn Task >1 Tag.
**REVIEW:** QA prüft Done-Kriterium → APPROVED oder REJECTED mit Notiz.
**DONE:** Ergebnis + Learning dokumentiert. Task bleibt permanent.

---

## 3. QUALITY-GATE — 5 Fragen vor JEDER Auslieferung

```
1. ✅ Vollständig?     — Kein TODO, kein TBD, kein "ich gehe davon aus"
2. ✅ Verifiziert?     — Getestet/geprüft, nicht nur geschrieben
3. ✅ Konsistent?      — Kein Widerspruch zu Memory/vergangenen Entscheidungen
4. ✅ Actionable?      — Dom kann sofort handeln, keine Rückfragen nötig
5. ✅ Format korrekt?  — Ergebnis zuerst, richtige Länge, Deutsch
```

**Ein NEIN → Nicht senden. Erst fixen.**

### Quality-Schleife

```
TASK FERTIG
    ↓
[1] SELF-CHECK — 5 Fragen. Alle ✅?
    ↓ JA
[2] TECH-CHECK — Nur bei Code/Deploy
    ↓ PASS
[3] QA REVIEW — Quality Guardian prüft
    ↓ APPROVED
[4] DELIVERY — An Dom oder Auto-Release
    ↓
[5] MEMORY UPDATE — COMPLETED-TASKS.md + Tages-Memory
```

### Eskalationsprotokoll

Nach 2 gescheiterten Quality-Gate-Durchläufen:
```
🚨 ESKALATION: [TASK-NAME]
Problem: [Was blockiert — konkret]
Versucht: [Was 2x probiert wurde]
Optionen:
  A) [Option + Vor/Nachteil]
  B) [Option + Vor/Nachteil]
Empfehlung: [A oder B + Begründung in 1 Satz]
```

---

## 4. BUG-TRACKING

```
🐛 BUG-ID:         BUG-[YYYY-MM-DD]-[NR]
📋 Titel:          [Was ist kaputt?]
📝 Beschreibung:   [Was passiert? Was sollte? Reproduzierbar?]
🏢 Firma/System:   [Wo tritt der Bug auf?]
👤 Gefunden von:   [Agent oder Dom]
🔴 Impact:         CRITICAL | HIGH | MEDIUM | LOW
📊 Status:         NEU | IN ARBEIT | GEFIXT | VERIFIZIERT | GESCHLOSSEN
🔁 Wiederkehrend:  JA/NEIN → Wenn JA → sofort CRITICAL
```

Pipeline: NEU → IN ARBEIT (Dev) → GEFIXT → VERIFIZIERT (QA) → GESCHLOSSEN
Erneut? → Sofort CRITICAL → Dev fixt SOFORT.

---

## 5. DOM-DELIVERY-FORMAT

Wenn ich Dom ein Ergebnis liefere (Telegram):
```
✅ [TASK-ID] [AUFGABE] — erledigt

📊 Ergebnis: [Konkret, mit Zahlen]
⚠️ Offen: [Falls noch was fehlt — sonst weglassen]
▶️ Nächster Schritt: [Was als nächstes passiert]

→ Details: http://187.77.75.92:8888/
```

---

## 6. KPI-FRAMEWORK

**Universal (alle Firmen — täglich):**
- Revenue (heute, Woche, Monat)
- Neue Leads (Anzahl, Quelle)
- Conversion Rate (Lead → Kunde)
- Offene Tasks (Anzahl, Alter)
- Bugs (offen, gefixt)
- Content-Output (Posts, Engagement)

**Firmenspezifisch:**
- SYSTEMS™: MRR, aktive Kunden, Churn Rate, LTV
- DWMUC: Retainer-Kunden, Projekt-Pipeline
- LeadJet: Leads generiert, Cost per Lead, Lead-Qualität
- SNIP: Orders, Avg Order Value, Return Rate
- WAC/Crypto: Portfolio-Wert, ROI, Win-Rate Signale
- ÉlanSÉVEN: Uhren verkauft, E7-Conversions, Brand Awareness

**Regeln:**
- KPIs nicht gemessen = existieren nicht
- Jede Woche: Trend-Analyse
- Jeder Monat: Vollständiger Report an Dom
- KPI sinkt 2 Wochen in Folge → Alarm → Root Cause → Fix

---

## 7. SELF-LEARNING-SYSTEM

### Feedback-Loop
```
AKTION → ERGEBNIS → BEWERTUNG → LEARNING → ANPASSUNG
   ↑                                              │
   └──────────── Nächste Aktion ◄──────────────────┘
```

### Wie Learnings entstehen
1. Jeder abgeschlossene Task → COMPLETED-TASKS.md mit Bewertung (1-10)
2. Jeder Fehler → Bug-Report + Learning in Memory
3. Jede Dom-Korrektur → Learning sofort dokumentieren, Pattern erkennen
4. Jede KPI-Auswertung → Was funktioniert? Was nicht? Warum?

### Learning-Dateien
```
/data/.openclaw/workspace/learnings/
├── GLOBAL-LEARNINGS.md       ← Übergreifend
├── marketing-learnings.md    ← Marketing
├── sales-learnings.md        ← Sales
├── tech-learnings.md         ← Technische Fehler & Fixes
└── [FIRMA]-learnings.md      ← Firmenspezifisch
```

### ELONs Rolle im Self-Learning
ELON scannt regelmäßig:
- COMPLETED-TASKS.md → Muster erkennen
- Bug-Reports → Wiederkehrende Fehler
- Learnings → In Prozessverbesserungen übersetzen
- KPIs → Trends, Anomalien melden

→ Wöchentlicher Optimierungs-Report an JARVIS → Umsetzung oder Eskalation an Dom.

---

## 8. SELF-HEALING-SYSTEM

### Proaktive Checks
Agents suchen AKTIV Fehler — nicht nur reagieren:
- Outputs stichprobenartig testen
- Edge-Cases durchdenken
- Prozesse auf Schwachstellen prüfen
- Verbesserungsideen einbringen

### Bug-Flow
```
FEHLER ERKANNT → BUG-REPORT erstellen → AUTOMATISCH in Dev-Queue
→ Dev fixt → Bug bleibt im System (nie löschen!)
→ Wenn Bug erneut auftritt → CRITICAL → Sofort-Fix
```

---

## 9. NOTFALL-PROTOKOLL

```
SYSTEM-AUSFALL ERKANNT
    ↓
[1] Was genau ist down? Scope bestimmen.
    → Nur ein Service? → docker restart
    → Ganzer Server? → Hosting-Provider
    → Nur Telegram? → Alternative Kommunikation
    ↓
[2] DOM INFORMIEREN — Über jeden verfügbaren Kanal
    → "🚨 [SERVICE] ist down seit [ZEIT]. Ich arbeite am Fix."
    ↓
[3] TRIAGE — Kundenservice = höchste Priorität
    ↓
[4] FIX — docker restart, Logs prüfen, Dev-Team
    ↓
[5] POST-MORTEM — Was? Warum? Wie verhindern? → Tech-Learnings
```

**Backup-Kommunikation wenn Telegram down:**
1. E-Mail an Dom
2. WhatsApp
3. Discord
4. Mission Control Dashboard Notiz (http://187.77.75.92:8888/)

---

## 10. TECHNISCHE UMSETZUNG

**Dashboard LIVE:** http://187.77.75.92:8888/

Tasks, Bugs, KPIs und Pipeline werden über das Dashboard verwaltet.
JARVIS interagiert mit Mission Control über API/Dashboard — nicht über Dateien.

> Für Übergangslösungen bis volle API-Integration: COMPLETED-TASKS.md + Pipeline-Manager-Script.

---

## 11. JARVIS PFLICHT

```
BEI JEDER AUFGABE:
[1] In Mission Control anlegen
[2] Agents zuweisen
[3] Status bei jedem Wechsel aktualisieren
[4] Team-Kommunikation loggen
[5] Bei Abschluss: Ergebnis + Learning
[6] NIEMALS Task nur in Telegram haben
```

**Task nicht in Mission Control = existiert nicht. Gilt auch für mich.**
