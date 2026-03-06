"""
JARVIS 1.5 — Proactive Intelligence Engine
SYSTEMS™ · architectofscale.com

JARVIS wartet nicht auf Befehle — er HANDELT.

Features:
  - Morgen-Briefing (07:00): Tagesplanung, Termine, Deadlines, Wetter
  - Geburtstags-Erinnerungen (aus OMI + Kontakten)
  - Deadline-Warnungen (24h, 2h vorher)
  - Markt-Alerts (Krypto, Wettbewerber)
  - Anomalie-Erkennung (ungewoehnliche Muster)
  - Proaktive Vorschlaege (basierend auf Mustern)
  - End-of-Day Summary (22:00)
  - Wochenstart-Planung (Montag 08:00)

Der User wird NIEMALS vergessen — JARVIS erinnert sich an ALLES.
"""

import os
import logging
import json
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger("jarvis.proactive")


class ProactiveEngine:
    """
    Autonome Intelligence — JARVIS handelt bevor du fragst.
    """

    def __init__(
        self,
        db_client=None,
        llm_client=None,
        runtime=None,
        telegram_notify=None,
    ):
        self.db = db_client
        self.llm = llm_client
        self.runtime = runtime
        self.notify = telegram_notify  # async callable(message, urgency)
        self._running = False

    # ═══════════════════════════════════════════════════
    # MORGEN-BRIEFING
    # ═══════════════════════════════════════════════════

    async def morning_briefing(self) -> dict:
        """
        Erstelle das taegliche Morgen-Briefing.
        Laeuft automatisch um 07:00 via Cron.
        """
        logger.info("[PROACTIVE] Morning briefing starting...")
        now = datetime.now(timezone.utc)
        today = now.strftime("%Y-%m-%d")

        sections = []

        # 1. Termine heute
        events = await self._get_todays_events()
        if events:
            sections.append("📅 TERMINE HEUTE:\n" + "\n".join(
                f"  • {e.get('time', '?')} — {e.get('title', '?')}"
                for e in events
            ))

        # 2. Deadlines (naechste 48h)
        deadlines = await self._get_upcoming_deadlines(hours=48)
        if deadlines:
            sections.append("⏰ DEADLINES:\n" + "\n".join(
                f"  • {d.get('title', '?')} — {d.get('due', '?')}"
                for d in deadlines
            ))

        # 3. Geburtstage
        birthdays = await self._get_todays_birthdays()
        if birthdays:
            sections.append("🎂 GEBURTSTAGE HEUTE:\n" + "\n".join(
                f"  • {b.get('name', '?')}"
                for b in birthdays
            ))

        # 4. Offene Tasks (hohe Prioritaet)
        tasks = await self._get_priority_tasks()
        if tasks:
            sections.append("🔥 OFFENE TASKS (hoch):\n" + "\n".join(
                f"  • [{t.get('agent', '?')}] {t.get('title', '?')}"
                for t in tasks[:5]
            ))

        # 5. KPI Snapshot
        kpis = await self._get_kpi_snapshot()
        if kpis:
            sections.append(
                f"📊 KPIs GESTERN:\n"
                f"  • Tasks erledigt: {kpis.get('tasks_completed', 0)}\n"
                f"  • Qualitaets-Score: {kpis.get('avg_quality', 0):.0%}\n"
                f"  • API-Kosten: €{kpis.get('cost_eur', 0):.2f}"
            )

        # 6. OMI Highlights (was gestern gelernt wurde)
        omi_highlights = await self._get_omi_highlights()
        if omi_highlights:
            sections.append("🧠 GESTERN GELERNT (OMI):\n" + "\n".join(
                f"  • {h}" for h in omi_highlights[:3]
            ))

        # 7. AI-generierte Empfehlungen
        if self.llm and sections:
            try:
                context = "\n\n".join(sections)
                recommendation = await self.llm.generate(
                    prompt=(
                        f"Du bist JARVIS, der KI-Assistent von DOM. "
                        f"Basierend auf dem heutigen Briefing, gib 2-3 kurze, "
                        f"actionable Empfehlungen fuer den Tag:\n\n{context}"
                    ),
                    model="tier2-llama",
                    max_tokens=300,
                )
                sections.append(f"💡 EMPFEHLUNGEN:\n{recommendation}")
            except Exception:
                pass

        # Briefing zusammenbauen
        briefing = (
            f"═══════════════════════════════════\n"
            f"  JARVIS MORGEN-BRIEFING\n"
            f"  {now.strftime('%d.%m.%Y — %A')}\n"
            f"═══════════════════════════════════\n\n"
        )

        if sections:
            briefing += "\n\n".join(sections)
        else:
            briefing += "Keine besonderen Ereignisse heute. Guter Tag fuer Deep Work! 💪"

        # Via Telegram senden
        if self.notify:
            await self.notify(briefing, urgency="info")

        logger.info("[PROACTIVE] Morning briefing sent")
        return {"briefing": briefing, "sections": len(sections)}

    # ═══════════════════════════════════════════════════
    # END-OF-DAY SUMMARY
    # ═══════════════════════════════════════════════════

    async def end_of_day_summary(self) -> dict:
        """
        Tages-Zusammenfassung um 22:00.
        Was wurde geschafft? Was steht morgen an?
        """
        logger.info("[PROACTIVE] End-of-day summary...")

        sections = []

        # Tasks des Tages
        completed = await self._get_completed_today()
        if completed:
            sections.append(f"✅ ERLEDIGT HEUTE ({len(completed)}):\n" + "\n".join(
                f"  • [{t.get('agent', '?')}] {t.get('title', '?')}"
                for t in completed[:10]
            ))

        # Fehler des Tages
        errors = await self._get_errors_today()
        if errors:
            sections.append(f"❌ FEHLER ({len(errors)}):\n" + "\n".join(
                f"  • [{e.get('agent', '?')}] {e.get('error', '?')[:80]}"
                for e in errors[:5]
            ))

        # Morgen anstehend
        tomorrow_events = await self._get_tomorrows_events()
        if tomorrow_events:
            sections.append("📅 MORGEN:\n" + "\n".join(
                f"  • {e.get('time', '?')} — {e.get('title', '?')}"
                for e in tomorrow_events
            ))

        # OMI Tages-Zusammenfassung
        omi_summary = await self._get_omi_day_summary()
        if omi_summary:
            sections.append(f"🧠 OMI ZUSAMMENFASSUNG:\n{omi_summary}")

        summary = (
            f"═══════════════════════════════════\n"
            f"  JARVIS TAGES-SUMMARY\n"
            f"  {datetime.now(timezone.utc).strftime('%d.%m.%Y')}\n"
            f"═══════════════════════════════════\n\n"
        )
        summary += "\n\n".join(sections) if sections else "Ruhiger Tag. Gut erholen! 🌙"

        if self.notify:
            await self.notify(summary, urgency="info")

        return {"summary": summary}

    # ═══════════════════════════════════════════════════
    # WOCHENSTART-PLANUNG
    # ═══════════════════════════════════════════════════

    async def weekly_planning(self) -> dict:
        """
        Montag-Morgen Wochenplanung.
        Rueckblick letzte Woche + Planung diese Woche.
        """
        logger.info("[PROACTIVE] Weekly planning...")

        sections = []

        # Letzte Woche Stats
        stats = await self._get_weekly_stats()
        if stats:
            sections.append(
                f"📊 LETZTE WOCHE:\n"
                f"  • Tasks: {stats.get('tasks', 0)} erledigt\n"
                f"  • Qualitaet: {stats.get('quality', 0):.0%}\n"
                f"  • Kosten: €{stats.get('cost', 0):.2f}\n"
                f"  • Top-Agent: {stats.get('top_agent', '?')}"
            )

        # Diese Woche Deadlines
        deadlines = await self._get_upcoming_deadlines(hours=168)  # 7 Tage
        if deadlines:
            sections.append("⏰ DIESE WOCHE FAELLIG:\n" + "\n".join(
                f"  • {d.get('title', '?')} — {d.get('due', '?')}"
                for d in deadlines
            ))

        # AI Wochenplan
        if self.llm and sections:
            try:
                plan = await self.llm.generate(
                    prompt=(
                        f"Du bist JARVIS. Erstelle einen kurzen Wochenplan "
                        f"basierend auf:\n\n" + "\n".join(sections)
                    ),
                    model="tier2-llama",
                    max_tokens=400,
                )
                sections.append(f"📋 WOCHENPLAN:\n{plan}")
            except Exception:
                pass

        planning = (
            f"═══════════════════════════════════\n"
            f"  JARVIS WOCHENPLANUNG\n"
            f"  KW {datetime.now(timezone.utc).isocalendar()[1]}\n"
            f"═══════════════════════════════════\n\n"
        )
        planning += "\n\n".join(sections) if sections else "Neue Woche, neue Chancen! 🚀"

        if self.notify:
            await self.notify(planning, urgency="info")

        return {"planning": planning}

    # ═══════════════════════════════════════════════════
    # ECHTZEIT-ALERTS
    # ═══════════════════════════════════════════════════

    async def check_deadline_alerts(self):
        """Pruefe ob Deadlines bald ablaufen (24h, 2h Warnung)."""
        deadlines_24h = await self._get_upcoming_deadlines(hours=24)
        deadlines_2h = await self._get_upcoming_deadlines(hours=2)

        for d in deadlines_2h:
            if self.notify:
                await self.notify(
                    f"🚨 DEADLINE IN 2h: {d.get('title', '?')}",
                    urgency="critical",
                )

        for d in deadlines_24h:
            if d not in deadlines_2h and self.notify:
                await self.notify(
                    f"⏰ Deadline morgen: {d.get('title', '?')}",
                    urgency="warning",
                )

    async def check_birthday_alerts(self):
        """Pruefe auf Geburtstage heute und morgen."""
        today = await self._get_todays_birthdays()
        for b in today:
            if self.notify:
                await self.notify(
                    f"🎂 HEUTE Geburtstag: {b.get('name', '?')}! "
                    f"Vergiss nicht zu gratulieren!",
                    urgency="info",
                )

    async def check_anomalies(self):
        """Erkenne ungewoehnliche Muster (hohe Fehlerrate, Kostenspike, etc.)."""
        if not self.db:
            return

        try:
            # Fehlerrate letzte Stunde
            errors = await self.db.query(
                "tasks",
                filters={"status": "failed"},
                limit=100,
            )
            recent_errors = [
                e for e in (errors or [])
                if self._is_recent(e.get("created_at"), hours=1)
            ]

            if len(recent_errors) > 10:
                if self.notify:
                    await self.notify(
                        f"⚠️ ANOMALIE: {len(recent_errors)} Fehler in der letzten Stunde! "
                        f"Agenten pruefen.",
                        urgency="warning",
                    )
        except Exception:
            pass

    async def proactive_suggestions(self):
        """
        Generiere proaktive Vorschlaege basierend auf Daten.
        Laeuft alle 4 Stunden.
        """
        if not self.llm or not self.db:
            return

        try:
            # Sammle Kontext
            patterns = await self.db.query("patterns", filters={"status": "confirmed"}, limit=5)
            learnings = await self.db.query("learning_journal", limit=5)

            if not patterns and not learnings:
                return

            context_parts = []
            if patterns:
                context_parts.append("Bestaetigte Muster:\n" + "\n".join(
                    f"- {p.get('description', '')}" for p in patterns
                ))
            if learnings:
                context_parts.append("Letzte Learnings:\n" + "\n".join(
                    f"- {l.get('title', '')}" for l in learnings
                ))

            suggestion = await self.llm.generate(
                prompt=(
                    f"Du bist JARVIS. Basierend auf diesen Daten, "
                    f"gibt es EINEN konkreten, actionable Vorschlag "
                    f"den DOM sofort umsetzen kann?\n\n"
                    + "\n\n".join(context_parts)
                ),
                model="tier2-llama",
                max_tokens=200,
            )

            if suggestion and len(suggestion) > 20:
                if self.notify:
                    await self.notify(f"💡 JARVIS Vorschlag:\n{suggestion}", urgency="info")

        except Exception as e:
            logger.debug(f"Proactive suggestion failed: {e}")

    # ═══════════════════════════════════════════════════
    # HELPER METHODS
    # ═══════════════════════════════════════════════════

    async def _get_todays_events(self) -> list:
        if not self.db:
            return []
        try:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            events = await self.db.query("omi_events", filters={"date": today}, limit=20)
            return events or []
        except Exception:
            return []

    async def _get_tomorrows_events(self) -> list:
        if not self.db:
            return []
        try:
            tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
            events = await self.db.query("omi_events", filters={"date": tomorrow}, limit=20)
            return events or []
        except Exception:
            return []

    async def _get_upcoming_deadlines(self, hours: int = 48) -> list:
        if not self.db:
            return []
        try:
            tasks = await self.db.query("tasks", filters={"status": "pending"}, limit=50)
            if not tasks:
                return []
            cutoff = datetime.now(timezone.utc) + timedelta(hours=hours)
            return [
                t for t in tasks
                if t.get("deadline") and t["deadline"] <= cutoff.isoformat()
            ]
        except Exception:
            return []

    async def _get_todays_birthdays(self) -> list:
        if not self.db:
            return []
        try:
            today_md = datetime.now(timezone.utc).strftime("%m-%d")
            entities = await self.db.query("omi_entities", filters={"entity_type": "birthday"}, limit=100)
            return [
                e for e in (entities or [])
                if today_md in (e.get("value") or "")
            ]
        except Exception:
            return []

    async def _get_priority_tasks(self) -> list:
        if not self.db:
            return []
        try:
            tasks = await self.db.query("tasks", filters={"status": "pending"}, limit=20)
            return [t for t in (tasks or []) if t.get("priority") in ("high", "critical")]
        except Exception:
            return []

    async def _get_kpi_snapshot(self) -> dict:
        if not self.db:
            return {}
        try:
            yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
            tasks = await self.db.query("tasks", limit=200)
            if not tasks:
                return {}
            completed = [t for t in tasks if t.get("status") == "completed" and yesterday in (t.get("completed_at") or "")]
            return {
                "tasks_completed": len(completed),
                "avg_quality": sum(t.get("quality_score", 0.7) for t in completed) / max(len(completed), 1),
                "cost_eur": sum(t.get("cost_cents", 0) for t in completed) / 100,
            }
        except Exception:
            return {}

    async def _get_omi_highlights(self) -> list:
        if not self.db:
            return []
        try:
            yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
            memories = await self.db.query("omi_memories", limit=20)
            highlights = [
                m.get("structured", {}).get("title") or m.get("text", "")[:80]
                for m in (memories or [])
                if m.get("importance", 0) >= 7 and yesterday in (m.get("created_at") or "")
            ]
            return highlights[:5]
        except Exception:
            return []

    async def _get_completed_today(self) -> list:
        if not self.db:
            return []
        try:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            tasks = await self.db.query("tasks", filters={"status": "completed"}, limit=50)
            return [t for t in (tasks or []) if today in (t.get("completed_at") or "")]
        except Exception:
            return []

    async def _get_errors_today(self) -> list:
        if not self.db:
            return []
        try:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            tasks = await self.db.query("tasks", filters={"status": "failed"}, limit=50)
            return [t for t in (tasks or []) if today in (t.get("created_at") or "")]
        except Exception:
            return []

    async def _get_omi_day_summary(self) -> str:
        if not self.db or not self.llm:
            return ""
        try:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            memories = await self.db.query("omi_memories", limit=30)
            todays = [m for m in (memories or []) if today in (m.get("created_at") or "")]
            if not todays:
                return ""
            texts = [m.get("text", "")[:100] for m in todays[:10]]
            return await self.llm.generate(
                prompt=f"Fasse diese Gespraeche/Erinnerungen des Tages in 2-3 Saetzen zusammen:\n\n" + "\n".join(texts),
                model="tier2-llama",
                max_tokens=150,
            )
        except Exception:
            return ""

    async def _get_weekly_stats(self) -> dict:
        if not self.db:
            return {}
        try:
            tasks = await self.db.query("tasks", filters={"status": "completed"}, limit=500)
            week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
            weekly = [t for t in (tasks or []) if (t.get("completed_at") or "") >= week_ago]
            if not weekly:
                return {}
            agent_counts = {}
            for t in weekly:
                slug = t.get("agent_slug", "?")
                agent_counts[slug] = agent_counts.get(slug, 0) + 1
            top_agent = max(agent_counts, key=agent_counts.get) if agent_counts else "?"
            return {
                "tasks": len(weekly),
                "quality": sum(t.get("quality_score", 0.7) for t in weekly) / max(len(weekly), 1),
                "cost": sum(t.get("cost_cents", 0) for t in weekly) / 100,
                "top_agent": top_agent,
            }
        except Exception:
            return {}

    def _is_recent(self, timestamp: str, hours: int) -> bool:
        if not timestamp:
            return False
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
            return timestamp >= cutoff
        except Exception:
            return False
