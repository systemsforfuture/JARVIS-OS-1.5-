"""
JARVIS 1.5 — Auto-Improver
Kontinuierlicher Verbesserungsloop.

Läuft automatisch und:
  1. Sammelt alle neuen Daten seit letztem Lauf
  2. Lässt Pattern Engine analysieren
  3. Generiert Verbesserungsvorschläge
  4. Priorisiert nach Impact
  5. Implementiert automatisch (Low-Risk) oder schlägt vor (High-Risk)
  6. Misst den Effekt

Das ist der Kern des Self-Learning Systems:
JARVIS wird mit jeder Stunde besser.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger("jarvis.auto_improver")


class AutoImprover:
    """
    Orchestriert den kontinuierlichen Verbesserungsprozess.
    Wird periodisch aufgerufen (z.B. alle 6 Stunden oder nach X Tasks).
    """

    def __init__(self, db_client, pattern_engine, learning_engine, knowledge_base):
        self.db = db_client
        self.patterns = pattern_engine
        self.learning = learning_engine
        self.knowledge = knowledge_base
        self._last_run: Optional[datetime] = None
        self._tasks_since_last_run: int = 0
        self._run_threshold: int = 50  # Nach 50 Tasks automatisch analysieren

    # ─── Task-Counter (wird nach jedem Task aufgerufen) ───

    async def on_task_completed(self):
        self._tasks_since_last_run += 1
        if self._tasks_since_last_run >= self._run_threshold:
            await self.run_improvement_cycle()

    # ─── Hauptzyklus ───

    async def run_improvement_cycle(self) -> dict:
        logger.info("=== AUTO-IMPROVEMENT CYCLE START ===")
        self._tasks_since_last_run = 0
        self._last_run = datetime.now(timezone.utc)

        report = {
            "started_at": self._last_run.isoformat(),
            "patterns_found": 0,
            "improvements_proposed": 0,
            "improvements_auto_applied": 0,
            "learnings_stored": 0,
        }

        # ─── 1. Pattern-Analyse ───
        analysis = await self.patterns.run_full_analysis(days=7)
        total_patterns = sum(
            len(v) if isinstance(v, list) else 0 for v in analysis.values()
        )
        report["patterns_found"] = total_patterns

        # ─── 2. Verbesserungen generieren ───
        improvements = await self._generate_improvements(analysis)
        report["improvements_proposed"] = len(improvements)

        # ─── 3. Auto-Apply (low-risk) + Queue (high-risk) ───
        for imp in improvements:
            if imp["auto_apply"]:
                applied = await self._apply_improvement(imp)
                if applied:
                    report["improvements_auto_applied"] += 1
            else:
                await self._queue_improvement(imp)

        # ─── 4. Learnings aus dem Zyklus speichern ───
        learnings = await self._extract_learnings(analysis, improvements)
        report["learnings_stored"] = len(learnings)

        # ─── 5. Wissen aktualisieren ───
        await self._update_knowledge(analysis)

        logger.info(
            f"=== AUTO-IMPROVEMENT CYCLE DONE === "
            f"Patterns: {report['patterns_found']}, "
            f"Improvements: {report['improvements_proposed']}, "
            f"Auto-applied: {report['improvements_auto_applied']}"
        )

        return report

    # ─── Verbesserungen generieren ───

    async def _generate_improvements(self, analysis: dict) -> list[dict]:
        improvements = []

        # Aus Model-Performance: Bessere Modelle vorschlagen
        for pattern in analysis.get("model_performance", []):
            best = pattern.get("best_model")
            cheapest = pattern.get("cheapest_model")
            agent = pattern.get("agent")

            if best and cheapest and best != cheapest:
                best_score = pattern.get("best_score", 0)
                cheapest_cost = pattern.get("cheapest_cost", 0)

                # Wenn billigstes Model >80% Score hat → auto-switch
                cheapest_data = next(
                    (m for m in pattern.get("all_models", [])
                     if m["model"] == cheapest), None
                )
                if cheapest_data and cheapest_data["avg_score"] > 0.8:
                    improvements.append({
                        "category": "model_switch",
                        "title": f"{agent}: Switch zu {cheapest} (spart Kosten)",
                        "description": (
                            f"{cheapest} hat Score {cheapest_data['avg_score']:.2f} "
                            f"bei nur {cheapest_cost:.1f}ct/Task"
                        ),
                        "affected_agents": [agent],
                        "proposed_change": {
                            "type": "model_default",
                            "agent": agent,
                            "task_type": pattern.get("task_type"),
                            "from_model": best,
                            "to_model": cheapest,
                        },
                        "auto_apply": True,  # Low-risk: Model-Switch
                        "priority": 6,
                        "estimated_impact": "Kostenreduktion ohne Qualitätsverlust",
                    })

        # Aus Error-Patterns: Fixes vorschlagen
        for pattern in analysis.get("error_patterns", []):
            if pattern.get("type") == "recurring_error" and not pattern.get("resolved"):
                improvements.append({
                    "category": "prompt_fix",
                    "title": f"Fix für wiederkehrenden Fehler bei {pattern.get('agent')}",
                    "description": (
                        f"{pattern.get('error_type')}: {pattern.get('message', '')[:100]} "
                        f"({pattern.get('occurrences')}x aufgetreten)"
                    ),
                    "affected_agents": [pattern.get("agent")],
                    "proposed_change": {
                        "type": "error_fix",
                        "error_type": pattern.get("error_type"),
                        "agent": pattern.get("agent"),
                    },
                    "auto_apply": False,  # Prompt-Changes = high-risk
                    "priority": 8 if pattern.get("severity") == "critical" else 5,
                    "estimated_impact": f"Reduktion von {pattern.get('occurrences')} Fehlern",
                })

        # Aus Agent-Effizienz: Optimierungen
        for pattern in analysis.get("agent_efficiency", []):
            if pattern.get("status") == "critical":
                improvements.append({
                    "category": "workflow_change",
                    "title": f"Agent {pattern.get('agent')} braucht Optimierung",
                    "description": (
                        f"Effizienz: {pattern.get('efficiency_score', 0):.2f}, "
                        f"Error-Rate: {pattern.get('error_rate', 0):.0%}"
                    ),
                    "affected_agents": [pattern.get("agent")],
                    "proposed_change": {
                        "type": "agent_review",
                        "agent": pattern.get("agent"),
                        "metrics": pattern,
                    },
                    "auto_apply": False,
                    "priority": 7,
                    "estimated_impact": "Signifikante Effizienzsteigerung möglich",
                })

        # Aus Knowledge Gaps: Wissensaufbau
        for pattern in analysis.get("knowledge_gaps", []):
            improvements.append({
                "category": "knowledge_gap",
                "title": f"Wissenslücke bei {pattern.get('agent')}",
                "description": pattern.get("recommendation", ""),
                "affected_agents": [pattern.get("agent")],
                "proposed_change": {
                    "type": "knowledge_acquisition",
                    "agent": pattern.get("agent"),
                },
                "auto_apply": False,
                "priority": 6,
                "estimated_impact": "Weniger Fehler durch besseres Wissen",
            })

        # Aus Cost-Patterns: Kosten-Optimierungen
        for pattern in analysis.get("cost_patterns", []):
            if pattern.get("type") == "cost_optimization":
                improvements.append({
                    "category": "cost_optimization",
                    "title": f"Kosten-Optimierung für {pattern.get('agent')}",
                    "description": pattern.get("recommendation", ""),
                    "affected_agents": [pattern.get("agent")],
                    "proposed_change": {
                        "type": "cost_reduction",
                        "agent": pattern.get("agent"),
                        "current_cost": pattern.get("total_cost_cents"),
                    },
                    "auto_apply": False,
                    "priority": 5,
                    "estimated_impact": f"Kostenreduktion von {pattern.get('cost_share', 0):.0%}",
                })

        # Nach Priorität sortieren
        improvements.sort(key=lambda x: x["priority"], reverse=True)
        return improvements

    # ─── Auto-Apply (nur low-risk Änderungen) ───

    async def _apply_improvement(self, improvement: dict) -> bool:
        change = improvement.get("proposed_change", {})

        try:
            if change.get("type") == "model_default":
                # Pattern in DB aktualisieren → Smart Router nutzt das
                await self.db.client.table("patterns").upsert({
                    "agent_slug": change["agent"],
                    "task_type": change.get("task_type", "general"),
                    "best_model": change["to_model"],
                }, on_conflict="agent_slug,task_type").execute()

                logger.info(
                    f"Auto-applied: {change['agent']} default model "
                    f"{change.get('from_model')} → {change['to_model']}"
                )

                # In Improvement-Queue als deployed markieren
                await self._store_improvement(improvement, status="deployed")
                return True

        except Exception as e:
            logger.error(f"Auto-apply failed: {e}")
            await self._store_improvement(improvement, status="rejected")

        return False

    # ─── Improvement in Queue speichern ───

    async def _queue_improvement(self, improvement: dict):
        await self._store_improvement(improvement, status="proposed")

    async def _store_improvement(self, improvement: dict, status: str = "proposed"):
        try:
            await self.db.client.table("improvement_queue").insert({
                "category": improvement["category"],
                "priority": improvement.get("priority", 5),
                "title": improvement["title"],
                "description": improvement["description"],
                "affected_agents": improvement.get("affected_agents", []),
                "proposed_change": improvement.get("proposed_change"),
                "estimated_impact": improvement.get("estimated_impact"),
                "status": status,
                "implemented_at": (
                    datetime.now(timezone.utc).isoformat() if status == "deployed" else None
                ),
            }).execute()
        except Exception as e:
            logger.warning(f"Could not store improvement: {e}")

    # ─── Learnings extrahieren und speichern ───

    async def _extract_learnings(self, analysis: dict, improvements: list) -> list:
        learnings = []

        # Learning: Welche Patterns wurden gefunden
        for category, patterns in analysis.items():
            if isinstance(patterns, list) and patterns:
                for pattern in patterns[:3]:  # Max 3 pro Kategorie
                    try:
                        await self.db.client.table("learning_journal").insert({
                            "agent_slug": pattern.get("agent", "system"),
                            "event_type": "pattern_found",
                            "title": f"Pattern erkannt: {pattern.get('type', category)}",
                            "description": str(pattern)[:500],
                            "context": pattern,
                            "lesson_learned": pattern.get("recommendation", ""),
                            "applies_to": [pattern.get("agent", "system")],
                            "impact_score": 0.6,
                        }).execute()
                        learnings.append(pattern)
                    except Exception:
                        pass

        # Learning: Welche Verbesserungen wurden angewendet
        for imp in improvements:
            if imp.get("auto_apply"):
                try:
                    await self.db.client.table("learning_journal").insert({
                        "agent_slug": imp.get("affected_agents", ["system"])[0],
                        "event_type": "optimization",
                        "title": imp["title"],
                        "description": imp["description"],
                        "context": imp.get("proposed_change", {}),
                        "lesson_learned": imp.get("estimated_impact", ""),
                        "applies_to": imp.get("affected_agents", []),
                        "impact_score": 0.7,
                    }).execute()
                    learnings.append(imp)
                except Exception:
                    pass

        return learnings

    # ─── Wissen aus Analyse aktualisieren ───

    async def _update_knowledge(self, analysis: dict):
        """Speichert Analyse-Ergebnisse als Wissen in der Knowledge Base."""
        try:
            # Bester Agent
            efficiencies = analysis.get("agent_efficiency", [])
            if efficiencies:
                best = max(efficiencies, key=lambda x: x.get("efficiency_score", 0))
                await self.knowledge.learn_fact(
                    subject="System-Performance",
                    predicate="effizientester_agent",
                    object=f"{best['agent']} (Score: {best.get('efficiency_score', 0):.2f})",
                    source="auto_improver",
                    tags=["performance", "auto-analysis"],
                )

            # Gesamtkosten
            cost_patterns = analysis.get("cost_patterns", [])
            total_cost = sum(
                p.get("total_cost_cents", 0) for p in cost_patterns
                if p.get("type") == "cost_optimization"
            )
            if total_cost > 0:
                await self.knowledge.learn_fact(
                    subject="System-Kosten",
                    predicate="wöchentliche_kosten_cents",
                    object=str(round(total_cost, 2)),
                    source="auto_improver",
                    tags=["kosten", "auto-analysis"],
                )

        except Exception as e:
            logger.warning(f"Could not update knowledge from analysis: {e}")

    # ─── Pending Improvements abrufen (für ELON / DOM) ───

    async def get_pending_improvements(self) -> list[dict]:
        try:
            result = await self.db.client.table("improvement_queue") \
                .select("*") \
                .eq("status", "proposed") \
                .order("priority", desc=True) \
                .limit(20) \
                .execute()
            return result.data or []
        except Exception:
            return []

    # ─── Status ───

    async def get_status(self) -> dict:
        pending = await self.get_pending_improvements()
        return {
            "last_run": self._last_run.isoformat() if self._last_run else "never",
            "tasks_since_last_run": self._tasks_since_last_run,
            "run_threshold": self._run_threshold,
            "pending_improvements": len(pending),
        }
