---
summary: "ARCHI Debugging & Diagnostik — 5-Why, Log-Analyse, Performance, Known Issues"
read_when:
  - When debugging any issue
  - When performance is degraded
  - When investigating errors
  - System health issues
---

# DEBUGGING.md — Wie ich Probleme löse

## Philosophie

> "Nie raten. Immer messen. Der Bug ist nie wo du denkst."

Debugging ist kein Zufall. Es ist ein systematischer Prozess. Jeder Bug hat eine Root Cause. Jede Root Cause hat einen Fix. Jeder Fix hat eine Lektion.

---

## 1. DER 5-STEP DEBUGGING PROZESS

```
STEP 1: REPRODUZIEREN
  → Kann ich den Bug zuverlässig auslösen?
  → Wenn nein: Logs. Wenn ja: Weiter.

STEP 2: ISOLIEREN
  → WO genau passiert der Fehler?
  → Frontend? Backend? DB? Netzwerk? Docker?
  → Binäre Suche: Funktioniert es mit halben Daten?
     Funktioniert es auf einem anderen Endpoint?

STEP 3: VERSTEHEN
  → WARUM passiert es? (5-Why Methode)
  → Was ist der erwartete vs. tatsächliche Zustand?
  → Was hat sich geändert seit es zuletzt funktioniert hat?

STEP 4: FIXEN
  → Minimaler Fix für die Root Cause.
  → Nicht das Symptom kaschieren. Die Ursache beheben.
  → Edge Cases mitdenken.

STEP 5: VERIFIZIEREN + LERNEN
  → Bug reproduzieren → jetzt gefixt?
  → Regression? Irgendwas anderes kaputt?
  → Root Cause + Fix in Memory/Brain speichern.
```

---

## 2. DIE 5-WHY METHODE

Niemals beim ersten "Warum" aufhören.

```
BUG: Sales Dashboard zeigt keine Leads

WHY 1: API gibt leeres Array zurück
WHY 2: Directory /data/unternehmen/DEALIO/_SALES/PIPELINE/ existiert nicht
WHY 3: DEALIO hatte eine kaputte Directory-Struktur (falsche Pfade)
WHY 4: Initial-Setup hat falsche Verzeichnisse angelegt
WHY 5: Kein Validation-Script das Directory-Struktur prüft

ROOT CAUSE: Fehlende Validierung bei Firmen-Setup
FIX: Directory repariert + Validation-Check eingebaut
PREVENTION: Setup-Script prüft ab jetzt alle Pfade
```

**Regel:** Gleicher Bug zweimal = ICH habe versagt, nicht das System.

---

## 3. DIAGNOSTIK-TOOLS

### System-Level
```bash
# All-in-One Health Check
bash /data/agents/scripts/system-status.sh

# CPU / Memory / Swap
free -h
cat /proc/loadavg
top -bn1 | head -20

# Disk
df -h /
du -sh /data/* | sort -rh | head -20

# Network
ss -tlnp                          # Offene Ports
curl -w "time: %{time_total}s\n" -s http://localhost:3001/health
```

### Docker
```bash
# Container Status
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Container Ressourcen
docker stats --no-stream

# Container Logs (letzte 50 Zeilen)
docker logs [container] --tail 50

# Container Logs (nur Errors)
docker logs [container] --tail 200 2>&1 | grep -i "error\|fail\|fatal\|exception"

# In Container hinein
docker exec -it [container] sh

# Container Restart
docker restart [container]

# Container komplett neu bauen
docker-compose up -d --build [service]
```

### API Debugging
```bash
# Response + Timing
curl -s -w "\nStatus: %{http_code}\nTime: %{time_total}s\n" \
  http://localhost:3001/api/leads

# Response Body formatiert
curl -s http://localhost:3001/api/leads | python3 -m json.tool

# POST Request testen
curl -s -X POST http://localhost:3001/api/test \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}'

# Header inspizieren
curl -sI http://localhost:3001/health
```

### Brain System
```bash
# Health
curl -s http://localhost:7700/health

# Stats (Collections, Counts)
curl -s http://localhost:7700/stats | python3 -m json.tool

# Semantische Suche testen
bash /data/agents/scripts/brain-search.sh "sales dashboard bug" knowledge ARCHI 3
```

### Frontend Debugging
```bash
# Build + Errors prüfen
cd /data/mission-control/repo/
npm run build 2>&1 | tail -30

# TypeScript Errors
npx tsc --noEmit 2>&1 | head -50

# Bundle Size
ls -lh dist/assets/*.js

# Dev Server starten (für Live-Debugging)
npm run dev -- --host 0.0.0.0 --port 5173
```

### Log-Analyse Patterns
```bash
# Letzte Errors in allen Container-Logs
for c in $(docker ps --format "{{.Names}}"); do
  echo "=== $c ==="
  docker logs $c --tail 20 2>&1 | grep -i "error\|warn\|fail" | tail -5
done

# Agent-Logs
cat /data/agents/logs/ARCHI.log | tail -30

# N8N Workflow Errors
docker logs n8n-main --tail 100 2>&1 | grep -i "error"
```

---

## 4. COMMON BUG PATTERNS

### Pattern: "Funktioniert lokal, nicht in Production"
```
CHECK 1: Environment Variables gesetzt? (.env vorhanden?)
CHECK 2: Ports korrekt? (Container vs. Host Mapping)
CHECK 3: Build aktuell? (dist/ vs. src/ — wurde rebuild gemacht?)
CHECK 4: CORS-Einstellungen korrekt?
CHECK 5: File Permissions (Docker non-root User?)
```

### Pattern: "API gibt 500 zurück"
```
CHECK 1: docker logs [container] --tail 50 → Stack Trace?
CHECK 2: Input-Daten korrekt? (curl mit bekannt-guten Daten testen)
CHECK 3: Filesystem erreichbar? (Permissions, Disk full?)
CHECK 4: External Service down? (Brain, Supabase, etc.)
CHECK 5: Memory-Limit erreicht? (docker stats)
```

### Pattern: "Frontend zeigt nichts / weiße Seite"
```
CHECK 1: Browser Console → JavaScript Errors?
CHECK 2: Network Tab → API Calls fehlgeschlagen?
CHECK 3: Build clean? (npm run build → 0 Errors?)
CHECK 4: Routing korrekt? (React Router, Fallback auf index.html?)
CHECK 5: Assets laden? (CSS, JS Files 200 OK?)
```

### Pattern: "Container startet nicht"
```
CHECK 1: docker logs [container] → Startup Error?
CHECK 2: Port bereits belegt? (ss -tlnp | grep [port])
CHECK 3: Disk full? (df -h /)
CHECK 4: Image korrekt? (docker images | grep [name])
CHECK 5: Depends-On Service läuft? (DB, Redis, etc.)
```

### Pattern: "Alles langsam"
```
CHECK 1: Swap aktiv? (free -h → Swap > 50% = Problem)
CHECK 2: Welcher Container frisst RAM? (docker stats)
CHECK 3: Disk I/O? (iostat oder iotop wenn installiert)
CHECK 4: CPU-Last? (cat /proc/loadavg → >2.0 = Problem auf 2-Core)
CHECK 5: Network? (ping, curl Timing → DNS? Latency?)
```

---

## 5. PERFORMANCE DEBUGGING

### Wo ist der Bottleneck?
```
FRONTEND:
  - Lighthouse Audit → Performance Score
  - Bundle Size → < 500KB gzipped?
  - Render Time → React Profiler
  - Netzwerk → Waterfall im DevTools

BACKEND:
  - Response Time → curl -w "%{time_total}"
  - DB Queries → Query Logging aktivieren
  - N+1 Problem? → Zu viele Queries für eine Seite?
  - Memory Leak? → docker stats über Zeit beobachten

SYSTEM:
  - CPU Bound → top, htop
  - Memory Bound → free -h, Swap-Nutzung
  - I/O Bound → iotop, Disk-Geschwindigkeit
  - Network Bound → Latency, DNS, Bandwidth
```

### Performance Optimierung Priorität
```
1. ALGORITHMUS (O(n²) → O(n log n)) → Größter Impact
2. CACHING (Ergebnis speichern statt nochmal berechnen)
3. LAZY LOADING (nur laden was sichtbar ist)
4. BATCH OPERATIONS (10 einzelne Queries → 1 Batch-Query)
5. INFRASTRUCTURE (mehr RAM, schnellere Disk) → LETZTES Mittel
```

---

## 6. KNOWN ISSUES TRACKER

Von ELON's OPTIMIZATION-LIST — meine Verantwortung:

| ID | Severity | Problem | Root Cause | Fix-Plan |
|---|---|---|---|---|
| OPT-001 | 🔴 | API-Keys im Plaintext | Historisch gewachsen | → Vault-Migration (braucht Plan) |
| OPT-003 | 🟠 | Postiz Memory 1.4GB | Memory Leak oder Config | → mem_limit setzen + beobachten |
| OPT-004 | 🟠 | Swap 60% genutzt | Zu viele Container für RAM | → Container-Limits optimieren |
| OPT-007 | 🟠 | N8N Workflow-Inventar | 44 Exports vs 2 in Summary | → Audit + Cleanup |
| OPT-008 | 🟠 | Elasticsearch 309MB | Postiz Standard-Dependency | → Usage prüfen, ggf. kill |
| OPT-009 | 🟡 | Disk 72% | Logs, Images, Exports | → Cleanup-Script |
| OPT-012 | 🟡 | DEV Queue 155 Lines | Backlog-Stau | → Review + zusammenfassen |

### Fix-Priorisierung
```
SOFORT:  OPT-001 (Security)
DIESE WOCHE: OPT-003, OPT-004 (Stability)
NÄCHSTE WOCHE: OPT-008, OPT-009 (Resources)
BACKLOG: OPT-007, OPT-012 (Hygiene)
```

---

## 7. POST-MORTEM TEMPLATE

Nach jedem SEV-1 oder SEV-2 Incident:

```markdown
## POST-MORTEM: [Titel]
**Datum:** [YYYY-MM-DD]
**Severity:** SEV-[1/2]
**Duration:** [Wie lange war es kaputt?]
**Impact:** [Was ging nicht? Wer war betroffen?]

### Timeline
- [HH:MM] Bug entdeckt durch [Wie]
- [HH:MM] Root Cause identifiziert
- [HH:MM] Fix deployed
- [HH:MM] Verified + Normal Operation

### Root Cause
[5-Why Analyse]

### Fix
[Was wurde geändert]

### Prevention
[Was tun wir damit das NICHT nochmal passiert]

### Learnings
[Was haben wir gelernt]
```

Post-Mortems werden in Brain gespeichert:
```bash
bash /data/agents/scripts/brain-store.sh ARCHI knowledge \
  "POST-MORTEM: [Titel]" "[Inhalt]" "post-mortem,incident,bug"
```

---

## 8. DEBUGGING MINDSET

```
□ Nicht raten — MESSEN. Hypothese → Test → Beweis.
□ Nicht fixen was ich nicht verstehe — erst Root Cause.
□ Nicht das Symptom kaschieren — die Ursache beheben.
□ Einer nach dem anderen — nie 3 Dinge gleichzeitig ändern.
□ Immer Rollback-Plan haben BEVOR ich was ändere.
□ Nach dem Fix: Konnte ich das VERHINDERN haben? → System verbessern.
□ Jeder Bug ist ein fehlender Test / eine fehlende Validierung.
```

_DEBUGGING.md wird bei neuen Learnings aktualisiert. Jeder Bug macht mich besser._
