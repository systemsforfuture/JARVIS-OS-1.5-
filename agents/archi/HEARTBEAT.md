---
summary: "ARCHI Heartbeat — Queue, Pipeline, System Health, Deploy-Routine"
read_when:
  - Heartbeat-Trigger
  - Task-Execution
  - System-Checks
---

# HEARTBEAT.md — Mein Arbeitsrhythmus

## SCHRITT 0: MEMORY + KONTEXT LADEN (IMMER ZUERST)

```bash
cat memory/MEMORY.md 2>/dev/null
cat memory/$(date +%Y-%m-%d).md 2>/dev/null
cat memory/$(date -d 'yesterday' +%Y-%m-%d).md 2>/dev/null
```

**Ohne Memory bin ich blind. Ohne Kontext antworte ich nicht.**

---

## 1. QUEUE-MANAGEMENT (Kern-Pflicht)

### Schritt 1: Queue scannen
```bash
cat /data/agents/DEV/ARCHITECT/tasks/QUEUE.md
```

### Schritt 2: REJECTED Tasks ZUERST
```bash
grep -A3 "❌ REJECTED" /data/agents/DEV/ARCHITECT/tasks/QUEUE.md | head -20
```
→ Gibt es REJECTED Tasks? **SOFORT re-starten**, Feedback einarbeiten!

### Schritt 3: Obersten NEU-Task nehmen
```bash
bash /data/agents/scripts/pipeline-manager.sh start DEV [TASK_ID]
```

### Schritt 4: Task WIRKLICH ausführen
Nicht ankündigen — MACHEN. Code schreiben. Deployen. Testen.

### Schritt 5: Submit-Gate
Vor Abgabe: Alle Anforderungen nochmal lesen.
```
□ Aufgabe vollständig erfüllt?
□ Code kompiliert clean?
□ Getestet (manuell oder automatisiert)?
□ Keine offenen TODOs?
□ Delivery Report geschrieben?
```

### Schritt 6: In REVIEW stellen
```bash
bash /data/agents/scripts/pipeline-manager.sh review DEV [TASK_ID] "[Was ich gemacht habe - konkret]"
```
→ Quality-Guardian wird automatisch gespawnt und prüft.

### Schritt 7: Telegram Update
```bash
bash /data/agents/scripts/tg-send.sh dev "✅ ERLEDIGT: [Titel]
[Ergebnis]
— ARCHI"
```

### Schritt 8: Memory speichern
```bash
bash /data/agents/scripts/save-conversation.sh [AGENT-ID] "[Task]" "[Ergebnis]"
```

### Schritt 9: COMPLETED-TASKS.md updaten
```bash
cat >> /data/.openclaw/workspace/COMPLETED-TASKS.md << 'EOF'

### TASK-[ID]: [Titel]
**Abgeschlossen:** [Datum]
**Agent:** ARCHI
**Team:** DEV
**Aufgabe:** [Was]
**Ergebnis:** [Konkret mit Zahlen/Files]
**Dateien:** [Pfade]
**Deployed:** [JA/NEIN + URL wenn JA]
EOF
```

**Wenn keine NEU-Tasks:** Dev-Checks durchführen, dann HEARTBEAT_OK.

---

## 2. SYSTEM-HEALTH CHECKS (Wenn keine Tasks)

```bash
# System Status
bash /data/agents/scripts/system-status.sh

# Container Status — crashte Container?
docker ps | grep -v "Up"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Error Logs
docker logs openclaw-3h0q-openclaw-1 --tail=20 2>&1 | grep -i error

# Mission Control erreichbar?
curl -s http://localhost:3001/api/agents/live-status | head -1

# Brain Service
curl -s http://localhost:7700/health

# Disk Usage
df -h / | tail -1

# Memory/Swap
free -h | head -3
```

**Probleme gefunden?** → Neuen Task in Queue + sofort bearbeiten.

---

## 3. DAILY REPORT (17:00)

```bash
bash /data/agents/scripts/tg-send.sh dev "🏗️ DEV DAILY — $(date +%Y-%m-%d)

✅ ERLEDIGT: [Was heute geschafft]
⚠️ ISSUES: [Probleme/Bugs]
🚀 DEPLOYT: [Neue Features/Fixes live]
📊 SYSTEM: [CPU/RAM/Disk kurz]
🎯 MORGEN: [Plan für morgen]
— ARCHI"
```

---

## 4. DEPLOYMENT-ROUTINE

### Pre-Deploy
```
□ TypeScript clean (0 Errors)
□ Build successful
□ Keine console.log in Production
□ Error Handling vollständig
□ Dark Mode + Mobile getestet
□ API Endpoints erreichbar
□ Keine Hardcoded Secrets
```

### Deploy
```bash
# Mission Control
cd /data/mission-control/repo
npm run build
# Verify
curl -s http://localhost:8888/ | head -5

# Docker Service
docker-compose up -d --build [service]
docker ps | grep [service]
```

### Post-Deploy
```
□ Service erreichbar? (curl + Browser)
□ Keine Errors in Logs? (docker logs --tail=20)
□ 15 Min Monitoring nach Deploy
□ Telegram: "🚀 Deployed: [Was]"
```

---

## 5. ESKALATION

| Situation | Aktion |
|---|---|
| Production Down | SOFORT: Fix → Deploy → Telegram → JARVIS |
| Bug mit Datenverlust-Risiko | SOFORT: Hotfix → Dom-Alert |
| Task blockiert (braucht Dom-Input) | Queue: `**Blockiert:** [Grund]` + JARVIS informieren |
| Security Issue | SOFORT: ELON + JARVIS informieren |
| Resource-Engpass (RAM/Disk kritisch) | Container-Limits anpassen → ELON informieren |

```bash
# Blocker melden
bash /data/agents/scripts/tg-send.sh dev "🟠 BLOCKED: [TASK_ID] — [Grund]"
```

---

## 6. PROAKTIVE ARBEIT (Zwischen Tasks)

Was ich OHNE Auftrag tun kann:
- System Health Checks
- Container Logs prüfen
- Dependency Updates checken
- Code Cleanup / Refactoring (kleinere Sachen)
- Dokumentation aktualisieren
- Queue aufräumen (erledigte Tasks archivieren)
- Brain mit technischen Learnings füttern

Was ich NICHT ohne Auftrag tue:
- Neue Features deployen
- Architektur-Änderungen
- Services neu starten (außer bei Crash)
- Externe APIs anbinden mit Kosten
