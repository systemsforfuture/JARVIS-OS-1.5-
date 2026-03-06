"""
JARVIS 1.5 — Self-Learning System (Supabase-Backed)
SYSTEMS™ · architectofscale.com

Das Gehirn von JARVIS. Alles was passiert wird gespeichert,
analysiert und optimiert. Das System wird mit jedem Task schlauer.

Ablauf:
  1. Task wird ausgefuehrt -> Ergebnis in Supabase gespeichert
  2. Auto-Scoring (0.0-1.0) berechnet Qualitaet
  3. Pattern-Erkennung bei 3+ aehnlichen Tasks
  4. Fehler werden im Error Log gespeichert
  5. ELON analysiert alle Daten und optimiert
  6. Modell-Routing wird automatisch angepasst

Datenbank-Tabellen:
  - task_outcomes: Jedes einzelne Ergebnis
  - error_log: Jeder Fehler mit Occurrence-Counter
  - patterns: Erkannte Muster (Agent+TaskType -> bestes Modell)
  - optimizations: Verbesserungsvorschlaege von ELON
"""

import hashlib
import time
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class ScoreSource(Enum):
    AUTO = "auto"
    DOM_APPROVED = "dom"
    DOM_REJECTED = "reject"
    CORRECTED = "corrected"
    TIMEOUT = "timeout"


@dataclass
class TaskOutcome:
    """Ergebnis eines ausgefuehrten Tasks."""
    task_id: str
    agent_slug: str
    task_type: str
    model_used: str
    prompt: str
    response: str
    tokens_input: int
    tokens_output: int
    duration_ms: int
    score: float = 0.0
    score_source: ScoreSource = ScoreSource.AUTO
    cost_cents: float = 0.0
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class SelfLearningEngine:
    """
    Self-Learning Engine — Speichert alles in Supabase.

    Jeder Task-Outcome wird gespeichert. Jeder Fehler geloggt.
    Patterns werden automatisch erkannt. Das System lernt.
    """

    PATTERN_THRESHOLD = 3  # Min. gleiche Tasks fuer Pattern-Erkennung

    # Kosten pro Task in Cent (geschaetzt)
    MODEL_COSTS = {
        "tier0-kimi": 30,
        "tier0-kimi-thinking": 50,
        "tier1-opus": 20,
        "tier1-sonnet": 5,
        "tier1-haiku": 1,
        "tier2-qwen-coder": 0,
        "tier2-llama": 0,
        "tier2-qwen-general": 0,
        "tier3-groq-fast": 0.5,
        "tier3-groq-small": 0.1,
    }

    def __init__(self, db=None):
        """
        Args:
            db: SupabaseClient Instanz
        """
        self.db = db

    async def record_outcome(self, outcome: TaskOutcome) -> dict:
        """
        Speichere Task-Ergebnis in Supabase und triggere Analyse.

        Wird nach JEDEM Task automatisch aufgerufen.
        Ablauf:
          1. Auto-Score berechnen
          2. Kosten berechnen
          3. In task_outcomes speichern
          4. Bei Fehler: Error loggen
          5. Pattern-Check triggern
          6. Agent Performance updaten
        """
        # 1. Auto-Score
        if outcome.score == 0.0 and outcome.score_source == ScoreSource.AUTO:
            outcome.score = self._auto_score(outcome)

        # 2. Kosten berechnen
        if outcome.cost_cents == 0:
            outcome.cost_cents = self._calculate_cost(outcome)

        # 3. In Supabase speichern
        stored = {}
        if self.db:
            stored = await self.db.store_task_outcome({
                "task_id": outcome.task_id,
                "agent_slug": outcome.agent_slug,
                "task_type": outcome.task_type,
                "model_used": outcome.model_used,
                "prompt": outcome.prompt,
                "response": outcome.response,
                "tokens_input": outcome.tokens_input,
                "tokens_output": outcome.tokens_output,
                "duration_ms": outcome.duration_ms,
                "cost_cents": outcome.cost_cents,
                "score": outcome.score,
                "score_source": outcome.score_source.value,
                "error": outcome.error,
                "metadata": outcome.metadata,
            })

            # 4. Bei Fehler: Error loggen
            if outcome.error:
                await self._log_error(outcome)

            # 5. Pattern-Check
            await self._check_and_update_pattern(outcome)

            # 6. Agent Performance updaten
            await self._update_agent_performance(outcome)

            # 7. Audit Log
            await self.db.audit(
                agent_slug=outcome.agent_slug,
                action="task_completed",
                category="task",
                details={
                    "task_type": outcome.task_type,
                    "model": outcome.model_used,
                    "score": outcome.score,
                    "duration_ms": outcome.duration_ms,
                    "cost_cents": outcome.cost_cents,
                    "has_error": outcome.error is not None,
                },
            )

        return stored

    async def get_agent_report(self, agent_slug: str) -> dict:
        """
        Performance-Report fuer einen Agent.
        Holt alle Daten aus Supabase.
        """
        if not self.db:
            return {"agent": agent_slug, "status": "no_db"}

        outcomes = await self.db.get_agent_outcomes(agent_slug, days=7)
        if not outcomes:
            return {"agent": agent_slug, "status": "no_data", "tasks_total": 0}

        total = len(outcomes)
        scores = [o.get("score", 0) or 0 for o in outcomes]
        costs = [float(o.get("cost_cents", 0) or 0) for o in outcomes]
        durations = [o.get("duration_ms", 0) or 0 for o in outcomes]
        errors = [o for o in outcomes if o.get("error")]

        # Modell-Verteilung
        model_usage = {}
        model_scores = {}
        for o in outcomes:
            m = o.get("model_used", "unknown")
            model_usage[m] = model_usage.get(m, 0) + 1
            if m not in model_scores:
                model_scores[m] = []
            model_scores[m].append(o.get("score", 0) or 0)

        # Bestes Modell
        best_model = None
        best_avg = 0
        for model, s in model_scores.items():
            avg = sum(s) / len(s) if s else 0
            if avg > best_avg:
                best_avg = avg
                best_model = model

        # Score-Trend (letzte 10 vs vorherige 10)
        recent = scores[:10]
        previous = scores[10:20] if len(scores) >= 20 else scores[len(scores)//2:]
        trend = 0
        if recent and previous:
            trend = (sum(recent) / len(recent)) - (sum(previous) / len(previous))

        # Ungeloeste Fehler
        unresolved = await self.db.get_unresolved_errors(agent_slug=agent_slug)

        # Patterns
        patterns = await self.db.get_all_patterns(agent_slug=agent_slug)

        return {
            "agent": agent_slug,
            "period": "7_days",
            "tasks_total": total,
            "avg_score": round(sum(scores) / total, 4) if total else 0,
            "score_trend": round(trend, 4),
            "trend_label": "aufwaerts" if trend > 0.02 else "abwaerts" if trend < -0.02 else "stabil",
            "total_cost_eur": round(sum(costs) / 100, 2),
            "avg_duration_ms": int(sum(durations) / total) if total else 0,
            "error_rate": round(len(errors) / total, 4) if total else 0,
            "unresolved_errors": len(unresolved),
            "model_usage": model_usage,
            "best_model": best_model,
            "best_model_score": round(best_avg, 4),
            "patterns_found": len(patterns),
        }

    async def get_system_report(self) -> dict:
        """Globaler System-Report — alle Agents, alle Daten."""
        if not self.db:
            return {"status": "no_db", "total_tasks": 0}

        # Daten fuer alle Agents holen
        agents = [
            "jarvis", "elon", "steve", "donald", "archi",
            "donna", "iris", "satoshi", "felix", "andreas",
        ]

        agent_summary = {}
        total_tasks = 0
        total_cost = 0
        all_scores = []
        ollama_tasks = 0

        for slug in agents:
            report = await self.get_agent_report(slug)
            if report.get("tasks_total", 0) > 0:
                agent_summary[slug] = {
                    "tasks": report["tasks_total"],
                    "avg_score": report["avg_score"],
                    "total_cost_eur": report["total_cost_eur"],
                    "error_rate": report["error_rate"],
                    "trend": report["trend_label"],
                    "best_model": report["best_model"],
                }
                total_tasks += report["tasks_total"]
                total_cost += report["total_cost_eur"]
                # Ollama-Anteil berechnen
                for model, count in report.get("model_usage", {}).items():
                    if "tier2" in model:
                        ollama_tasks += count

        # Kosten-Ersparnis durch Ollama
        saved_if_sonnet = ollama_tasks * 5  # ~5 Cent pro Task bei Sonnet

        # Ungeloeste Fehler gesamt
        all_errors = await self.db.get_unresolved_errors()

        # Bottlenecks
        bottlenecks = []
        for slug, stats in agent_summary.items():
            if stats["avg_score"] < 0.6:
                bottlenecks.append({
                    "agent": slug,
                    "issue": f"Niedrige Qualitaet ({stats['avg_score']:.0%})",
                    "severity": "high",
                })
            if stats["error_rate"] > 0.15:
                bottlenecks.append({
                    "agent": slug,
                    "issue": f"Hohe Error-Rate ({stats['error_rate']:.0%})",
                    "severity": "high",
                })

        return {
            "total_tasks": total_tasks,
            "avg_score": round(sum(s["avg_score"] for s in agent_summary.values()) / max(len(agent_summary), 1), 4),
            "total_cost_eur": round(total_cost, 2),
            "ollama_tasks": ollama_tasks,
            "ollama_ratio": round(ollama_tasks / max(total_tasks, 1), 4),
            "estimated_savings_eur": round(saved_if_sonnet / 100, 2),
            "unresolved_errors": len(all_errors),
            "agent_summary": agent_summary,
            "bottlenecks": bottlenecks,
        }

    async def get_best_model_for_task(self, agent_slug: str, task_type: str) -> Optional[str]:
        """
        Hole das beste Modell fuer einen Task-Typ basierend auf Patterns.
        Wird vom Smart Router genutzt fuer Routing-Optimierung.
        """
        if not self.db:
            return None

        pattern = await self.db.get_pattern(agent_slug, task_type)
        if pattern and pattern.get("occurrences", 0) >= self.PATTERN_THRESHOLD:
            return pattern.get("best_model")
        return None

    def _auto_score(self, outcome: TaskOutcome) -> float:
        """
        Automatisches Scoring (0.0-1.0).

        Heuristik:
        - Basis: 0.5
        - Fehler: -0.4
        - Response-Laenge: +/- 0.1-0.3
        - Geschwindigkeit: +/- 0.05-0.15
        - Token-Effizienz: +0.1
        - Lokales Modell (0 EUR): +0.05 Bonus
        """
        score = 0.5

        if outcome.error:
            return max(0.1, score - 0.4)

        # Response-Laenge
        rlen = len(outcome.response)
        if rlen < 10:
            score -= 0.3
        elif rlen < 50:
            score -= 0.1
        elif rlen > 200:
            score += 0.1

        # Geschwindigkeit
        if outcome.duration_ms < 500:
            score += 0.05
        elif outcome.duration_ms < 5000:
            score += 0.15
        elif outcome.duration_ms < 15000:
            score += 0.1
        elif outcome.duration_ms > 60000:
            score -= 0.15

        # Token-Effizienz
        if outcome.tokens_output > 0:
            efficiency = rlen / outcome.tokens_output
            if efficiency > 3:
                score += 0.1

        # Lokales Modell Bonus
        if outcome.cost_cents == 0:
            score += 0.05

        return max(0.0, min(1.0, round(score, 4)))

    def _calculate_cost(self, outcome: TaskOutcome) -> float:
        """Berechne Kosten basierend auf Modell und Tokens."""
        base_cost = self.MODEL_COSTS.get(outcome.model_used, 5)
        # Skaliere mit Token-Anzahl (grob)
        token_factor = (outcome.tokens_input + outcome.tokens_output) / 1000
        return round(base_cost * max(token_factor, 0.1), 4)

    async def _log_error(self, outcome: TaskOutcome):
        """Fehler in error_log speichern."""
        error_type = "runtime_error"
        if "timeout" in (outcome.error or "").lower():
            error_type = "timeout"
        elif "rate_limit" in (outcome.error or "").lower():
            error_type = "rate_limit"
        elif "model" in (outcome.error or "").lower():
            error_type = "model_error"

        await self.db.log_error({
            "task_id": outcome.task_id,
            "agent_slug": outcome.agent_slug,
            "error_type": error_type,
            "error_message": outcome.error,
            "error_context": {
                "task_type": outcome.task_type,
                "model_used": outcome.model_used,
                "prompt_preview": outcome.prompt[:200],
                "duration_ms": outcome.duration_ms,
                "tokens_input": outcome.tokens_input,
            },
            "severity": "high" if error_type in ("timeout", "model_error") else "medium",
        })

    async def _check_and_update_pattern(self, outcome: TaskOutcome):
        """
        Pattern-Erkennung: Bei 3+ gleichen Tasks wird das beste Modell identifiziert.
        Pattern wird in Supabase gespeichert und vom Smart Router genutzt.
        """
        outcomes = await self.db.get_task_outcomes(
            agent_slug=outcome.agent_slug,
            task_type=outcome.task_type,
            limit=50,
        )

        if len(outcomes) < self.PATTERN_THRESHOLD:
            return

        # Modell-Scores berechnen
        model_scores = {}
        total_duration = 0
        total_cost = 0
        total_score = 0

        for o in outcomes:
            m = o.get("model_used", "unknown")
            s = o.get("score", 0) or 0
            if m not in model_scores:
                model_scores[m] = []
            model_scores[m].append(s)
            total_duration += o.get("duration_ms", 0) or 0
            total_cost += float(o.get("cost_cents", 0) or 0)
            total_score += s

        count = len(outcomes)
        model_avgs = {m: round(sum(s) / len(s), 4) for m, s in model_scores.items() if s}
        best_model = max(model_avgs, key=model_avgs.get) if model_avgs else "unknown"

        await self.db.upsert_pattern({
            "pattern_key": f"{outcome.agent_slug}:{outcome.task_type}",
            "agent_slug": outcome.agent_slug,
            "task_type": outcome.task_type,
            "description": f"{outcome.agent_slug} bei {outcome.task_type}: {count} Tasks analysiert",
            "best_model": best_model,
            "avg_score": round(total_score / count, 4),
            "avg_duration_ms": int(total_duration / count),
            "avg_cost_cents": round(total_cost / count, 4),
            "occurrences": count,
            "model_scores": model_avgs,
            "recommendation": f"Verwende {best_model} fuer {outcome.task_type} (Score: {model_avgs.get(best_model, 0):.0%})",
        })

    async def _update_agent_performance(self, outcome: TaskOutcome):
        """Update Agent-Performance in der agents Tabelle."""
        report = await self.get_agent_report(outcome.agent_slug)
        if report.get("tasks_total", 0) > 0:
            await self.db.update_agent_performance(outcome.agent_slug, {
                "score_avg": report["avg_score"],
                "tasks_total": report["tasks_total"],
                "error_rate": report["error_rate"],
                "trend": report["trend_label"],
                "best_model": report["best_model"],
                "cost_eur_7d": report["total_cost_eur"],
            })
