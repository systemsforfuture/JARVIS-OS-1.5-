---
summary: "STEVE Bootstrap — Session-Start Sequenz"
read_when:
  - First session ever
  - After reset
---

# BOOTSTRAP.md — Session Start

## Reihenfolge (PFLICHT)

```bash
# 1. Wer bin ich?
cat IDENTITY.md

# 2. Was treibt mich an?
cat SOUL.md

# 3. Wer ist Dom?
cat USER.md

# 4. Was weiß ich? (nur Main Session)
cat memory/MEMORY.md 2>/dev/null

# 5. Was ist heute/gestern passiert?
cat memory/$(date +%Y-%m-%d).md 2>/dev/null
cat memory/$(date -d 'yesterday' +%Y-%m-%d).md 2>/dev/null

# 6. Habe ich Tasks?
cat /data/agents/MARKETING/STEVE/tasks/QUEUE.md 2>/dev/null
```

## Bei Marketing-Arbeit zusätzlich:
```bash
# 7. Marketing-Frameworks laden
cat MARKETING-PLAYBOOK.md

# 8. Firmen-Referenz laden
cat COMPANIES.md
```

## First-Run Tasks

Wenn `memory/` Ordner nicht existiert:
```bash
mkdir -p memory
echo "# STEVE Memory — $(date +%Y-%m-%d)" > memory/$(date +%Y-%m-%d).md
echo "Session gestartet. Erster Run." >> memory/$(date +%Y-%m-%d).md
```

Wenn Daily Report Ordner nicht existiert:
```bash
mkdir -p /data/agents/_DAILY-REPORTS/MARKETING
```

## Dann: HEARTBEAT.md folgen

Nach Bootstrap → HEARTBEAT.md Schritt 1 (Queue checken) ausführen.

_Diese Datei nach erfolgreichem First-Run: behalten als Referenz, nicht löschen._
