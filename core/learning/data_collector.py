"""
JARVIS 1.5 — Automatic Data Collector
SYSTEMS™ · architectofscale.com

Sammelt automatisch ALLE Daten die im System anfallen.
Laeuft als Middleware — jeder Task geht durch den Collector.

Was gesammelt wird:
  - Task Start/End/Dauer/Ergebnis
  - Fehler mit vollem Kontext
  - Modell-Nutzung und Kosten
  - Quality Gate Ergebnisse
  - Agent-zu-Agent Kommunikation
  - Routing-Entscheidungen
  - Alles was die Brain/Memory speichert

Nichts geht verloren. ELON hat Zugriff auf alle Daten.
"""

import time
import traceback
from typing import Optional, Callable
from dataclasses import dataclass, field


@dataclass
class TaskEvent:
    """Ein Event das im System passiert."""
    event_type: str         # task_start, task_end, task_error, routing, quality_check, agent_message
    agent_slug: str
    task_id: Optional[str] = None
    task_type: Optional[str] = None
    model_used: Optional[str] = None
    data: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class DataCollector:
    """
    Automatischer Datensammler.

    Wird als Middleware in die Task-Pipeline eingebaut.
    Jedes Event wird an den Collector gesendet.
    Der Collector speichert alles in Supabase.

    Usage:
        collector = DataCollector(db=supabase_client)

        # Am Anfang eines Tasks:
        await collector.on_task_start(agent="steve", task_id="abc", task_type="content_creation")

        # Am Ende:
        await collector.on_task_end(task_id="abc", result="...", score=0.85)

        # Bei Fehler:
        await collector.on_error(task_id="abc", error=exception)
    """

    def __init__(self, db=None, learning=None):
        self.db = db
        self.learning = learning
        self._active_tasks = {}  # task_id -> start_time
        self._event_hooks = []   # Callbacks fuer externe Listener

    def add_hook(self, callback: Callable):
        """Registriere einen Callback der bei jedem Event aufgerufen wird."""
        self._event_hooks.append(callback)

    async def _emit(self, event: TaskEvent):
        """Sende Event an alle Hooks."""
        for hook in self._event_hooks:
            try:
                await hook(event)
            except Exception:
                pass  # Hooks duerfen nicht die Pipeline blockieren

    # ══════════════════════════════════════
    # TASK LIFECYCLE
    # ══════════════════════════════════════

    async def on_task_start(
        self,
        agent_slug: str,
        task_id: str,
        task_type: str,
        model_used: str = "",
        prompt: str = "",
    ):
        """Task gestartet — Timer starten, Event loggen."""
        self._active_tasks[task_id] = {
            "start_time": time.time(),
            "agent_slug": agent_slug,
            "task_type": task_type,
            "model_used": model_used,
            "prompt": prompt,
        }

        event = TaskEvent(
            event_type="task_start",
            agent_slug=agent_slug,
            task_id=task_id,
            task_type=task_type,
            model_used=model_used,
        )
        await self._emit(event)

        if self.db:
            await self.db.audit(
                agent_slug=agent_slug,
                action="task_start",
                category="task",
                details={
                    "task_id": task_id,
                    "task_type": task_type,
                    "model": model_used,
                },
            )

    async def on_task_end(
        self,
        task_id: str,
        response: str = "",
        score: float = 0.0,
        tokens_input: int = 0,
        tokens_output: int = 0,
        error: Optional[str] = None,
        metadata: dict = None,
    ) -> dict:
        """
        Task beendet — Ergebnis speichern, Metriken berechnen.

        Gibt das gespeicherte TaskOutcome zurueck.
        """
        task_info = self._active_tasks.pop(task_id, {})
        duration_ms = int((time.time() - task_info.get("start_time", time.time())) * 1000)

        # An Self-Learning Engine weiterleiten
        if self.learning:
            from core.learning.self_learning import TaskOutcome, ScoreSource

            outcome = TaskOutcome(
                task_id=task_id,
                agent_slug=task_info.get("agent_slug", "unknown"),
                task_type=task_info.get("task_type", "unknown"),
                model_used=task_info.get("model_used", "unknown"),
                prompt=task_info.get("prompt", ""),
                response=response,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                duration_ms=duration_ms,
                score=score,
                error=error,
                metadata=metadata or {},
            )

            result = await self.learning.record_outcome(outcome)

            event = TaskEvent(
                event_type="task_end",
                agent_slug=task_info.get("agent_slug", "unknown"),
                task_id=task_id,
                task_type=task_info.get("task_type"),
                model_used=task_info.get("model_used"),
                data={
                    "duration_ms": duration_ms,
                    "score": outcome.score,
                    "has_error": error is not None,
                },
            )
            await self._emit(event)

            return result

        return {}

    async def on_error(
        self,
        agent_slug: str,
        task_id: Optional[str] = None,
        error: Optional[Exception] = None,
        error_type: str = "runtime_error",
        error_message: str = "",
        context: dict = None,
        severity: str = "medium",
    ):
        """
        Fehler aufgetreten — in Error Log speichern.

        Wird automatisch aufgerufen bei:
        - Exception waehrend Task-Ausfuehrung
        - Quality Gate Failure
        - Timeout
        - Rate Limit
        """
        msg = error_message or (str(error) if error else "Unknown error")
        ctx = context or {}

        if error:
            ctx["traceback"] = traceback.format_exc()

        if self.db:
            await self.db.log_error({
                "task_id": task_id,
                "agent_slug": agent_slug,
                "error_type": error_type,
                "error_message": msg,
                "error_context": ctx,
                "severity": severity,
            })

            # Memory speichern damit es nicht vergessen wird
            await self.db.store_memory({
                "agent_slug": agent_slug,
                "memory_type": "error",
                "key": f"error_{task_id or 'system'}_{int(time.time())}",
                "value": f"[{error_type}] {msg[:500]}",
                "priority": "high" if severity in ("critical", "high") else "normal",
                "tags": ["error", error_type, severity],
                "metadata": ctx,
            })

        event = TaskEvent(
            event_type="task_error",
            agent_slug=agent_slug,
            task_id=task_id,
            data={"error_type": error_type, "message": msg, "severity": severity},
        )
        await self._emit(event)

    # ══════════════════════════════════════
    # ROUTING EVENTS
    # ══════════════════════════════════════

    async def on_routing_decision(
        self,
        agent_slug: str,
        task_type: str,
        selected_model: str,
        reason: str = "",
        alternatives: list = None,
    ):
        """Routing-Entscheidung loggen — fuer spaetere Analyse durch ELON."""
        if self.db:
            await self.db.audit(
                agent_slug=agent_slug,
                action="routing_decision",
                category="routing",
                details={
                    "task_type": task_type,
                    "selected_model": selected_model,
                    "reason": reason,
                    "alternatives": alternatives or [],
                },
            )

    # ══════════════════════════════════════
    # QUALITY EVENTS
    # ══════════════════════════════════════

    async def on_quality_check(
        self,
        task_id: str,
        agent_slug: str,
        score: float,
        approved: bool,
        details: dict = None,
    ):
        """Quality Gate Ergebnis loggen."""
        if self.db:
            await self.db.audit(
                agent_slug="elon",
                action="quality_check",
                category="quality",
                details={
                    "task_id": task_id,
                    "agent": agent_slug,
                    "score": score,
                    "approved": approved,
                    **(details or {}),
                },
            )

    # ══════════════════════════════════════
    # AGENT COMMUNICATION
    # ══════════════════════════════════════

    async def on_agent_message(
        self,
        from_agent: str,
        to_agent: str,
        message_type: str,
        content: str = "",
    ):
        """Agent-zu-Agent Kommunikation loggen."""
        if self.db:
            await self.db.audit(
                agent_slug=from_agent,
                action="agent_message",
                category="communication",
                details={
                    "from": from_agent,
                    "to": to_agent,
                    "type": message_type,
                    "preview": content[:200],
                },
            )
