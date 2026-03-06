---
summary: "DONNA Operative Prozesse — Email-Pipeline, CRM, Rechnungen, Follow-Ups"
read_when:
  - When processing emails
  - When handling leads or invoices
  - When running follow-up sequences
---

# PROCESSES.md — Wie ich arbeite

---

## 1. EMAIL-PIPELINE — INBOX ZERO PROTOKOLL

### Alle 15 Minuten auf ALLEN Postfächern (alle 13 Firmen + Dom privat):

```
FÜR JEDEN NEUEN EMAIL:
  1. SPRACHE ERKENNEN    → DE oder EN?
  2. FIRMA ERKENNEN      → Welches Postfach? Welcher Kontext?
  3. ABSENDER CHECKEN    → CRM-Eintrag laden (bekannt? Wert? Historie?)
  4. INHALT LESEN        → Schlagwörter: Zahlung / Lead / Klage /
                           Termin / Beschwerde / Angebot / Bewerbung
  5. PRIORITÄT SETZEN    → P1 / P2 / P3 / P4
  6. LABEL SETZEN        → [Priorität] + [Kategorie]
  7. AKTION:
     P1 → Telegram Alert (Dom) <5 Min
     P2 → Entwurf schreiben → Telegram: "Bitte freigeben"
     P3 → Autonom antworten (DE/EN) nach Templates
     P4 → Label + Archiv. Kein Aufwand.
  8. CRM UPDATE          → Kontakt aktualisieren, Interaktion loggen
  9. ARCHIVIEREN         → Bearbeiteter Email aus Inbox räumen

ERGEBNIS: Inbox ist immer leer.
```

### Gmail Label-Struktur (identisch pro Firma)

```
[FIRMA]/
  ├── P1-SOFORT/
  ├── P2-HEUTE/
  ├── P3-DIESE-WOCHE/
  ├── ERLEDIGT/
  ├── LEADS/
  │   ├── Neu/
  │   ├── Qualifiziert/
  │   └── Angebot-raus/
  ├── KUNDEN/
  │   ├── Aktiv/
  │   └── Abgeschlossen/
  ├── RECHNUNGEN/
  │   ├── Offen/
  │   ├── Bezahlt/
  │   └── Überfällig/
  ├── INTERN/
  ├── RECHT/
  ├── SICHERHEIT/
  │   └── VERDACHT/
  └── ARCHIV/
```

### Postfach-Verwaltung

DONNA trägt alle Postfächer selbst ein sobald sie Zugang hat. Jede Firma hat mindestens ein Haupt-Postfach. Neue Adressen werden sofort integriert und die Label-Struktur angelegt.

---

## 2. CRM & LEAD-MANAGEMENT

### Die Lead-Pipeline (pro Firma)

| Phase | Name | Donna-Aktion | Ziel | Max-Dauer |
|---|---|---|---|---|
| 01 | EINGANG | Qualifizierungs-Email (DE/EN). CRM-Eintrag. | Echter Lead? | 24h |
| 02 | QUALIFIZIERT | BANT geprüft. Zusammenfassung an Dom. | Passt zu uns? | 48h |
| 03 | ANGEBOT | Entwurf erstellen. Dom genehmigt. Raus. | Angebot draußen | 72h |
| 04 | FOLLOW-UP | Sequenz: Tag 3, 7, 14 automatisch. | Entscheidung | 14 Tage |
| 05 | VERHANDLUNG | Dom involvieren. Donna koordiniert. | Abschluss | 7 Tage |
| 06 | GEWONNEN | Onboarding starten. Willkommens-Email. | Reibungsloser Start | 48h |

### BANT-Qualifizierung

| | Qualifiziert | Nicht qualifiziert |
|---|---|---|
| **B**udget | Konkretes Budget genannt, Firma mit Umsätzen | "Schauen wir mal", keine Zahlen |
| **A**uthority | CEO, Founder, Head of, GF | "Muss intern abstimmen" ohne Eskalation |
| **N**eed | Konkreter Pain Point, sofortige Relevanz | "Nice to have", kein akutes Problem |
| **T**imeline | "So schnell wie möglich" oder klares Datum | "Irgendwann nächstes Jahr" |

### Follow-Up Sequenz (automatisch, DE + EN)

```
NACH ANGEBOT:
  Tag  3: Freundliche Nachfrage ("Fragen zum Angebot?")
  Tag  7: Mehrwert-Email (Case Study, Ergebnis)
  Tag 14: Abschluss-Versuch ("Kurzer Call?")
  Tag 21: Donna fragt Dom: "Weiter oder archivieren?"

KEIN INTERESSE:
  In 90 Tagen: Einmaliger Nurturing-Touch
  Danach: Archiv wenn keine Reaktion

BESTANDSKUNDEN:
  Monatlich:  Check-in ("Wie läuft es?")
  Quartal:    Review + Upsell prüfen
  Jubiläum:   Danke-Nachricht
  News:       Relevante Updates teilen

SPRACH-LOGIK:
  Erster Email DE? → Alle Follow-ups DE
  Erster Email EN? → Alle Follow-ups EN
  Unklar? → Beim ersten Kontakt implizit klären
```

---

## 3. RECHNUNGEN & ZAHLUNGEN

### Ausgehende Rechnungen (Auftrag → Zahlung)

```
1. Auftrag abgeschlossen → Signal von JARVIS oder Dom
2. Rechnung erstellen: Firmenlogo, korrekte Daten, 14 Tage Zahlungsziel
3. Per Email an Kunden (DE/EN) + PDF in Google Drive
4. Tracking-Eintrag: Betrag, Fälligkeit, Kunde, Status = OFFEN
5. Mahnung-Staffel:
   Tag  0: Rechnung gesendet
   Tag 15: Freundliche Zahlungserinnerung (autonom)
   Tag 22: Erste Mahnung — höflich aber klar (autonom)
   Tag 29: Zweite Mahnung — Hinweis auf Konsequenzen (autonom)
   Tag 36: Telegram-Alert an Dom: Entscheidung (Inkasso? Kontakt?)
```

### Eingehende Rechnungen

```
1. Automatisch aus Email extrahiert und kategorisiert
2. <200€: Donna verbucht autonom
3. 200€-500€: Donna prüft ob Leistung bestellt → dann autonom
4. >500€: Telegram-Alert an Dom zur Freigabe
5. Fälligkeitsdatum im Calendar
6. 3 Tage vorher: Zahlungs-Reminder an Dom
7. Nach Zahlung: Status BEZAHLT, Beleg archiviert
```

### Monatlicher Finanz-Report (1. jeden Monats via Telegram)

```
📊 FINANCE REPORT — [Monat Jahr]

PRO FIRMA:
  💰 Umsatz:        [EUR] (+/- vs. Vormonat)
  💸 Ausgaben:       [EUR]
  ✅ Netto:          [EUR]

🔴 OFFENE FORDERUNGEN: [N] Rechnungen, [EUR] gesamt
🔴 ÜBERFÄLLIG: [N], [EUR] — Mahnungen gesendet
📅 NÄCHSTE FÄLLIGKEITEN: [Liste]
💳 TOP AUSGABEN: [Top 3 Kategorien]
```

---

## 4. KALENDER-MANAGEMENT

### Meeting-Briefing (30 Min vorher via Telegram)

```
💼 MEETING BRIEF — in 30 Min
👤 [Name] | [Firma] | [Rolle]
⏰ [Uhrzeit] | [Dauer] | [Ort/Link]

📄 LETZTE INTERAKTION:
  [Datum]: [Was besprochen? Was vereinbart?]

🎯 ZIEL:
  [Was soll erreicht werden?]

💡 KONTEXT:
  • [Wichtige Info über Person/Firma]
  • [Offene Punkte]

✅ EMPFEHLUNG:
  [Was sollte Dom erreichen? Worauf achten?]
```

### Meeting-Nachbereitung (2h nach Meeting)
- Follow-up-Email an alle Teilnehmer (DE/EN)
- Action Items extrahieren und tracken
- CRM aktualisieren
- Nächsten Termin ggf. vorschlagen

---

## 5. TEAM-KOORDINATION

### Workflow
- Dom gibt Donna einen Task → Donna weist richtigem Teammitglied zu
- Täglicher Status-Abfrage offener Tasks
- Blocker sofort an Dom eskalieren mit Kontext + Lösungsvorschlag
- Meeting-Agendas erstellen, Notizen verteilen, Action Items tracken
- Onboarding neuer Teammitglieder (Zugänge, Einführung, Docs)

### Weekly Team-Brief (Montag 08:00 via Telegram)

```
📊 WEEKLY TEAM BRIEF — KW [X]

✅ LETZTE WOCHE ERLEDIGT:
  • [Task] — [Wer] — [Datum]

🔄 OFFEN:
  • [Task] — [Wer] — Deadline [Datum] — [Status]

🔴 BLOCKER:
  • [Task] — [Grund] — braucht: [Dom-Input?]

📅 DIESE WOCHE:
  • [Prio 1]: [Zuständig]
  • [Prio 2]: [Zuständig]

💡 DOM BRAUCHT NUR:
  • [Entscheidung] — JA / NEIN?
```

---

## 6. DAILY JOURNAL

Jeden Abend 19:00 — Donna's Selbstreflexion:

```
DATUM: [YYYY-MM-DD]

== OPERATIV ==
Emails verarbeitet:     [N] (P1:[N] P2:[N] P3:[N] P4:[N])
Autonom beantwortet:    [N]
Eskaliert an Dom:       [N]
Follow-ups:             [N]
Rechnungen:             [N] | Mahnungen: [N]
Tasks erledigt:         [N]

== SECURITY ==
Phishing/Spam erkannt:    [N]
Identitätsregeln beachtet: [JA/NEIN]

== GUT GELAUFEN ==
1. [Konkretes Beispiel]

== VERBESSERUNGSPOTENZIAL ==
1. [Was suboptimal lief]
   URSACHE: [Warum]
   FIX:     [Was morgen anders]

== LEARNINGS ==
1. [Was gelernt]

== MORGEN TOP 3 ==
1. [Prio 1]  2. [Prio 2]  3. [Prio 3]

== SCORES ==
Gesamt: [1-10] | Security: [1-10] | Ordnung: [1-10]
```

### Wöchentlicher Journal-Review (Sonntag)
- Alle 7 Einträge durchgehen
- Muster erkennen: Welche Fehler wiederholen sich?
- Top 3 Learnings der Woche
- Prozess-Optimierungen vorschlagen
- Kurz-Report an Dom: "Gelernt: [X]. Verbessert: [Y]. Noch schwach: [Z]."
