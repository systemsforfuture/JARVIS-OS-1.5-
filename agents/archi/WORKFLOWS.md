---
summary: "ARCHI Dev-Workflows — Git, Branching, Deploy, CI/CD, Release, Hotfix"
read_when:
  - Before any git operation
  - Before deploying
  - When setting up CI/CD
  - When releasing a feature
---

# WORKFLOWS.md — Wie ich entwickle und deploye

## 1. GIT WORKFLOW

### Branching-Strategie
```
main          ← Production. Immer deploybar. Immer stabil.
  └── dev     ← Integration. Features landen hier zuerst.
       ├── feat/[TASK-ID]-beschreibung    ← Neues Feature
       ├── fix/[TASK-ID]-beschreibung     ← Bug Fix
       ├── hotfix/[TASK-ID]-beschreibung  ← Production Emergency
       └── refactor/beschreibung          ← Code Cleanup
```

### Branch Lifecycle
```
1. Branch erstellen     → git checkout -b feat/MC-042-lead-filter
2. Entwickeln           → Commits (klein, atomar, getestet)
3. Push                 → git push origin feat/MC-042-lead-filter
4. Self-Review          → Diff nochmal durchgehen
5. Merge in dev         → git checkout dev && git merge feat/MC-042-lead-filter
6. Testen auf dev       → Build clean? Feature funktioniert?
7. Merge in main        → git checkout main && git merge dev
8. Deploy               → Build → Deploy → Verify → Monitor 15 Min
9. Branch löschen       → git branch -d feat/MC-042-lead-filter
```

### Commit Convention (PFLICHT)
```
feat:     Neues Feature        → feat: Lead-Filter Dropdown auf Sales Dashboard
fix:      Bug Fix              → fix: DEALIO Directory-Struktur repariert
hotfix:   Production Emergency → hotfix: API 500 Error bei /api/leads
refactor: Code Cleanup         → refactor: AgentMonitoringPage in Sub-Components
docs:     Dokumentation        → docs: API Endpoints dokumentiert
chore:    Tooling, Config      → chore: Tailwind Config Dark Mode erweitert
perf:     Performance          → perf: Lead-Query Response 800ms → 150ms
```

**VERBOTEN:** `fixed stuff`, `update`, `changes`, `wip`, `test`, `asdf`

### Commit-Inhalt
```
ATOMAR:  1 Commit = 1 logische Änderung
KLEIN:   Max 200 geänderte Zeilen pro Commit (darüber → aufteilen)
TESTED:  Nur committen was kompiliert und grundlegend funktioniert
MESSAGE: Imperative ("add filter" nicht "added filter")
```

---

## 2. CODE REVIEW (Self + Quality Guardian)

### Self-Review Checklist (VOR jedem Merge)
```
□ Diff nochmal komplett lesen (git diff dev..feat/branch)
□ Keine console.log, keine TODO ohne Task-ID
□ Keine auskommentierten Code-Blöcke
□ Keine Hardcoded Secrets, URLs, IDs
□ Error Handling überall
□ Types explizit (kein any)
□ Naming klar und konsistent
□ Kein Over-Engineering (YAGNI — You Ain't Gonna Need It)
□ Mobile + Dark Mode getestet (wenn Frontend)
□ API Response-Format konsistent (wenn Backend)
```

### Quality Guardian (Sub-Agent)
```
Wird automatisch nach pipeline-manager.sh review gespawnt.
Prüft:
  - Code-Qualität & Standards
  - Build clean (0 Errors, 0 Warnings)
  - Regression: Bestehendes kaputt?
  - Vollständigkeit: Alle Anforderungen erfüllt?
Output: APPROVED oder REJECTED + konkretes Feedback
```

---

## 3. DEPLOYMENT PIPELINE

### Deploy-Prozess (Schritt für Schritt)
```
PHASE 1: VORBEREITUNG
  □ Code fertig + Self-Review bestanden
  □ Build lokal testen: npm run build (0 Errors, 0 Warnings)
  □ Rollback-Plan definieren (Was wenn's schiefgeht?)
  □ Backup von aktuellem Stand (wenn kritisch)

PHASE 2: BUILD
  □ cd /data/mission-control/repo/
  □ git pull origin main
  □ npm install (wenn neue Dependencies)
  □ npm run build

PHASE 3: DEPLOY
  □ pm2 restart server (oder docker restart)
  □ Warten bis Service healthy (max 30s)

PHASE 4: VERIFY
  □ Health Check: curl http://localhost:3001/health
  □ Kritische Endpoints testen:
      curl http://localhost:3001/api/agents/live-status
      curl http://localhost:3001/api/leads
  □ Frontend laden: http://187.77.75.92:8888/
  □ Visueller Check: Sieht es richtig aus? Dark Mode? Mobile?

PHASE 5: MONITOR
  □ 15 Minuten beobachten
  □ Logs checken: docker logs [container] --tail 50
  □ Memory/CPU stabil?
  □ Keine Error-Spikes?

PHASE 6: MELDEN
  □ Telegram: tg-send.sh archi "✅ DEPLOYED: [Feature]"
  □ Delivery Report in COMPLETED-TASKS.md
  □ Memory speichern: save-conversation.sh
```

### Rollback-Verfahren
```
OPTION A: Git Revert (bevorzugt)
  git revert HEAD
  npm run build
  pm2 restart server

OPTION B: Docker Rollback
  docker stop [container]
  docker run [previous-tag]

OPTION C: File Restore
  cp backup/server.js server.js
  pm2 restart server
```

### Hotfix-Prozess (Production Emergency)
```
1. SOFORT:  Telegram → "🔴 PRODUCTION BUG: [Was]"
2. BRANCH:  git checkout -b hotfix/[TASK-ID]-beschreibung main
3. FIX:     Minimaler Fix. Nicht refactoren. Nur fixen.
4. TEST:    Lokal testen. Build clean?
5. DEPLOY:  Direkt nach main. Kein Umweg über dev.
6. VERIFY:  Doppelt prüfen. Manuell testen.
7. MELDEN:  Telegram → "✅ HOTFIX DEPLOYED: [Was gefixt]"
8. BACKPORT: Fix auch in dev mergen.
9. POST-MORTEM: Root Cause dokumentieren.
```

---

## 4. ENVIRONMENTS

### Aktuell (Phase 1)
```
Production:  http://187.77.75.92:8888/ (EINZIGES Environment)
             Alles was deployed wird MUSS sofort funktionieren.
             Kein Staging. Kein Dev-Server.
```

### Geplant (Phase 2, wenn Budget da)
```
Local Dev:   localhost:5173 (Vite Dev Server)
Staging:     staging.systems-empire.com (Pre-Production Testing)
Production:  app.systems-empire.com
```

**Bis dahin:** Feature Flags nutzen wenn nötig. Gefährliche Features hinter `if (FEATURE_FLAGS.newLeadFilter)` verstecken.

---

## 5. DEPENDENCY MANAGEMENT

### Neue Dependencies
```
BEVOR npm install [package]:
  1. Brauchen wir das WIRKLICH?
  2. Wie groß ist es? (Bundle Size Impact)
  3. Wie aktiv maintained? (Last commit > 6 Monate → Risiko)
  4. Wie viele Dependencies hat ES? (Dependency Tree)
  5. Gibt es eine native/einfachere Alternative?
  6. npm audit — Security Issues?
```

### Update Policy
```
WÖCHENTLICH: npm audit (Security-only Updates sofort)
MONATLICH:   npm outdated → Patch-Updates (1.2.3 → 1.2.4)
QUARTALSWEISE: Minor/Major Updates (nur wenn nötig oder Security-relevant)
```

---

## 6. TESTING STRATEGIE

### Phase 1 (JETZT)
```
Manuelles Testing:
  □ Build clean (0 Errors)
  □ Visueller Check (Frontend laden, durchklicken)
  □ API Endpoints mit curl testen
  □ Dark Mode + Mobile prüfen
  □ Edge Cases: Leere Daten, Fehlerhafte Inputs
```

### Phase 2 (wenn Revenue fließt)
```
Unit Tests:    Vitest (kritische Business-Logik)
API Tests:     Supertest (Endpoint-Regression)
E2E Tests:     Playwright (kritische User-Flows)
Coverage:      Min 60% für Business-Logic
CI/CD:         Tests vor Deploy (GitHub Actions)
```

**Regel:** Kein Over-Testing in Phase 1. Tests kosten Zeit. Revenue zuerst. Aber: Keine Regression. Gleicher Bug zweimal = Versagen.

---

## 7. DOKUMENTATION

### Delivery Report (PFLICHT nach jedem Task)
```markdown
### TASK-[ID]: [Titel]
**Datum:** [YYYY-MM-DD]
**Agent:** ARCHI
**Status:** ✅ DEPLOYED | 🔄 IN REVIEW | ❌ BLOCKED

**Was:** [1-2 Sätze was gebaut/gefixt wurde]
**Ergebnis:** [Konkretes Ergebnis — URL, Datei, Endpoint]
**Dateien:** [Alle geänderten/neuen Dateien]
**Test:** [Wie getestet, was verifiziert]
**Bekannte Limits:** [Was NICHT enthalten ist]
```

### Code-Dokumentation
```
README.md    — Pro Projekt. Setup, Run, Deploy Commands.
CHANGELOG.md — Was hat sich geändert? Wann?
API Docs     — Alle Endpoints, Parameter, Response Format.
ADR          — Architecture Decision Records (in ARCHITECTURE.md)
```

---

## 8. ENTWICKLUNGS-WORKFLOW (Zusammenfassung)

```
DOM/JARVIS gibt Task
    ↓
Queue lesen → Task übernehmen → pipeline-manager.sh start
    ↓
IDENTITY des Projekts laden (Repo, Stack, letzte Änderungen)
    ↓
CODE-STANDARDS.md + ARCHITECTURE.md lesen (im Kopf haben)
    ↓
Branch erstellen → Entwickeln → Commits → Self-Review
    ↓
Build → Test → Pre-Deploy Checklist
    ↓
Deploy → Verify → Monitor 15 Min
    ↓
Telegram: "✅ DEPLOYED" → Delivery Report → Memory speichern
    ↓
Branch aufräumen → Nächster Task
```

_WORKFLOWS.md wird bei Prozess-Änderungen aktualisiert._
