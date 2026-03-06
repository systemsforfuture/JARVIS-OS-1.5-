"""
JARVIS 1.5 — ELON Engine (Quality Gate + Optimizer + Error Solver)
SYSTEMS™ · architectofscale.com

ELON ist das Nervensystem von JARVIS.
Er sieht ALLES was passiert, analysiert JEDEN Fehler,
entwickelt Loesungen und optimiert das gesamte System.

Pipeline:
  1. QUALITY GATE     — Prueft jedes wichtige Ergebnis (Score 0-1)
  2. ERROR ANALYSIS   — Analysiert jeden Fehler, findet Root Cause
  3. SOLUTION ENGINE   — Entwickelt konkrete Loesungen
  4. AGENT OPTIMIZER  — Verbessert Agent-Configs basierend auf Daten
  5. PATTERN LEARNER  — Lernt aus Patterns und optimiert Routing
  6. KPI TRACKER      — Ueberwacht alle Metriken
  7. WEEKLY ANALYSIS  — Tiefenanalyse fuer DOM

ELON-Prinzip: Befund -> Ursache -> Loesung -> Umsetzung -> Messung
"""

import json
import time
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class QualityReport:
    """Qualitaetsbericht fuer ein Task-Ergebnis."""
    task_id: str
    agent_slug: str
    score: float = 0.0
    completeness: float = 0.0
    accuracy: float = 0.0
    brand_voice: float = 0.0
    actionability: float = 0.0
    issues: list = field(default_factory=list)
    suggestions: list = field(default_factory=list)
    approved: bool = True


class ElonEngine:
    """
    ELON — Analyst, Optimierer, Fehler-Loser.

    Laeuft parallel zu allen Tasks und analysiert alles.
    Kein Ergebnis verlaesst JARVIS ohne ELONs Check.
    Jeder Fehler wird gespeichert, analysiert, und geloest.
    Das System wird jeden Tag besser.
    """

    QUALITY_THRESHOLD_PASS = 0.6
    QUALITY_THRESHOLD_HIGH = 0.8

    def __init__(self, db=None, learning=None):
        """
        Args:
            db: SupabaseClient Instanz
            learning: SelfLearningEngine Instanz
        """
        self.db = db
        self.learning = learning

    # ══════════════════════════════════════
    # 1. QUALITY GATE
    # ══════════════════════════════════════

    async def quality_gate(
        self,
        task_id: str,
        agent_slug: str,
        prompt: str,
        result: str,
        task_type: str = "general",
    ) -> QualityReport:
        """
        Qualitaets-Gate: Pruefe ein Task-Ergebnis.

        Scoring:
          - Completeness (30%): Ist alles beantwortet?
          - Accuracy (30%): Ist es korrekt?
          - Brand Voice (20%): Stimmt der Ton?
          - Actionability (20%): Kann DOM damit arbeiten?

        Score < 0.6 = REJECTED -> Task wird mit hoeherem Modell wiederholt
        Score 0.6-0.8 = PASSED -> OK aber verbesserbar
        Score > 0.8 = EXCELLENT -> Perfekt
        """
        report = QualityReport(task_id=task_id, agent_slug=agent_slug)

        # Checks
        report.completeness = self._check_completeness(prompt, result)
        report.brand_voice = self._check_brand_voice(result)
        report.actionability = self._check_actionability(result)
        report.accuracy = self._check_accuracy(result)

        # Gesamt-Score
        report.score = round(
            report.completeness * 0.3
            + report.accuracy * 0.3
            + report.brand_voice * 0.2
            + report.actionability * 0.2,
            4,
        )

        report.approved = report.score >= self.QUALITY_THRESHOLD_PASS

        # Bei Reject: Fehler loggen + Memory speichern
        if not report.approved and self.db:
            report.suggestions.append(
                "Task mit hoeherem Modell-Tier wiederholen (Upgrade Routing)"
            )

            await self.db.log_error({
                "task_id": task_id,
                "agent_slug": agent_slug,
                "error_type": "quality_fail",
                "error_message": f"Quality Gate FAILED: Score {report.score:.0%}. Issues: {', '.join(report.issues)}",
                "error_context": {
                    "task_type": task_type,
                    "score": report.score,
                    "completeness": report.completeness,
                    "accuracy": report.accuracy,
                    "brand_voice": report.brand_voice,
                    "actionability": report.actionability,
                    "issues": report.issues,
                },
                "severity": "high",
            })

            # In Memory speichern damit es nicht wieder passiert
            await self.db.store_memory({
                "agent_slug": agent_slug,
                "memory_type": "error",
                "key": f"quality_fail_{task_id}",
                "value": f"Task {task_id} abgelehnt (Score: {report.score:.0%}). "
                        f"Issues: {', '.join(report.issues)}. "
                        f"Empfehlung: {', '.join(report.suggestions)}",
                "priority": "high",
                "tags": ["quality", "rejected", task_type],
                "metadata": {
                    "score": report.score,
                    "task_type": task_type,
                },
            })

            # Audit
            await self.db.audit(
                agent_slug="elon",
                action="quality_gate_failed",
                category="quality",
                details={
                    "task_id": task_id,
                    "agent": agent_slug,
                    "score": report.score,
                    "issues": report.issues,
                },
            )

        return report

    # ══════════════════════════════════════
    # 2. ERROR ANALYSIS + SOLUTION ENGINE
    # ══════════════════════════════════════

    async def analyze_errors(self) -> list:
        """
        Analysiere alle ungeloesten Fehler und entwickle Loesungen.

        ELON's Kernaufgabe:
        1. Hole alle unresolved Errors aus Supabase
        2. Gruppiere nach Typ und Agent
        3. Analysiere Root Cause
        4. Entwickle konkrete Loesung
        5. Speichere Loesung in error_solutions
        6. Markiere Fehler als resolved

        Gibt Liste von entwickelten Loesungen zurueck.
        """
        if not self.db:
            return []

        unresolved = await self.db.get_unresolved_errors()
        solutions_created = []

        for error in unresolved:
            # Pruefen ob schon eine Loesung fuer diesen Fehlertyp existiert
            existing_solutions = await self.db.get_solutions_for_error_type(
                error["error_type"]
            )

            if existing_solutions:
                # Es gibt schon eine effektive Loesung — anwenden
                best = existing_solutions[0]
                if (best.get("effectiveness") or 0) >= 0.7:
                    await self.db.resolve_error(error["id"], best["id"])
                    solutions_created.append({
                        "error_id": error["id"],
                        "reused_solution": best["id"],
                        "action": "reused_existing_solution",
                    })
                    continue

            # Neue Loesung entwickeln
            solution = self._develop_solution(error)

            stored = await self.db.store_solution(solution)

            # Error als resolved markieren
            if stored.get("id"):
                await self.db.resolve_error(error["id"], stored["id"])

            solutions_created.append({
                "error_id": error["id"],
                "solution_id": stored.get("id"),
                "solution_type": solution["solution_type"],
                "root_cause": solution["root_cause"],
                "solution": solution["solution"],
            })

            # In Memory speichern
            await self.db.store_memory({
                "agent_slug": error.get("agent_slug", "elon"),
                "memory_type": "learning",
                "key": f"error_solution_{error['error_type']}_{error['id'][:8]}",
                "value": f"Fehler: {error['error_message'][:200]}. "
                        f"Ursache: {solution['root_cause']}. "
                        f"Loesung: {solution['solution']}",
                "priority": "high",
                "tags": ["error", "solution", error["error_type"]],
            })

            # Audit
            await self.db.audit(
                agent_slug="elon",
                action="error_solved",
                category="error",
                details={
                    "error_id": error["id"],
                    "error_type": error["error_type"],
                    "solution_type": solution["solution_type"],
                    "occurrences": error.get("occurrences", 1),
                },
            )

        return solutions_created

    def _develop_solution(self, error: dict) -> dict:
        """
        Entwickle eine konkrete Loesung fuer einen Fehler.

        Analyse-Regeln (regelbasiert, kein LLM noetig):
        - timeout -> model_change (schnelleres Modell oder Groq)
        - rate_limit -> config_update (Rate Limiter anpassen)
        - model_error -> model_change (Fallback-Modell)
        - quality_fail -> prompt_fix (besserer Prompt + Kontext)
        - validation_error -> prompt_fix (Klarere Anforderungen)
        - runtime_error -> code_fix (Bug melden an ARCHI)
        """
        error_type = error.get("error_type", "unknown")
        context = error.get("error_context", {})
        agent = error.get("agent_slug", "unknown")
        occurrences = error.get("occurrences", 1)
        message = error.get("error_message", "")

        # Standard-Template
        solution = {
            "error_id": error["id"],
            "error_type": error_type,
            "root_cause": "",
            "solution": "",
            "solution_type": "prompt_fix",
            "implementation": {},
        }

        if error_type == "timeout":
            model = context.get("model_used", "unknown")
            solution["root_cause"] = f"Modell {model} zu langsam fuer Task-Typ {context.get('task_type', '?')}"
            solution["solution"] = (
                f"1. Task-Typ auf schnelleres Modell routen (Groq oder Ollama). "
                f"2. Prompt kuerzen (aktuell {context.get('tokens_input', '?')} Tokens). "
                f"3. Max-Token-Limit setzen."
            )
            solution["solution_type"] = "model_change"
            solution["implementation"] = {
                "action": "update_routing",
                "current_model": model,
                "suggested_model": "tier3-groq-fast" if "classification" in context.get("task_type", "") else "tier2-llama",
                "agent": agent,
                "task_type": context.get("task_type"),
            }

        elif error_type == "rate_limit":
            solution["root_cause"] = "API Rate Limit erreicht — zu viele gleichzeitige Anfragen"
            solution["solution"] = (
                "1. Request-Queue mit Backoff implementieren. "
                "2. Mehr Tasks auf Ollama (lokal, kein Limit) routen. "
                "3. Caching aktivieren fuer wiederkehrende Anfragen."
            )
            solution["solution_type"] = "config_update"
            solution["implementation"] = {
                "action": "enable_rate_limiting",
                "backoff_ms": 1000,
                "max_concurrent": 5,
                "cache_ttl_seconds": 300,
            }

        elif error_type == "model_error":
            model = context.get("model_used", "unknown")
            solution["root_cause"] = f"Modell {model} hat einen Fehler zurueckgegeben"
            solution["solution"] = (
                f"1. Fallback auf alternatives Modell aktivieren. "
                f"2. Bei {occurrences}+ Occurrences: Standard-Modell fuer diesen Agent wechseln."
            )
            solution["solution_type"] = "model_change"
            fallback = "tier1-sonnet" if "tier2" in model else "tier2-llama"
            solution["implementation"] = {
                "action": "set_fallback_model",
                "failing_model": model,
                "fallback_model": fallback,
                "agent": agent,
                "auto_switch_threshold": 3,
            }

        elif error_type == "quality_fail":
            score = context.get("score", 0)
            task_type = context.get("task_type", "unknown")
            issues = context.get("issues", [])
            solution["root_cause"] = (
                f"Quality Score {score:.0%} unter Minimum (60%). "
                f"Issues: {', '.join(issues) if issues else 'Unbekannt'}"
            )
            solution["solution"] = (
                f"1. Prompt-Template fuer {task_type} ueberarbeiten — mehr Kontext + klarere Anforderungen. "
                f"2. Modell-Tier erhoehen (Sonnet statt Haiku/Ollama). "
                f"3. Brain-Kontext-Injection aktivieren fuer diesen Task-Typ."
            )
            solution["solution_type"] = "prompt_fix"
            solution["implementation"] = {
                "action": "improve_prompt",
                "agent": agent,
                "task_type": task_type,
                "add_context_injection": True,
                "upgrade_model_tier": True,
                "issues_to_fix": issues,
            }

        elif error_type == "validation_error":
            solution["root_cause"] = "Output hat Validierung nicht bestanden"
            solution["solution"] = (
                "1. Output-Schema definieren und erzwingen. "
                "2. Prompt mit Beispiel-Output ergaenzen. "
                "3. Retry mit structured output (JSON mode)."
            )
            solution["solution_type"] = "prompt_fix"
            solution["implementation"] = {
                "action": "add_output_schema",
                "agent": agent,
                "enforce_json": True,
                "add_example_output": True,
            }

        else:  # runtime_error oder unknown
            solution["root_cause"] = f"Runtime-Fehler: {message[:200]}"
            solution["solution"] = (
                f"1. Fehler an ARCHI (Dev-Team) melden. "
                f"2. Detaillierten Bug-Report erstellen. "
                f"3. Temporaeren Workaround implementieren."
            )
            solution["solution_type"] = "code_fix"
            solution["implementation"] = {
                "action": "create_bug_report",
                "assign_to": "archi",
                "error_message": message[:500],
                "priority": "high" if occurrences >= 3 else "medium",
            }

        return solution

    # ══════════════════════════════════════
    # 3. AGENT OPTIMIZER
    # ══════════════════════════════════════

    async def optimize_all_agents(self) -> list:
        """
        Analysiere und optimiere ALLE Agents.

        Prueft fuer jeden Agent:
        - Gibt es ein guenstigeres Modell das genauso gut ist?
        - Gibt es wiederholte Fehler?
        - Wird Ollama genug genutzt?
        - Ist der Agent-Prompt optimal?

        Speichert Optimierungen in der optimizations Tabelle.
        """
        if not self.db:
            return []

        agents = [
            "jarvis", "elon", "steve", "donald", "archi",
            "donna", "iris", "satoshi", "felix", "andreas",
        ]

        all_optimizations = []

        for slug in agents:
            opts = await self._optimize_agent(slug)
            all_optimizations.extend(opts)

        return all_optimizations

    async def _optimize_agent(self, agent_slug: str) -> list:
        """Optimiere einen einzelnen Agent."""
        optimizations = []

        report = await self.learning.get_agent_report(agent_slug)
        if report.get("tasks_total", 0) < 5:
            return []  # Zu wenig Daten

        # 1. Modell-Downgrade moeglich?
        model_usage = report.get("model_usage", {})
        for model, count in model_usage.items():
            if model in ("tier1-opus", "tier0-kimi") and count > 5:
                # Teueres Modell — pruefen ob guenstigeres auch reicht
                opt = {
                    "agent_slug": agent_slug,
                    "category": "model_routing",
                    "title": f"Modell-Downgrade fuer {agent_slug.upper()}",
                    "current_state": f"Nutzt {model} fuer {count} Tasks",
                    "suggested_state": f"Teste tier1-sonnet oder tier2-qwen — bei Score >0.7 dauerhaft wechseln",
                    "expected_impact": f"Einsparung ~{count * 15} Cent/Woche",
                    "confidence": 0.75,
                    "evidence": [f"Agent {agent_slug}: {count}x {model} in 7 Tagen"],
                }
                optimizations.append(opt)
                if self.db:
                    await self.db.store_optimization(opt)

        # 2. Hohe Error-Rate?
        if report.get("error_rate", 0) > 0.1:
            opt = {
                "agent_slug": agent_slug,
                "category": "prompt_engineering",
                "title": f"Error-Rate senken fuer {agent_slug.upper()}",
                "current_state": f"Error-Rate: {report['error_rate']:.0%}",
                "suggested_state": "Prompt-Templates ueberarbeiten, mehr Kontext injizieren, Validation hinzufuegen",
                "expected_impact": "Reduktion auf <5% Error-Rate",
                "confidence": 0.8,
                "evidence": [
                    f"Error-Rate {report['error_rate']:.0%} bei {report['tasks_total']} Tasks",
                    f"Unresolved Errors: {report.get('unresolved_errors', 0)}",
                ],
            }
            optimizations.append(opt)
            if self.db:
                await self.db.store_optimization(opt)

        # 3. Ollama nicht genug genutzt?
        ollama_usage = sum(
            c for m, c in model_usage.items() if "tier2" in m
        )
        total = report["tasks_total"]
        ollama_ratio = ollama_usage / max(total, 1)

        if ollama_ratio < 0.3 and total > 10:
            opt = {
                "agent_slug": agent_slug,
                "category": "model_routing",
                "title": f"Mehr Ollama fuer {agent_slug.upper()}",
                "current_state": f"Ollama-Anteil: {ollama_ratio:.0%}",
                "suggested_state": "Routine-Tasks (Datensammlung, Formatting, einfache Checks) auf Ollama routen",
                "expected_impact": f"Einsparung ~{int(total * 0.3 * 5)} Cent/Woche",
                "confidence": 0.85,
                "evidence": [
                    f"Nur {ollama_ratio:.0%} Ollama-Nutzung bei {total} Tasks",
                ],
            }
            optimizations.append(opt)
            if self.db:
                await self.db.store_optimization(opt)

        # 4. Score-Trend negativ?
        if report.get("trend_label") == "abwaerts":
            opt = {
                "agent_slug": agent_slug,
                "category": "process",
                "title": f"Performance-Einbruch bei {agent_slug.upper()}",
                "current_state": f"Score-Trend: abwaerts ({report.get('score_trend', 0):+.2%})",
                "suggested_state": "Root Cause Analyse durchfuehren, letzte Aenderungen pruefen, Prompt-Template revert pruefen",
                "expected_impact": "Score-Stabilisierung auf >0.8",
                "confidence": 0.7,
                "evidence": [
                    f"Score-Trend: {report.get('score_trend', 0):+.2%}",
                    f"Aktueller Score: {report.get('avg_score', 0):.0%}",
                ],
            }
            optimizations.append(opt)
            if self.db:
                await self.db.store_optimization(opt)

        return optimizations

    # ══════════════════════════════════════
    # 4. KPI TRACKER
    # ══════════════════════════════════════

    async def track_kpis(self) -> dict:
        """
        Berechne und speichere alle KPIs in Supabase.
        Taeglich aufrufen.
        """
        if not self.db or not self.learning:
            return {}

        report = await self.learning.get_system_report()

        kpis = {
            "tasks_total": {
                "value": report.get("total_tasks", 0),
                "target": 0,
                "unit": "tasks",
            },
            "avg_score": {
                "value": report.get("avg_score", 0),
                "target": 0.8,
                "unit": "score",
            },
            "monthly_cost_eur": {
                "value": report.get("total_cost_eur", 0),
                "target": 500,
                "unit": "EUR",
            },
            "ollama_ratio": {
                "value": report.get("ollama_ratio", 0) * 100,
                "target": 60,
                "unit": "%",
            },
            "ollama_savings_eur": {
                "value": report.get("estimated_savings_eur", 0),
                "target": 0,
                "unit": "EUR",
            },
            "unresolved_errors": {
                "value": report.get("unresolved_errors", 0),
                "target": 0,
                "unit": "errors",
            },
            "bottlenecks": {
                "value": len(report.get("bottlenecks", [])),
                "target": 0,
                "unit": "issues",
            },
        }

        # In Supabase speichern
        for name, data in kpis.items():
            await self.db.store_kpi(
                name=name,
                value=data["value"],
                target=data["target"],
                unit=data["unit"],
            )

        return kpis

    # ══════════════════════════════════════
    # 5. WEEKLY DEEP ANALYSIS
    # ══════════════════════════════════════

    async def weekly_analysis(self) -> dict:
        """
        Woechentliche Tiefenanalyse — wird an DOM gesendet.

        Inhalt:
        1. Executive Summary (1 Absatz)
        2. KPIs mit Trends
        3. Top-Fehler und deren Loesungen
        4. Agent-Rankings
        5. Kostensparmoeglichkeiten
        6. Konkrete Empfehlungen (Top 5)
        """
        if not self.db or not self.learning:
            return {"status": "no_data"}

        # Daten sammeln
        system_report = await self.learning.get_system_report()
        kpis = await self.track_kpis()
        solutions = await self.analyze_errors()
        optimizations = await self.optimize_all_agents()

        # Unresolved errors
        all_errors = await self.db.get_unresolved_errors()
        pending_opts = await self.db.get_pending_optimizations()

        # Agent Rankings
        agent_rankings = []
        for slug, stats in system_report.get("agent_summary", {}).items():
            agent_rankings.append({
                "agent": slug,
                "score": stats["avg_score"],
                "tasks": stats["tasks"],
                "cost": stats["total_cost_eur"],
                "trend": stats["trend"],
            })
        agent_rankings.sort(key=lambda a: a["score"], reverse=True)

        # Executive Summary
        total = system_report.get("total_tasks", 0)
        avg_score = system_report.get("avg_score", 0)
        cost = system_report.get("total_cost_eur", 0)
        savings = system_report.get("estimated_savings_eur", 0)
        errors = system_report.get("unresolved_errors", 0)
        bottlenecks = system_report.get("bottlenecks", [])

        summary = (
            f"Diese Woche: {total} Tasks ausgefuehrt. "
            f"Durchschnitts-Score: {avg_score:.0%}. "
            f"Kosten: {cost:.2f} EUR (gespart durch Ollama: {savings:.2f} EUR). "
            f"{errors} ungeloeste Fehler. "
            f"{len(bottlenecks)} Bottlenecks. "
            f"{len(solutions)} Fehler-Loesungen entwickelt. "
            f"{len(optimizations)} Optimierungsvorschlaege erstellt."
        )

        analysis = {
            "period": "weekly",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generated_by": "elon",
            "executive_summary": summary,
            "kpis": kpis,
            "system_report": system_report,
            "agent_rankings": agent_rankings,
            "errors_solved": len(solutions),
            "errors_remaining": len(all_errors),
            "optimizations_proposed": len(optimizations),
            "optimizations_pending": len(pending_opts),
            "top_recommendations": self._generate_top_recommendations(
                system_report, bottlenecks, optimizations
            ),
        }

        # In Memory speichern fuer Kontext
        if self.db:
            await self.db.store_memory({
                "agent_slug": "elon",
                "memory_type": "pattern",
                "key": f"weekly_analysis_{datetime.now(timezone.utc).strftime('%Y_%W')}",
                "value": summary,
                "priority": "high",
                "tags": ["weekly", "analysis", "report"],
                "metadata": {
                    "total_tasks": total,
                    "avg_score": avg_score,
                    "cost_eur": cost,
                },
            })

            # Audit
            await self.db.audit(
                agent_slug="elon",
                action="weekly_analysis",
                category="optimization",
                details={
                    "tasks": total,
                    "avg_score": avg_score,
                    "errors_solved": len(solutions),
                    "optimizations": len(optimizations),
                },
            )

        return analysis

    def _generate_top_recommendations(
        self,
        report: dict,
        bottlenecks: list,
        optimizations: list,
    ) -> list:
        """Top 5 Empfehlungen generieren."""
        recs = []

        # Aus Bottlenecks
        for b in bottlenecks[:3]:
            recs.append({
                "priority": "HIGH",
                "agent": b.get("agent", "system"),
                "title": b["issue"],
                "action": f"Agent {b['agent'].upper()} optimieren — Prompt + Modell pruefen",
            })

        # Aus Optimierungen
        for opt in optimizations[:5 - len(recs)]:
            recs.append({
                "priority": "MEDIUM",
                "agent": opt["agent_slug"],
                "title": opt["title"],
                "action": opt["suggested_state"],
            })

        # Immer: Ollama-Empfehlung
        ollama_ratio = report.get("ollama_ratio", 0)
        if ollama_ratio < 0.5:
            recs.append({
                "priority": "HIGH",
                "agent": "system",
                "title": f"Ollama-Anteil erhoehen (aktuell {ollama_ratio:.0%})",
                "action": "Mehr Routine-Tasks auf Ollama routen. Ziel: >60%. Spart sofort Geld.",
            })

        return recs[:5]

    # ══════════════════════════════════════
    # QUALITY CHECK HELPERS
    # ══════════════════════════════════════

    def _check_completeness(self, prompt: str, result: str) -> float:
        score = 0.7
        question_count = prompt.count("?")
        if question_count > 0:
            expected_min = question_count * 50
            score += 0.2 if len(result) >= expected_min else -0.2
        if prompt.count("- [ ]") + prompt.count("- [x]") > 0:
            score += 0.1
        return max(0.0, min(1.0, score))

    def _check_brand_voice(self, result: str) -> float:
        score = 0.7
        weak = ["ich denke", "vielleicht", "eventuell", "moeglicherweise", "gute frage"]
        rl = result.lower()
        for w in weak:
            if w in rl:
                score -= 0.05
        if result[:50].count(":") > 0:
            score += 0.05
        if len(result.split("\n")) > 3:
            score += 0.05
        if any(c.isdigit() for c in result[:200]):
            score += 0.05
        return max(0.0, min(1.0, score))

    def _check_actionability(self, result: str) -> float:
        score = 0.6
        if any(m in result for m in ["1.", "- ", "## ", "**"]):
            score += 0.15
        actions = ["erstelle", "sende", "oeffne", "klicke", "buche", "starte"]
        for a in actions:
            if a in result.lower():
                score += 0.05
        if sum(1 for c in result if c.isdigit()) > 5:
            score += 0.1
        return max(0.0, min(1.0, score))

    def _check_accuracy(self, result: str) -> float:
        score = 0.7
        errors = ["ich bin nicht sicher", "ich kann nicht", "error", "entschuldigung", "nicht moeglich"]
        rl = result.lower()
        for e in errors:
            if e in rl:
                score -= 0.1
        return max(0.0, min(1.0, score))
