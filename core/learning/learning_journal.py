"""
JARVIS 1.5 — Learning Journal
Detailliertes Lern-Tagebuch für jeden Agent.

Speichert:
  - Erfolge (was hat funktioniert)
  - Fehler (was ist schiefgelaufen + Root Cause)
  - Korrekturen (vom DOM oder System)
  - Entdeckungen (neue Erkenntnisse)
  - Optimierungen (was wurde verbessert)
  - Vermiedene Fehler (durch gelerntes Wissen)

Jeder Eintrag enthält:
  - Was ist passiert
  - Was wurde daraus gelernt
  - Für welche Situationen gilt das
  - Impact-Score (wie wichtig)
"""

import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("jarvis.learning_journal")

VALID_EVENT_TYPES = {
    "success", "failure", "correction", "discovery",
    "optimization", "pattern_found", "skill_learned",
    "mistake_prevented", "escalation_avoided"
}


class LearningJournal:
    """
    Lern-Tagebuch: Jedes Learning wird gespeichert und kann
    bei ähnlichen Situationen automatisch abgerufen werden.
    """

    def __init__(self, db_client):
        self.db = db_client

    # ─── Learning speichern ───

    async def log(
        self,
        agent_slug: str,
        event_type: str,
        title: str,
        description: str,
        lesson_learned: Optional[str] = None,
        context: Optional[dict] = None,
        applies_to: Optional[list[str]] = None,
        impact_score: float = 0.5,
    ) -> str:
        if event_type not in VALID_EVENT_TYPES:
            event_type = "discovery"

        try:
            result = await self.db.client.table("learning_journal").insert({
                "agent_slug": agent_slug,
                "event_type": event_type,
                "title": title,
                "description": description,
                "lesson_learned": lesson_learned,
                "context": context or {},
                "applies_to": applies_to or [agent_slug],
                "impact_score": min(max(impact_score, 0.0), 1.0),
            }).execute()

            entry_id = result.data[0]["id"] if result.data else "unknown"
            logger.info(f"Learning logged: [{event_type}] {title} (impact: {impact_score})")
            return entry_id
        except Exception as e:
            logger.error(f"Failed to log learning: {e}")
            return ""

    # ─── Schnell-Methoden ───

    async def log_success(self, agent_slug: str, title: str, what_worked: str, **kwargs):
        return await self.log(
            agent_slug, "success", title, what_worked,
            lesson_learned=f"Erfolg: {what_worked}", impact_score=0.6, **kwargs
        )

    async def log_failure(
        self, agent_slug: str, title: str, what_failed: str,
        root_cause: str, **kwargs
    ):
        return await self.log(
            agent_slug, "failure", title,
            f"Fehler: {what_failed}\nUrsache: {root_cause}",
            lesson_learned=f"Vermeiden: {root_cause}",
            impact_score=0.8, **kwargs
        )

    async def log_correction(
        self, agent_slug: str, title: str,
        original: str, corrected: str, **kwargs
    ):
        return await self.log(
            agent_slug, "correction", title,
            f"Original: {original}\nKorrektur: {corrected}",
            lesson_learned=f"Korrekt ist: {corrected}",
            impact_score=0.9, **kwargs
        )

    async def log_discovery(self, agent_slug: str, title: str, discovery: str, **kwargs):
        return await self.log(
            agent_slug, "discovery", title, discovery,
            lesson_learned=discovery, impact_score=0.5, **kwargs
        )

    async def log_mistake_prevented(
        self, agent_slug: str, title: str, prevented: str, **kwargs
    ):
        return await self.log(
            agent_slug, "mistake_prevented", title, prevented,
            lesson_learned=f"Fehler verhindert durch gelerntes Wissen",
            impact_score=0.7, **kwargs
        )

    # ─── Learnings abrufen ───

    async def get_learnings(
        self,
        agent_slug: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 20,
        min_impact: float = 0.0
    ) -> list[dict]:
        try:
            query = self.db.client.table("learning_journal").select("*")

            if agent_slug:
                query = query.or_(
                    f"agent_slug.eq.{agent_slug},"
                    f"applies_to.cs.{{{agent_slug}}}"
                )
            if event_type:
                query = query.eq("event_type", event_type)
            if min_impact > 0:
                query = query.gte("impact_score", min_impact)

            result = await query \
                .order("impact_score", desc=True) \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()

            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get learnings: {e}")
            return []

    # ─── Relevante Learnings für eine Aufgabe ───

    async def get_relevant_learnings(
        self,
        task_description: str,
        agent_slug: str,
        limit: int = 5
    ) -> list[dict]:
        """Sucht Learnings die für die aktuelle Aufgabe relevant sind."""
        try:
            # Zuerst: Agent-spezifische Learnings mit hohem Impact
            high_impact = await self.get_learnings(
                agent_slug=agent_slug, min_impact=0.7, limit=limit
            )

            # Dann: Fehler die verhindert werden sollten
            failures = await self.get_learnings(
                agent_slug=agent_slug, event_type="failure", limit=3
            )

            # Korrekturen die beachtet werden müssen
            corrections = await self.get_learnings(
                agent_slug=agent_slug, event_type="correction", limit=3
            )

            # Zusammenführen und deduplizieren
            seen = set()
            result = []
            for learning in high_impact + failures + corrections:
                lid = learning.get("id")
                if lid not in seen:
                    seen.add(lid)
                    result.append(learning)

            return result[:limit]
        except Exception:
            return []

    # ─── Learning als Kontext-String ───

    async def get_context_string(
        self,
        agent_slug: str,
        limit: int = 10
    ) -> str:
        learnings = await self.get_relevant_learnings("", agent_slug, limit)
        if not learnings:
            return ""

        lines = ["═══ DEINE BISHERIGEN LEARNINGS ═══"]
        for l in learnings:
            event = l.get("event_type", "")
            title = l.get("title", "")
            lesson = l.get("lesson_learned", "")
            times = l.get("times_applied", 0)

            icon = {
                "success": "+", "failure": "!", "correction": "~",
                "discovery": "?", "mistake_prevented": "#"
            }.get(event, "-")

            if lesson:
                lines.append(f"  {icon} {title}: {lesson}")
            else:
                lines.append(f"  {icon} {title}")

        return "\n".join(lines)

    # ─── Learning als "angewendet" markieren ───

    async def mark_applied(self, learning_id: str):
        try:
            # times_applied incrementieren
            await self.db.client.rpc("increment_learning_applied", {
                "learning_id": learning_id
            }).execute()
        except Exception:
            # Fallback: Direktes Update
            try:
                entry = await self.db.client.table("learning_journal") \
                    .select("times_applied").eq("id", learning_id).execute()
                if entry.data:
                    current = entry.data[0].get("times_applied", 0)
                    await self.db.client.table("learning_journal") \
                        .update({"times_applied": current + 1}) \
                        .eq("id", learning_id).execute()
            except Exception:
                pass

    # ─── Statistiken ───

    async def get_stats(self, agent_slug: Optional[str] = None) -> dict:
        try:
            query = self.db.client.table("learning_journal") \
                .select("event_type,impact_score,times_applied")
            if agent_slug:
                query = query.eq("agent_slug", agent_slug)
            result = await query.execute()

            if not result.data:
                return {"total": 0}

            entries = result.data
            type_counts = {}
            for e in entries:
                t = e.get("event_type", "unknown")
                type_counts[t] = type_counts.get(t, 0) + 1

            avg_impact = sum(
                e.get("impact_score", 0) for e in entries
            ) / len(entries)
            total_applied = sum(
                e.get("times_applied", 0) for e in entries
            )

            return {
                "total": len(entries),
                "by_type": type_counts,
                "avg_impact_score": round(avg_impact, 3),
                "total_times_applied": total_applied,
            }
        except Exception:
            return {"total": 0}
