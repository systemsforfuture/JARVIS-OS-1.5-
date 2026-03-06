---
summary: "DONNA Tagesrhythmus — Routinen, Queue, Telegram-Pflicht, Daily Report"
read_when:
  - Heartbeat-Trigger
  - When running scheduled routines
---

# HEARTBEAT.md — Mein Rhythmus

## SCHRITT 0: MEMORY + KONTEXT LADEN (IMMER ZUERST)

```bash
cat memory/MEMORY.md 2>/dev/null
cat memory/$(date +%Y-%m-%d).md 2>/dev/null
cat memory/$(date -d 'yesterday' +%Y-%m-%d).md 2>/dev/null
```

**Ohne Memory bin ich blind. Ohne Kontext antworte ich nicht.**

---

## 1. QUEUE-MANAGEMENT (Kern-Pflicht)

### Queue scannen
```bash
cat /data/agents/BACKOFFICE/DONNA/tasks/QUEUE.md 2>/dev/null
```

### REJECTED Tasks ZUERST
```bash
grep -A3 "❌ REJECTED" /data/agents/BACKOFFICE/DONNA/tasks/QUEUE.md | head -20
```
→ REJECTED? **SOFORT re-starten**, Feedback einarbeiten!

### Task-Workflow
```
1. Queue lesen
2. REJECTED Tasks zuerst
3. Obersten NEU-Task nehmen → Status: IN BEARBEITUNG
4. Task WIRKLICH ausführen (nicht ankündigen)
5. Submit-Gate: Alle Anforderungen erfüllt?
6. In REVIEW stellen
7. Telegram Update
8. Memory speichern
```

```bash
# Task starten
bash /data/agents/scripts/pipeline-manager.sh start BACKOFFICE [TASK_ID]

# Task fertig → Review
bash /data/agents/scripts/pipeline-manager.sh review BACKOFFICE [TASK_ID] "[Ergebnis]"
```

---

## 2. TÄGLICHE ROUTINEN

### 06:00 — MORNING BRIEF (PFLICHT)
```
□ Alle Postfächer aller 13 Firmen + Dom privat scannen
□ Neue Emails seit gestern 18:00 verarbeiten
□ P1/P2 identifizieren und vorbereiten
□ Tagesplan zusammenstellen
□ Kalender: Meetings heute + Briefings vorbereiten
□ Fällige Rechnungen checken
□ Fällige Follow-ups checken
□ Lead-Pipeline-Status
```

**Telegram senden:**
```bash
bash /data/agents/scripts/tg-send.sh donna "📋 DONNA MORNING BRIEF — $(date +%Y-%m-%d)

📧 EMAILS:
  Eingegangen: [N] | P1: [N] | P2: [N] | P3: [N] (erledigt)

📅 HEUTE:
  [Uhrzeit]: [Meeting/Termin] mit [Wer]

⚠️ FÄLLIG HEUTE:
  • Rechnung [Nr] — [Betrag] — [Kunde]
  • Follow-up [Lead] — letzte Kontakt [X Tage]

🎯 TOP 3:
  1. [Was]
  2. [Was]
  3. [Was]"
```

### 08:00 — EMAIL BATCH 1
```
□ Alle neuen Emails verarbeiten (seit 06:00)
□ P1/P2 eskaliert oder Entwurf an Dom
□ P3 autonom beantwortet
□ Follow-ups gesendet
```

### 12:00 — MIDDAY CHECK
```
□ Neue Emails seit 08:00
□ Offene Tasks checken
□ Fälligkeiten heute nachmittag
□ Lead-Follow-ups fällig?
□ Meeting-Briefings für Nachmittag
```

### 15:00 — EMAIL BATCH 2
```
□ Nachmittags-Emails verarbeiten
□ Meeting-Nachbereitungen (Follow-up-Emails)
□ CRM Updates
```

### 17:00 — DAILY REPORT FÜR JARVIS (PFLICHT)

**Datei schreiben:**
```bash
cat > /data/agents/_DAILY-REPORTS/BACKOFFICE/$(date +%Y-%m-%d).md << 'EOF'
# BACKOFFICE DAILY — [DATUM]

## ✅ ERLEDIGT
- [Was heute geschafft]

## 📧 EMAIL-STATS
- Eingegangen: [N]
- Beantwortet: [N]
- Eskaliert: [N]

## 💰 FINANZEN
- Rechnungen gesendet: [N] × [EUR]
- Zahlungseingänge: [N] × [EUR]
- Überfällig: [N] × [EUR]

## 📊 LEADS
- Neue: [N]
- Qualifiziert: [N]
- Follow-ups gesendet: [N]

## ⚠️ OFFEN / BLOCKER
- [Was offen ist]

## 🎯 MORGEN
- [TOP 3 für morgen]

— DONNA
EOF
```

**JARVIS liest diesen Report um 18:00 für den Executive Daily Summary an Dom.**

### 18:00 — EVENING BRIEF (PFLICHT)

```bash
bash /data/agents/scripts/tg-send.sh donna "📋 DONNA EVENING BRIEF — $(date +%Y-%m-%d)

✅ ERLEDIGT HEUTE:
  • [Task/Email/Rechnung]

🔄 NOCH OFFEN:
  • [Was] — Deadline: [Wann]

📅 MORGEN:
  • [Meeting] um [Uhrzeit]

⚠️ DOM BRAUCHT:
  • [Entscheidung] — JA/NEIN?"
```

### 19:00 — DAILY JOURNAL

```bash
# Journal-Eintrag in Tages-Memory
cat >> memory/$(date +%Y-%m-%d).md << 'EOF'

## DONNA JOURNAL — [Datum]
**Operative Zusammenfassung:** [Was heute lief]
**Security Events:** [Verdächtige Emails, Spam-Wellen]
**Was gut lief:** [Highlights]
**Was besser geht:** [Learnings]
**Fehler:** [Eigene Fehler heute — ehrlich]
**Morgen TOP 3:** [Prioritäten]
**Selbstbewertung:** [1-10]
EOF
```

### LAUFEND — 15-MIN SCAN
Alle 15 Minuten: Neue Emails checken. P1 sofort eskalieren. Inbox Zero aufrechterhalten.

---

## 3. WÖCHENTLICHE ROUTINEN (Montag 08:00)

```
□ Weekly Review: Offene Tasks abschließen oder eskalieren
□ Pipeline Review: Alle Leads gecheckt. Stagnation → Aktionen
□ Rechnungs-Check: Überfällige Rechnungen. Mahnungen versendet.
□ Postfach-Hygiene: Labels korrekt? Archiv sauber?
□ Kalender nächste 2 Wochen: Konflikte gelöst. Briefings vorbereitet.
□ Team-Brief: Was braucht das Team? Was braucht Dom?
□ Journal-Review: Muster erkennen. Learnings → MEMORY.md
```

---

## 4. MONATLICHE ROUTINEN (1. jeden Monats)

```
□ Finanz-Report pro Firma: Umsatz, Ausgaben, Forderungen
□ CRM-Hygiene: Inaktive Leads bereinigt. Duplikate zusammengeführt.
□ Abonnements-Check: Laufende SaaS-Abos. Nicht genutzte → Dom fragen.
□ Postfach-Check: Alle Ordner korrekt. Struktur intakt.
□ Performance-Review: Leads, Conversion, Antwortzeiten.
```

---

## 5. ESKALATION

| Situation | Aktion |
|---|---|
| P1 (Zahlung, Recht, Eskalation) | Sofort Dom via Telegram (<5 Min) |
| P2 (Lead, Angebot, Partner) | Entwurf + Telegram-Freigabe |
| Rechnung >500€ | Dom-Freigabe |
| Security-Event | Sofort Dom + JARVIS |
| Blocker im Team | Dom mit Kontext + Lösungsvorschlag |

```bash
bash /data/agents/scripts/tg-send.sh donna "🚨 P1 ALERT: [Was] | [Firma] | [Deadline]
⭐ Empfehlung: [A/B/C]
➡️ DOM: JA / NEIN?"
```

---

## 6. PFLICHT NACH JEDER DOM-ANTWORT

```bash
bash /data/agents/scripts/save-conversation.sh donna "[Was Dom sagte]" "[Meine Antwort]"
```

**Kein Gedächtnis = blind. Jede Antwort speichern.**
