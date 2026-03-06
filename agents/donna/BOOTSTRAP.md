# BOOTSTRAP.md — Setup abgeschlossen

DONNA ist konfiguriert. Dateien laden:

**IMMER:** IDENTITY.md → SOUL.md → USER.md → MEMORY.md (+ Tages-Memory)
**Bei Bedarf:** SECURITY.md, PROCESSES.md, HEARTBEAT.md, TOOLS.md, AGENTS.md

## Session-Start Reihenfolge
```bash
# 1. Wer bin ich
cat IDENTITY.md

# 2. Wie arbeite ich
cat SOUL.md

# 3. Für wen
cat USER.md

# 4. Was weiß ich
cat MEMORY.md
cat memory/$(date +%Y-%m-%d).md 2>/dev/null

# 5. Was steht an
cat /data/agents/BACKOFFICE/DONNA/tasks/QUEUE.md 2>/dev/null
```

## First Run
Beim allerersten Start: MEMORY.md → "First Run Aufgaben" abarbeiten (Email-Zugänge, Labels, Calendar, Stripe etc.)

_Diese Datei kann gelöscht werden._
