# BOOTSTRAP.md — Setup abgeschlossen

ARCHI ist konfiguriert. Dateien laden:

**IMMER:** IDENTITY.md → SOUL.md → USER.md → MEMORY.md (+ Tages-Memory)
**Bei Bedarf:** HEARTBEAT.md (Queue + Pipeline), TOOLS.md (Stack + Endpoints), AGENTS.md (Team)

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
cat /data/agents/DEV/ARCHITECT/tasks/QUEUE.md
```

_Diese Datei kann gelöscht werden._
