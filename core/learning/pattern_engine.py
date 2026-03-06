"""
JARVIS 1.5 — Pattern Engine
Erkennt Muster über alle Daten hinweg.

Analysiert:
  - Welche Fehler treten wiederholt auf?
  - Welche Agent+Model Kombos sind am besten?
  - Welche Task-Typen brauchen welche Ressourcen?
  - Welche Zeiten sind am produktivsten?
  - Welche Workflows scheitern systematisch?
  - Wo gibt es Wissenslücken?

Muster werden automatisch erkannt und in der DB gespeichert.
ELON nutzt diese Muster für Optimierungen.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from collections import Counter, defaultdict

logger = logging.getLogger("jarvis.pattern_engine")


class PatternEngine:
    """
    Erkennt automatisch Muster in Task-Outcomes, Fehlern und Agent-Verhalten.
    Läuft als Hintergrund-Analyse — nicht bei jedem Request.
    """

    def __init__(self, db_client):
        self.db = db_client

    # ─── Hauptanalyse — wird periodisch aufgerufen ───

    async def run_full_analysis(self, days: int = 7) -> dict:
        """Führt alle Pattern-Analysen durch."""
        logger.info(f"Running full pattern analysis for last {days} days...")

        results = {}

        results["model_performance"] = await self.analyze_model_performance(days)
        results["error_patterns"] = await self.analyze_error_patterns(days)
        results["agent_efficiency"] = await self.analyze_agent_efficiency(days)
        results["task_patterns"] = await self.analyze_task_patterns(days)
        results["knowledge_gaps"] = await self.detect_knowledge_gaps(days)
        results["cost_patterns"] = await self.analyze_cost_patterns(days)

        # Erkannte Muster in DB speichern
        await self._store_patterns(results)

        logger.info(
            f"Pattern analysis complete: "
            f"{sum(len(v) if isinstance(v, list) else 1 for v in results.values())} patterns found"
        )
        return results

    # ─── Model-Performance Analyse ───

    async def analyze_model_performance(self, days: int = 7) -> list[dict]:
        """Welches Model ist für welchen Agent/Task am besten?"""
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        patterns = []

        try:
            result = await self.db.client.table("task_outcomes") \
                .select("agent_slug,task_type,model_used,score,cost_cents,duration_ms") \
                .gte("created_at", since) \
                .not_.is_("score", "null") \
                .execute()

            if not result.data:
                return []

            # Gruppiere nach agent+task_type+model
            groups = defaultdict(list)
            for row in result.data:
                key = (row["agent_slug"], row.get("task_type", "general"), row["model_used"])
                groups[key].append(row)

            # Finde beste Kombination pro agent+task_type
            agent_tasks = defaultdict(list)
            for (agent, task_type, model), outcomes in groups.items():
                if len(outcomes) < 3:
                    continue  # Mindestens 3 Samples

                avg_score = sum(o["score"] for o in outcomes) / len(outcomes)
                avg_cost = sum(o.get("cost_cents", 0) for o in outcomes) / len(outcomes)
                avg_duration = sum(o.get("duration_ms", 0) for o in outcomes) / len(outcomes)

                agent_tasks[(agent, task_type)].append({
                    "model": model,
                    "avg_score": round(avg_score, 3),
                    "avg_cost_cents": round(avg_cost, 2),
                    "avg_duration_ms": round(avg_duration),
                    "sample_count": len(outcomes),
                })

            for (agent, task_type), models in agent_tasks.items():
                best = max(models, key=lambda m: m["avg_score"])
                cheapest = min(models, key=lambda m: m["avg_cost_cents"])

                patterns.append({
                    "type": "model_performance",
                    "agent": agent,
                    "task_type": task_type,
                    "best_model": best["model"],
                    "best_score": best["avg_score"],
                    "cheapest_model": cheapest["model"],
                    "cheapest_cost": cheapest["avg_cost_cents"],
                    "all_models": models,
                })

        except Exception as e:
            logger.error(f"Model performance analysis failed: {e}")

        return patterns

    # ─── Fehler-Muster Analyse ───

    async def analyze_error_patterns(self, days: int = 7) -> list[dict]:
        """Welche Fehler treten wiederholt auf? Wo sind die Hotspots?"""
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        patterns = []

        try:
            result = await self.db.client.table("error_log") \
                .select("*") \
                .gte("created_at", since) \
                .order("occurrences", desc=True) \
                .limit(50) \
                .execute()

            if not result.data:
                return []

            # Top wiederkehrende Fehler
            for error in result.data:
                if error.get("occurrences", 1) >= 3:
                    patterns.append({
                        "type": "recurring_error",
                        "agent": error.get("agent_slug"),
                        "error_type": error.get("error_type"),
                        "message": error.get("error_message", "")[:200],
                        "occurrences": error.get("occurrences"),
                        "resolved": error.get("resolved", False),
                        "severity": "critical" if error.get("occurrences", 0) >= 10 else "warning",
                    })

            # Fehler pro Agent aggregieren
            agent_errors = Counter()
            for error in result.data:
                agent_errors[error.get("agent_slug", "unknown")] += error.get("occurrences", 1)

            for agent, count in agent_errors.most_common(5):
                if count >= 5:
                    patterns.append({
                        "type": "error_hotspot",
                        "agent": agent,
                        "total_errors": count,
                        "severity": "critical" if count >= 20 else "warning",
                    })

        except Exception as e:
            logger.error(f"Error pattern analysis failed: {e}")

        return patterns

    # ─── Agent-Effizienz Analyse ───

    async def analyze_agent_efficiency(self, days: int = 7) -> list[dict]:
        """Welche Agents sind effizient, welche nicht?"""
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        patterns = []

        try:
            result = await self.db.client.table("task_outcomes") \
                .select("agent_slug,score,cost_cents,duration_ms,error") \
                .gte("created_at", since) \
                .execute()

            if not result.data:
                return []

            agent_data = defaultdict(lambda: {
                "scores": [], "costs": [], "durations": [], "errors": 0, "total": 0
            })

            for row in result.data:
                agent = row["agent_slug"]
                agent_data[agent]["total"] += 1
                if row.get("score") is not None:
                    agent_data[agent]["scores"].append(row["score"])
                if row.get("cost_cents"):
                    agent_data[agent]["costs"].append(row["cost_cents"])
                if row.get("duration_ms"):
                    agent_data[agent]["durations"].append(row["duration_ms"])
                if row.get("error"):
                    agent_data[agent]["errors"] += 1

            for agent, data in agent_data.items():
                if data["total"] < 5:
                    continue

                avg_score = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0
                error_rate = data["errors"] / data["total"]
                avg_cost = sum(data["costs"]) / len(data["costs"]) if data["costs"] else 0

                efficiency = avg_score * (1 - error_rate)
                cost_efficiency = efficiency / max(avg_cost, 0.01)

                patterns.append({
                    "type": "agent_efficiency",
                    "agent": agent,
                    "total_tasks": data["total"],
                    "avg_score": round(avg_score, 3),
                    "error_rate": round(error_rate, 3),
                    "avg_cost_cents": round(avg_cost, 2),
                    "efficiency_score": round(efficiency, 3),
                    "cost_efficiency": round(cost_efficiency, 3),
                    "status": "healthy" if efficiency > 0.7 else (
                        "needs_attention" if efficiency > 0.4 else "critical"
                    ),
                })

        except Exception as e:
            logger.error(f"Agent efficiency analysis failed: {e}")

        return patterns

    # ─── Task-Muster Analyse ───

    async def analyze_task_patterns(self, days: int = 7) -> list[dict]:
        """Welche Task-Typen sind häufig? Welche scheitern?"""
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        patterns = []

        try:
            result = await self.db.client.table("task_outcomes") \
                .select("task_type,agent_slug,score,error") \
                .gte("created_at", since) \
                .execute()

            if not result.data:
                return []

            task_data = defaultdict(lambda: {"total": 0, "errors": 0, "scores": []})
            for row in result.data:
                task_type = row.get("task_type", "general")
                task_data[task_type]["total"] += 1
                if row.get("error"):
                    task_data[task_type]["errors"] += 1
                if row.get("score") is not None:
                    task_data[task_type]["scores"].append(row["score"])

            for task_type, data in task_data.items():
                if data["total"] < 3:
                    continue

                failure_rate = data["errors"] / data["total"]
                avg_score = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0

                if failure_rate > 0.3:
                    patterns.append({
                        "type": "failing_task_type",
                        "task_type": task_type,
                        "failure_rate": round(failure_rate, 3),
                        "avg_score": round(avg_score, 3),
                        "total_tasks": data["total"],
                        "severity": "critical" if failure_rate > 0.5 else "warning",
                    })

        except Exception as e:
            logger.error(f"Task pattern analysis failed: {e}")

        return patterns

    # ─── Wissenslücken erkennen ───

    async def detect_knowledge_gaps(self, days: int = 7) -> list[dict]:
        """Wo fehlt Wissen? Welche Themen tauchen oft auf ohne Lösung?"""
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        patterns = []

        try:
            # Fehler vom Typ "knowledge_gap" oder Tasks mit niedrigem Score
            errors = await self.db.client.table("error_log") \
                .select("*") \
                .gte("created_at", since) \
                .in_("error_type", ["knowledge_gap", "quality_fail", "hallucination"]) \
                .execute()

            if errors.data:
                gap_agents = Counter()
                for error in errors.data:
                    gap_agents[error.get("agent_slug", "unknown")] += 1

                for agent, count in gap_agents.most_common():
                    if count >= 2:
                        patterns.append({
                            "type": "knowledge_gap",
                            "agent": agent,
                            "gap_count": count,
                            "recommendation": f"Agent {agent} braucht mehr Wissen/Training",
                        })

            # Tasks mit sehr niedrigem Score = mögliche Wissenslücke
            low_scores = await self.db.client.table("task_outcomes") \
                .select("agent_slug,task_type,score,task_description") \
                .gte("created_at", since) \
                .lt("score", 0.4) \
                .not_.is_("score", "null") \
                .limit(20) \
                .execute()

            if low_scores.data:
                low_agents = Counter()
                for task in low_scores.data:
                    low_agents[task["agent_slug"]] += 1

                for agent, count in low_agents.most_common():
                    if count >= 3:
                        patterns.append({
                            "type": "performance_gap",
                            "agent": agent,
                            "low_score_tasks": count,
                            "recommendation": f"Agent {agent} hat systematisch niedrige Scores",
                        })

        except Exception as e:
            logger.error(f"Knowledge gap detection failed: {e}")

        return patterns

    # ─── Kosten-Muster Analyse ───

    async def analyze_cost_patterns(self, days: int = 7) -> list[dict]:
        """Wo wird zu viel Geld ausgegeben?"""
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        patterns = []

        try:
            result = await self.db.client.table("task_outcomes") \
                .select("agent_slug,model_used,cost_cents,score") \
                .gte("created_at", since) \
                .not_.is_("cost_cents", "null") \
                .execute()

            if not result.data:
                return []

            # Kosten pro Agent
            agent_costs = defaultdict(lambda: {"total": 0, "tasks": 0, "scores": []})
            for row in result.data:
                agent = row["agent_slug"]
                agent_costs[agent]["total"] += row.get("cost_cents", 0)
                agent_costs[agent]["tasks"] += 1
                if row.get("score") is not None:
                    agent_costs[agent]["scores"].append(row["score"])

            total_cost = sum(d["total"] for d in agent_costs.values())

            for agent, data in agent_costs.items():
                cost_share = data["total"] / max(total_cost, 0.01)
                avg_score = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0

                # Teuer aber schlecht = Optimierungs-Kandidat
                if cost_share > 0.3 and avg_score < 0.7:
                    patterns.append({
                        "type": "cost_optimization",
                        "agent": agent,
                        "cost_share": round(cost_share, 3),
                        "total_cost_cents": round(data["total"], 2),
                        "avg_score": round(avg_score, 3),
                        "recommendation": (
                            f"{agent} verbraucht {cost_share:.0%} der Kosten "
                            f"bei nur {avg_score:.0%} Score — Model-Downgrade prüfen"
                        ),
                    })

            # Modelle die Geld kosten aber Ollama ersetzen könnte
            model_data = defaultdict(lambda: {"cost": 0, "scores": [], "tasks": 0})
            for row in result.data:
                model = row.get("model_used", "unknown")
                model_data[model]["cost"] += row.get("cost_cents", 0)
                model_data[model]["tasks"] += 1
                if row.get("score") is not None:
                    model_data[model]["scores"].append(row["score"])

            for model, data in model_data.items():
                if data["cost"] > 0:
                    avg = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0
                    if avg < 0.6:
                        patterns.append({
                            "type": "model_waste",
                            "model": model,
                            "cost_cents": round(data["cost"], 2),
                            "avg_score": round(avg, 3),
                            "tasks": data["tasks"],
                            "recommendation": f"{model} kostet Geld bei schlechtem Score — Ollama testen",
                        })

        except Exception as e:
            logger.error(f"Cost pattern analysis failed: {e}")

        return patterns

    # ─── Muster in DB speichern ───

    async def _store_patterns(self, results: dict):
        for category, patterns in results.items():
            if not isinstance(patterns, list):
                continue
            for pattern in patterns:
                try:
                    agent = pattern.get("agent", "system")
                    task_type = pattern.get("task_type", pattern.get("type", "general"))

                    await self.db.client.table("patterns").upsert({
                        "agent_slug": agent,
                        "task_type": task_type,
                        "best_model": pattern.get("best_model") or pattern.get("model"),
                        "avg_score": pattern.get("avg_score") or pattern.get("efficiency_score"),
                        "avg_duration_ms": pattern.get("avg_duration_ms", 0),
                        "avg_cost_cents": pattern.get("avg_cost_cents") or pattern.get("cost_cents", 0),
                        "sample_count": pattern.get("sample_count") or pattern.get("total_tasks", 0),
                        "metadata": pattern,
                    }, on_conflict="agent_slug,task_type").execute()
                except Exception:
                    pass  # Pattern-Storage ist best-effort
