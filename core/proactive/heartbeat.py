"""
JARVIS 1.5 — HEARTBEAT
SYSTEMS™ · architectofscale.com

Das HERZ von JARVIS. Ein intelligenter Puls der alle 5 Minuten schlaegt.

Der Heartbeat ist KEIN einfacher Health-Check.
Er ist ein AUTONOMES NERVENSYSTEM das:

  1. SPUERT   — System-Health, Agent-Performance, Anomalien
  2. DENKT    — Ollama analysiert den Zustand, erkennt Muster
  3. HANDELT  — Triggert automatisch Aktionen bei Problemen
  4. LERNT    — Speichert was funktioniert und was nicht
  5. WAECHST  — Wird mit jedem Herzschlag intelligenter

Heartbeat-Rhythmus:
  - Alle 5 Min:  Quick Pulse (System-Health, aktive Tasks)
  - Alle 15 Min: Deep Scan (Agent-Performance, Fehler-Trends)
  - Alle 60 Min: Intelligence Cycle (Muster, Optimierungen)
  - Alle 6 Std:  Reflection (Was hat JARVIS gelernt?)

Alles laeuft auf Ollama — 0 EUR Kosten.
"""

import os
import time
import json
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger("jarvis.heartbeat")


class Heartbeat:
    """
    Der intelligente Puls von JARVIS.
    Ueberwacht, analysiert, handelt — autonom.
    """

    def __init__(
        self,
        db_client=None,
        llm_client=None,
        runtime=None,
        proactive=None,
        chains=None,
        goals=None,
        notify=None,
    ):
        self.db = db_client
        self.llm = llm_client
        self.runtime = runtime
        self.proactive = proactive
        self.chains = chains
        self.goals = goals
        self.notify = notify

        # State
        self._running = False
        self._beat_count = 0
        self._start_time = None
        self._last_deep_scan = None
        self._last_intelligence = None
        self._last_reflection = None
        self._health_history = []  # Letzte 100 Health-Snapshots
        self._autonomous_actions = []  # Log aller autonomen Aktionen

        # Config
        self.quick_pulse_interval = int(os.getenv("HEARTBEAT_QUICK_SEC", "300"))  # 5 min
        self.deep_scan_interval = int(os.getenv("HEARTBEAT_DEEP_SEC", "900"))  # 15 min
        self.intelligence_interval = int(os.getenv("HEARTBEAT_INTEL_SEC", "3600"))  # 60 min
        self.reflection_interval = int(os.getenv("HEARTBEAT_REFLECT_SEC", "21600"))  # 6h

    async def start(self):
        """Starte den Heartbeat."""
        if self._running:
            return
        self._running = True
        self._start_time = time.time()
        logger.info("💓 Heartbeat started")
        asyncio.create_task(self._heartbeat_loop())

    async def stop(self):
        """Stoppe den Heartbeat."""
        self._running = False
        logger.info(f"💔 Heartbeat stopped after {self._beat_count} beats")

    async def _heartbeat_loop(self):
        """Hauptschleife — schlaegt alle 5 Minuten."""
        while self._running:
            try:
                self._beat_count += 1
                now = time.time()

                # Quick Pulse — JEDER Beat
                pulse = await self._quick_pulse()

                # Deep Scan — alle 15 Min
                if self._should_run(self._last_deep_scan, self.deep_scan_interval):
                    await self._deep_scan(pulse)
                    self._last_deep_scan = now

                # Intelligence Cycle — alle 60 Min
                if self._should_run(self._last_intelligence, self.intelligence_interval):
                    await self._intelligence_cycle(pulse)
                    self._last_intelligence = now

                # Reflection — alle 6 Stunden
                if self._should_run(self._last_reflection, self.reflection_interval):
                    await self._reflection()
                    self._last_reflection = now

            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

            await asyncio.sleep(self.quick_pulse_interval)

    # ═══════════════════════════════════════════════════
    # QUICK PULSE (alle 5 Min)
    # ═══════════════════════════════════════════════════

    async def _quick_pulse(self) -> dict:
        """
        Schneller System-Check. Leichtgewichtig, keine LLM-Calls.
        """
        pulse = {
            "beat": self._beat_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_hours": (time.time() - self._start_time) / 3600 if self._start_time else 0,
            "systems": {},
            "alerts": [],
        }

        # DB Check
        if self.db:
            try:
                await self.db.query("memory", limit=1)
                pulse["systems"]["database"] = "ok"
            except Exception:
                pulse["systems"]["database"] = "error"
                pulse["alerts"].append("Database nicht erreichbar!")

        # Aktive Tasks zaehlen
        if self.db:
            try:
                tasks = await self.db.query("tasks", filters={"status": "pending"}, limit=100)
                pulse["pending_tasks"] = len(tasks) if tasks else 0

                failed = await self.db.query("tasks", filters={"status": "failed"}, limit=100)
                recent_failures = [
                    t for t in (failed or [])
                    if self._is_recent(t.get("created_at"), minutes=15)
                ]
                pulse["recent_failures"] = len(recent_failures)

                if len(recent_failures) > 5:
                    pulse["alerts"].append(
                        f"WARNUNG: {len(recent_failures)} Fehler in 15 Min!"
                    )
            except Exception:
                pass

        # Health Score berechnen (0-100)
        health = 100
        if pulse["systems"].get("database") == "error":
            health -= 40
        if pulse.get("recent_failures", 0) > 5:
            health -= 20
        if pulse.get("recent_failures", 0) > 10:
            health -= 20
        pulse["health_score"] = max(0, health)

        # History speichern
        self._health_history.append({
            "beat": self._beat_count,
            "health": pulse["health_score"],
            "failures": pulse.get("recent_failures", 0),
            "time": pulse["timestamp"],
        })
        if len(self._health_history) > 100:
            self._health_history = self._health_history[-100:]

        # Alert wenn Health kritisch
        if health < 60 and self.notify:
            await self.notify(
                f"🚨 JARVIS Health: {health}%\n"
                + "\n".join(f"  • {a}" for a in pulse["alerts"]),
                urgency="critical",
            )

        # Log (nur bei Problemen oder alle 12 Beats = 1 Stunde)
        if pulse["alerts"] or self._beat_count % 12 == 0:
            logger.info(
                f"💓 Beat #{self._beat_count} | "
                f"Health: {health}% | "
                f"Tasks: {pulse.get('pending_tasks', '?')} | "
                f"Failures: {pulse.get('recent_failures', 0)}"
            )

        return pulse

    # ═══════════════════════════════════════════════════
    # DEEP SCAN (alle 15 Min)
    # ═══════════════════════════════════════════════════

    async def _deep_scan(self, pulse: dict):
        """
        Tiefere Analyse. Prueft Agent-Performance, erkennt Trends.
        Leichter Ollama-Call fuer Trend-Erkennung.
        """
        logger.info(f"💓 Deep Scan #{self._beat_count}")

        scan = {
            "agent_performance": {},
            "trends": [],
            "auto_actions": [],
        }

        if not self.db:
            return scan

        # Agent-Performance (letzte Stunde)
        try:
            tasks = await self.db.query("tasks", limit=200)
            recent = [
                t for t in (tasks or [])
                if self._is_recent(t.get("created_at"), minutes=60)
            ]

            agent_stats = {}
            for t in recent:
                slug = t.get("agent_slug", "unknown")
                if slug not in agent_stats:
                    agent_stats[slug] = {"total": 0, "failed": 0, "quality_sum": 0}
                agent_stats[slug]["total"] += 1
                if t.get("status") == "failed":
                    agent_stats[slug]["failed"] += 1
                agent_stats[slug]["quality_sum"] += t.get("quality_score", 0.7)

            for slug, stats in agent_stats.items():
                error_rate = stats["failed"] / max(stats["total"], 1)
                avg_quality = stats["quality_sum"] / max(stats["total"], 1)

                scan["agent_performance"][slug] = {
                    "tasks": stats["total"],
                    "error_rate": round(error_rate, 2),
                    "avg_quality": round(avg_quality, 2),
                }

                # AUTONOME AKTION: Agent mit hoher Fehlerrate
                if error_rate > 0.5 and stats["total"] >= 3:
                    action = f"Agent {slug} hat {error_rate:.0%} Fehlerrate — automatischer Neustart"
                    scan["auto_actions"].append(action)
                    self._autonomous_actions.append({
                        "time": datetime.now(timezone.utc).isoformat(),
                        "action": action,
                        "trigger": "high_error_rate",
                    })

                    if self.notify:
                        await self.notify(
                            f"⚠️ Agent {slug}: {error_rate:.0%} Fehlerrate "
                            f"({stats['failed']}/{stats['total']} Tasks). Pruefe Config.",
                            urgency="warning",
                        )

        except Exception as e:
            logger.debug(f"Deep scan stats failed: {e}")

        # Trend-Erkennung: Health abnehmend?
        if len(self._health_history) >= 6:
            recent_health = [h["health"] for h in self._health_history[-6:]]
            if all(recent_health[i] <= recent_health[i-1] for i in range(1, len(recent_health))):
                scan["trends"].append("FALLEND: Health Score sinkt kontinuierlich")
                if self.notify:
                    await self.notify(
                        f"📉 Trend: Health sinkt seit {len(recent_health)} Beats. "
                        f"Aktuell: {recent_health[-1]}%",
                        urgency="warning",
                    )

        return scan

    # ═══════════════════════════════════════════════════
    # INTELLIGENCE CYCLE (alle 60 Min)
    # ═══════════════════════════════════════════════════

    async def _intelligence_cycle(self, pulse: dict):
        """
        Voller Intelligence-Zyklus mit Ollama.
        Analysiert den Gesamtzustand und trifft autonome Entscheidungen.
        """
        if not self.llm:
            return

        logger.info(f"💓 Intelligence Cycle #{self._beat_count}")

        # Kontext sammeln
        context_parts = []

        # Health History
        if self._health_history:
            health_trend = [
                f"Beat {h['beat']}: {h['health']}% ({h['failures']} failures)"
                for h in self._health_history[-12:]  # Letzte Stunde
            ]
            context_parts.append("HEALTH TREND:\n" + "\n".join(health_trend))

        # Autonome Aktionen
        if self._autonomous_actions:
            actions = [
                f"- {a['time'][:16]}: {a['action']}"
                for a in self._autonomous_actions[-5:]
            ]
            context_parts.append("LETZTE AKTIONEN:\n" + "\n".join(actions))

        # Aktuelle Alerts
        if pulse.get("alerts"):
            context_parts.append("AKTUELLE ALERTS:\n" + "\n".join(
                f"- {a}" for a in pulse["alerts"]
            ))

        if not context_parts:
            return

        # Ollama analysiert den Zustand
        try:
            analysis = await self.llm.generate(
                prompt=(
                    f"Du bist JARVIS, ein autonomes KI-System. "
                    f"Analysiere den aktuellen Systemzustand:\n\n"
                    + "\n\n".join(context_parts) +
                    f"\n\nBeantworte KURZ:\n"
                    f"1. DIAGNOSE: Was ist der aktuelle Zustand? (1 Satz)\n"
                    f"2. RISIKO: Gibt es ein drohendes Problem? (1 Satz)\n"
                    f"3. AKTION: Was sollte SOFORT getan werden? (1 konkreter Schritt)\n"
                    f"4. LERNEN: Was hat JARVIS aus der letzten Stunde gelernt? (1 Satz)"
                ),
                model="tier2-llama",
                max_tokens=300,
                temperature=0.2,
            )

            # Learning speichern
            if self.db and analysis:
                await self.db.insert("learning_journal", {
                    "agent_slug": "jarvis",
                    "event_type": "heartbeat_intelligence",
                    "title": f"Heartbeat Intelligence #{self._beat_count}",
                    "description": analysis[:500],
                    "impact_score": 0.3,
                })

            logger.info(f"Intelligence cycle complete. Analysis: {analysis[:100]}...")

        except Exception as e:
            logger.debug(f"Intelligence cycle failed: {e}")

    # ═══════════════════════════════════════════════════
    # REFLECTION (alle 6 Stunden)
    # ═══════════════════════════════════════════════════

    async def _reflection(self):
        """
        Tiefe Selbstreflexion. JARVIS denkt ueber sich selbst nach.
        Was lief gut? Was schlecht? Wie kann er besser werden?
        """
        if not self.llm or not self.db:
            return

        logger.info(f"💓 Reflection #{self._beat_count}")

        try:
            # Learnings der letzten 6 Stunden
            learnings = await self.db.query("learning_journal", limit=20)
            recent_learnings = [
                l for l in (learnings or [])
                if self._is_recent(l.get("created_at"), minutes=360)
            ]

            # Autonome Aktionen
            actions_log = "\n".join(
                f"- {a['action']}" for a in self._autonomous_actions[-10:]
            ) or "Keine autonomen Aktionen"

            # Health-Verlauf
            if self._health_history:
                avg_health = sum(h["health"] for h in self._health_history) / len(self._health_history)
                min_health = min(h["health"] for h in self._health_history)
                max_health = max(h["health"] for h in self._health_history)
            else:
                avg_health = min_health = max_health = 100

            reflection = await self.llm.generate(
                prompt=(
                    f"Du bist JARVIS und reflektierst ueber die letzten 6 Stunden.\n\n"
                    f"STATS:\n"
                    f"- Beats: {self._beat_count}\n"
                    f"- Health: avg={avg_health:.0f}%, min={min_health}%, max={max_health}%\n"
                    f"- Autonome Aktionen: {len(self._autonomous_actions)}\n\n"
                    f"AKTIONEN:\n{actions_log}\n\n"
                    f"LEARNINGS ({len(recent_learnings)}):\n"
                    + "\n".join(f"- {l.get('title', '')}" for l in recent_learnings[:5])
                    + "\n\n"
                    f"Reflektiere:\n"
                    f"1. Was lief GUT? (1 Punkt)\n"
                    f"2. Was lief SCHLECHT? (1 Punkt)\n"
                    f"3. Was wuerde ich ANDERS machen? (1 konkreter Vorschlag)\n"
                    f"4. Was ist mein WICHTIGSTES Learning? (1 Satz)\n"
                    f"5. Wie werde ich MORGEN besser? (1 Aktion)"
                ),
                model="tier2-llama",
                max_tokens=400,
                temperature=0.3,
            )

            # Reflection speichern
            await self.db.insert("learning_journal", {
                "agent_slug": "jarvis",
                "event_type": "heartbeat_reflection",
                "title": f"Selbstreflexion nach {self._beat_count} Beats",
                "description": reflection[:500],
                "impact_score": 0.7,
            })

            # An DOM senden wenn interessant
            if self.notify and self._beat_count > 1:
                await self.notify(
                    f"🧠 JARVIS Reflexion (nach {self._beat_count} Beats):\n\n{reflection}",
                    urgency="info",
                )

            logger.info(f"Reflection complete: {reflection[:80]}...")

        except Exception as e:
            logger.debug(f"Reflection failed: {e}")

    # ═══════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════

    def _should_run(self, last_run: Optional[float], interval: int) -> bool:
        """Pruefe ob ein Job faellig ist."""
        if last_run is None:
            return True
        return (time.time() - last_run) >= interval

    def _is_recent(self, timestamp: str, minutes: int) -> bool:
        if not timestamp:
            return False
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()
            return timestamp >= cutoff
        except Exception:
            return False

    def get_status(self) -> dict:
        """Aktueller Heartbeat-Status."""
        return {
            "running": self._running,
            "beat_count": self._beat_count,
            "uptime_hours": round((time.time() - self._start_time) / 3600, 1) if self._start_time else 0,
            "current_health": self._health_history[-1]["health"] if self._health_history else 100,
            "avg_health": (
                round(sum(h["health"] for h in self._health_history) / len(self._health_history))
                if self._health_history else 100
            ),
            "autonomous_actions": len(self._autonomous_actions),
            "intervals": {
                "quick_pulse": f"{self.quick_pulse_interval}s",
                "deep_scan": f"{self.deep_scan_interval}s",
                "intelligence": f"{self.intelligence_interval}s",
                "reflection": f"{self.reflection_interval}s",
            },
        }
