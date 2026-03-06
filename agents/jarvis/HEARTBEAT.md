---
summary: "JARVIS Heartbeat-Protokoll — Proaktive Checks"
read_when:
  - On every heartbeat poll
  - When configuring cron jobs
---

# HEARTBEAT.md — Proaktive Checks

## Heartbeat-Protokoll

Beim Heartbeat-Poll: Checks basierend auf Tageszeit ausführen.
`HEARTBEAT_OK` wenn nichts Relevantes. Proaktiv melden wenn Attention nötig.

---

## Check-Rotation (nach Uhrzeit)

### 09:00 — Morning Briefing (PFLICHT!)
- [ ] **Task-Check:** `bash scripts/task-manager.sh` → Zeigt alle ACTIVE Tasks
- [ ] **Morning Briefing an Dom senden:**
  1. Lies gestern's Memory: `memory/[GESTERN].md`
  2. Lies Team Status: Falls `TEAM-BOARD.md` existiert
  3. Lies **TASKS.md** → Was steht heute an
  4. **Briefing via Telegram:**
     ```
     ☀️ GOOD MORNING DOM!
     
     📅 HEUTE:
     - [Wichtigste Tasks/Events]
     
     ✅ GESTERN DONE:
     - [Top 3 Achievements]
     
     ⚠️ BRAUCHT DEINE ATTENTION:
     - [Dringendes oder: Alles läuft]
     
     📈 QUICK STATS:
     - Teams Status: [Kurz-Summary]
     ```
  5. **Sende via:** `bash /data/agents/scripts/tg-send.sh dom "[Message]"`

### ~12:00 — Midday Check
- [ ] Laufende Tasks on track?
- [ ] Neue wichtige Infos?
- Wenn nichts → HEARTBEAT_OK

### 18:00 — EXECUTIVE DAILY SUMMARY (PFLICHT!)

**N8N triggert um 17:00 alle Team Chiefs für Daily Reports.**
**N8N triggert JARVIS um 18:00: "Reports da, Executive Summary schreiben!"**

**Schritt 1: Alle Reports laden**
```
/data/agents/_DAILY-REPORTS/MARKETING/[DATUM].md   (STEVE)
/data/agents/_DAILY-REPORTS/SALES/[DATUM].md        (DONALD)
/data/agents/_DAILY-REPORTS/BACKOFFICE/[DATUM].md   (DONNA)
/data/agents/_DAILY-REPORTS/FULFILLMENT/[DATUM].md  (FELIX)
/data/agents/_DAILY-REPORTS/DEV/[DATUM].md          (ARCHI)
/data/agents/_DAILY-REPORTS/DESIGN/[DATUM].md       (IRIS)
```

**Schritt 2: Cross-Team Analyse**
- Was läuft gut über alle Teams?
- Wo Probleme oder Risiken?
- Was hängt zusammen? (Sales Lead → Marketing-Kampagne)
- Was muss Dom jetzt wissen?

**Schritt 3: Executive Summary an Dom**
```markdown
📊 DAILY SUMMARY — [DATUM]

🏆 TOP HIGHLIGHTS
1. [Wichtigstes Positive]
2. [Zweites Positive]
3. [Drittes Positive]

⚠️ PROBLEME & RISIKEN
1. [Wichtigstes Problem]
2. [Zweites Problem]

🎯 DOM — DEINE ENTSCHEIDUNGEN
1. [Was Dom entscheiden muss]

📈 MORGEN'S PRIORITÄTEN
- Marketing: [X]
- Sales: [Y]
- [Weiteres]
```

- [ ] Memory für heute updaten: `memory/YYYY-MM-DD.md`
- [ ] **Session Review schreiben** — `bash ~/.openclaw/workspace/scripts/session-review.sh`
- [ ] **Freitags:** Weekly Pattern Recognition + Dashboard Update

### ~21:00 — Night Check (leicht)
- [ ] Letzte wichtige Nachrichten
- [ ] Memory-Notizen für morgen
- Nicht stören wenn nichts Wichtiges

### 23:00 — ARIA PHASE A: ANALYSE
**AUTOMATED — kein Dom-Input nötig**
- Alle Team-KPIs scannen
- Fehler und Exceptions sammeln
- Quality-Gate-Fails dokumentieren
- Output: Vollständige Tages-Bilanz
→ `ARIA-ALGORITHMUS.md` Phase A | max. 15 Min

### 23:30 — ARIA PHASE R: REFLEXION
**AUTOMATED — kein Dom-Input nötig**
- Root Cause auf 3 Ebenen (direkt → systemisch → strukturell)
- Dokumentieren in Memory
- Änderungs-Typ: [PROMPT] / [PROZESS] / [REGEL] / [ESKALATION]
→ `ARIA-ALGORITHMUS.md` Phase R | max. 20 Min

### 23:59–08:00 — Ruhemodus
- NUR bei echten Notfällen melden
- ARIA läuft automated im Hintergrund

### 06:00 — ARIA PHASE I: IMPLEMENTATION
**AUTOMATED — kein Dom-Input nötig (außer ESKALATION)**
- Änderung aus Root-Cause-Analyse implementieren + versionieren
- Betroffene Teams benachrichtigen
- Change im Learning-Log dokumentieren
→ `ARIA-ALGORITHMUS.md` Phase I | max. 30 Min

### Sonntag 18:00 — ARIA PHASE A: AUSWERTUNG (WEEKLY)
- Baseline vs. Nach-Änderungs-Metriken (7 Tage)
- COMMIT (bleibt) oder REVERT (rückgängig)
- Learning dokumentieren
- ELON reviews

---

## Wann Dom proaktiv kontaktieren?

**Ja:** Dringende Nachricht, Kalender-Event <2h, System-Fehler, >8h seit letztem Kontakt + was Relevantes da
**Nein:** Ruhephase (23-08) außer Notfall, Dom offensichtlich beschäftigt, nichts Neues, letzter Check <30min

---

## Work Mode — Task Queue (PFLICHT!)

**JARVIS beim Heartbeat: Alle Team-Queues scannen!**

```bash
grep -l "🔴 NEU" /data/agents/*/QUEUE.md 2>/dev/null || \
grep -l "🔴 NEU" /data/agents/*/*/tasks/QUEUE.md 2>/dev/null
cat /data/agents/JARVIS/MASTER-BOARD.md
```

**Wenn keine dringenden Checks:** Nicht `HEARTBEAT_OK` — stattdessen arbeiten!

### Task Queue Workflow:
1. `tasks/QUEUE.md` lesen
2. Höchst-priorisierten "Ready"-Task wählen
3. Echte Arbeit machen
4. Queue updaten (In Progress → Done / neue Tasks)
5. Wenn Zeit übrig: nächsten Task

### Token-Priorität:
1. Dom's direkte Anfragen (immer zuerst)
2. Dringende Tasks (zeitkritisch)
3. High-Impact Tasks
4. Maintenance (Verbesserungen, Cleanup)

Token-Limit nah: Task abschließen, Notizen schreiben, schlafen.

---

## Proaktive Background-Tasks (ohne Anfrage)

JARVIS darf autonom beim Heartbeat:
- Memory-Dateien lesen und organisieren
- `MEMORY.md` mit Erkenntnissen updaten
- Workspace-Dateien reviewen und verbessern
- Veraltete Infos entfernen
- Tasks aus `tasks/QUEUE.md` abarbeiten

---

## Learning Engine

### Nach jeder Session (>5min oder >10 Messages):
```bash
bash ~/.openclaw/workspace/scripts/session-review.sh
```
→ Template in `learning/sessions/` ausfüllen

### Freitag 18:30 — Pattern Recognition:
```bash
bash ~/.openclaw/workspace/scripts/pattern-recognition.sh
```
→ Patterns aktualisieren → Dashboard updaten → Weekly Retro an Dom

### Samstag morgens — Integration:
Top 3 Improvements priorisieren → Implementieren → CHANGELOG.md

---

## Kosten-Awareness

Heartbeat läuft auf **Haiku** (günstigstes Modell).
Kein leeres `HEARTBEAT_OK` — lieber einen kleinen Task erledigen.
