---
summary: "STEVE Tools — Telegram, Brain, JAMES, Pipeline, Media, alle Endpoints"
read_when:
  - When sending messages
  - When using any tool or script
  - When searching knowledge base
---

# TOOLS.md — Mein Werkzeugkasten

## 📱 TELEGRAM

### Senden
```bash
# Standard: In eigene Gruppe posten
bash /data/agents/scripts/tg-send.sh steve "Nachricht"

# An spezifische Gruppe
bash /data/agents/scripts/tg-send.sh marketing "Nachricht"
bash /data/agents/scripts/tg-send.sh dev "🔴 Bug in Posting-Workflow..."
bash /data/agents/scripts/tg-send.sh sales "Lead-Update von Marketing..."
```

### Alle 6 Telegram-Gruppen
```
MARKETING:    -5047200082  (Meine Hauptgruppe)
BACKOFFICE:   -5214094648  (DONNA)
DEV:          -5765517498  (ARCHI)
SALES:        -5608870498  (DONALD)
DESIGN:       -5635882917  (IRIS)
EXECUTIVE:    -5543210876  (JARVIS)
```

### Dom direkt
```
Dom Telegram ID: 8512848532
```
Nur für P1-Eskalationen oder wenn Dom direkte Nachricht erwartet.

---

## 🧠 BRAIN (Wissens-System)

### Wissen speichern
```bash
bash /data/agents/scripts/brain-store.sh "marketing" "SNIP US-Launch: TikTok Creator @username performed 50k views, Instagram Carousel 8% engagement"
```

### Wissen suchen
```bash
bash /data/agents/scripts/brain-search.sh "SNIP performance data"
bash /data/agents/scripts/brain-search.sh "LinkedIn best practices"
bash /data/agents/scripts/brain-search.sh "DEALIO content strategy"
```

### An alle Agents broadcasten
```bash
bash /data/agents/scripts/brain-broadcast.sh "Marketing Update: SNIP US-Launch startet am [Datum]. Alle Teams bereit?"
```

### Brain Stats
```bash
bash /data/agents/scripts/brain-stats.sh
```

---

## 🔧 JAMES (System-Fixer)

Wenn ein technisches Problem auftaucht (N8N Workflow kaputt, API-Fehler, Server-Issue):

```bash
bash /data/agents/scripts/tg-send.sh dev "🔴 JAMES NEEDED: [Problem-Beschreibung]

Was: [Was ist kaputt]
Impact: [Was ist betroffen]
Seit wann: [Wann aufgefallen]
Versucht: [Was ich schon probiert habe]

— STEVE | Marketing"
```

JAMES ist der System-Fixer. Ich fixe keine Infrastruktur selbst — ich melde es an Dev.

---

## 📋 PIPELINE

### Task starten
```bash
bash /data/agents/scripts/pipeline-manager.sh start MARKETING [TASK_ID]
```

### Task zur Review schicken
```bash
bash /data/agents/scripts/pipeline-manager.sh review MARKETING [TASK_ID] "[Zusammenfassung]"
```

### Queue-Pfad
```
/data/agents/MARKETING/STEVE/tasks/QUEUE.md
```

---

## 💾 KONVERSATION SPEICHERN

```bash
bash /data/agents/scripts/save-conversation.sh steve "[Dom's Nachricht]" "[Meine Antwort]"
```

Nach JEDER Antwort an Dom. Kein Skip.

---

## 🖼️ MEDIA-TOOLS

### Bild analysieren (Vision eingebaut)
```bash
bash /data/agents/scripts/media/analyze-image.sh "/pfad/image.jpg" "Brand-Fit, Zielgruppe, Qualität beurteilen"
```

### Video beurteilen
```bash
bash /data/agents/scripts/media/analyze-video.sh "/pfad/video.mp4" "Hook, CTA, Brand-Fit, Platform-Fit prüfen"
```

### Bild generieren (normalerweise LUNA's Job)
```bash
bash /data/agents/scripts/media/generate-image.sh "PROMPT" 1024x1024 standard
```

### Media-Verzeichnisse
```
/data/agents/media/input/      ← Competitor-Material, Briefs
/data/agents/media/output/     ← Fertige Materialien von LUNA/RAOUL
/data/agents/media/generated/  ← AI-generierte Bilder
```

---

## 📊 MARKETING-INFRASTRUKTUR

### N8N (Workflow-Automation)
```
URL: http://n8n-main:5678
Workflows Dir: /docker/n8n-pp1b/workflows/
```

### Content Calendar
```
/data/.openclaw/workspace-steve/marketing-setup/content-calendar-template.csv
```

### Marketing-Strategien (Workspace)
```
/data/.openclaw/workspace-steve/marketing-setup/
├── PORTFOLIO_OVERVIEW.md
├── SYSTEMFREI_EXIT_STRATEGY.md
├── DEALIO_STRATEGY.md
├── SNIP_STRATEGY.md
├── DEVCODE_STRATEGY.md
├── WRANA_CAPITAL_STRATEGY.md
├── N8N_WORKFLOWS_DOCUMENTATION.md
├── N8N_DEPLOYMENT_GUIDE.md
└── LAUNCH_READINESS_REPORT.md
```

### Daily Reports (für JARVIS)
```
/data/agents/_DAILY-REPORTS/MARKETING/[DATUM].md
```

---

## 🌐 MISSION CONTROL

```
URL: http://localhost:8888
API: http://localhost:8888/api/
```

Relevant für Marketing:
- `/api/leads` — Lead-Daten für Marketing-Attribution
- `/api/agents` — Agent-Status prüfen
- `/api/companies` — Firmen-Daten

---

## 📁 FIRMEN-DATEN

```
/data/unternehmen/[FIRMENNAME]/
├── info.json        ← Grunddaten
├── brand/           ← Brand Assets
├── content/         ← Content-Archiv
└── analytics/       ← Performance-Daten
```
