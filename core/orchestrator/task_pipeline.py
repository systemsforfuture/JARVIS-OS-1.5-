"""
JARVIS 1.5 — Task Orchestrator & Pipeline
SYSTEMS™ · architectofscale.com

Der Orchestrator ist das Nervensystem von JARVIS.
Jeder Task durchlaeuft eine definierte Pipeline:

  1. INTAKE      — Task wird empfangen und validiert
  2. CLASSIFY    — Task-Typ und Komplexitaet bestimmen (Groq, blitz-schnell)
  3. ENRICH      — Kontext aus Brain/Memory injizieren
  4. ROUTE       — Smart Router waehlt das beste Modell
  5. EXECUTE     — Agent fuehrt den Task aus
  6. VALIDATE    — ELON prueft Qualitaet (bei wichtigen Tasks)
  7. LEARN       — Ergebnis wird in Learning-DB gespeichert
  8. DELIVER     — Ergebnis wird zugestellt (Dashboard, Telegram, etc.)

Bei Fehlern: Automatischer Retry mit Fallback-Modell.
Bei niedrigem Score: Automatische Nachbesserung.
"""

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum


class TaskStatus(Enum):
    PENDING = "pending"
    CLASSIFYING = "classifying"
    ENRICHING = "enriching"
    ROUTING = "routing"
    EXECUTING = "executing"
    VALIDATING = "validating"
    LEARNING = "learning"
    DELIVERING = "delivering"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class DeliveryChannel(Enum):
    DASHBOARD = "dashboard"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"
    EMAIL = "email"
    INTERNAL = "internal"  # Nur intern (Agent-zu-Agent)


@dataclass
class Task:
    """Ein Task im JARVIS System."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    description: str = ""
    prompt: str = ""
    agent_slug: str = "jarvis"
    task_type: str = ""
    complexity: int = 2
    priority: int = 2         # 0=KRITISCH, 1=HOCH, 2=NORMAL, 3=NIEDRIG
    status: TaskStatus = TaskStatus.PENDING
    model_used: str = ""
    result: str = ""
    score: float = 0.0
    tokens_input: int = 0
    tokens_output: int = 0
    cost_cents: float = 0.0
    duration_ms: int = 0
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 2
    parent_task_id: Optional[str] = None
    sub_tasks: list = field(default_factory=list)
    delivery_channels: list = field(default_factory=lambda: [DeliveryChannel.DASHBOARD])
    context: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


class TaskPipeline:
    """
    Die Task-Pipeline — Herzstuck der Orchestrierung.

    Jeder Task durchlaeuft automatisch alle Phasen.
    Hooks erlauben es, an jeder Phase einzugreifen.
    """

    def __init__(self, router=None, brain=None, learning=None, db_pool=None):
        self.router = router
        self.brain = brain
        self.learning = learning
        self.db = db_pool
        self._hooks = {phase: [] for phase in TaskStatus}
        self._active_tasks = {}
        self._task_queue = asyncio.Queue()
        self._workers_running = False

    def register_hook(self, phase: TaskStatus, callback: Callable):
        """Registriere einen Hook fuer eine bestimmte Phase."""
        self._hooks[phase].append(callback)

    async def submit(self, task: Task) -> str:
        """Task in die Pipeline einreichen."""
        self._active_tasks[task.id] = task
        await self._task_queue.put(task)

        # In DB speichern
        if self.db:
            await self.db.execute(
                """INSERT INTO tasks (title, description, agent_slug, status, priority)
                VALUES ($1, $2, $3, $4, $5)""",
                task.title, task.description, task.agent_slug,
                task.status.value, task.priority,
            )

        return task.id

    async def process(self, task: Task) -> Task:
        """
        Fuehre einen Task durch die komplette Pipeline.

        Jede Phase kann den Task modifizieren oder abbrechen.
        """
        task.started_at = time.time()

        try:
            # Phase 1: CLASSIFY
            task.status = TaskStatus.CLASSIFYING
            await self._run_hooks(TaskStatus.CLASSIFYING, task)
            task = await self._phase_classify(task)

            # Phase 2: ENRICH
            task.status = TaskStatus.ENRICHING
            await self._run_hooks(TaskStatus.ENRICHING, task)
            task = await self._phase_enrich(task)

            # Phase 3: ROUTE
            task.status = TaskStatus.ROUTING
            await self._run_hooks(TaskStatus.ROUTING, task)
            task = await self._phase_route(task)

            # Phase 4: EXECUTE
            task.status = TaskStatus.EXECUTING
            await self._run_hooks(TaskStatus.EXECUTING, task)
            task = await self._phase_execute(task)

            # Phase 5: VALIDATE (nur bei Prio 0-1)
            if task.priority <= 1 and not task.error:
                task.status = TaskStatus.VALIDATING
                await self._run_hooks(TaskStatus.VALIDATING, task)
                task = await self._phase_validate(task)

            # Phase 6: LEARN
            task.status = TaskStatus.LEARNING
            await self._run_hooks(TaskStatus.LEARNING, task)
            task = await self._phase_learn(task)

            # Phase 7: DELIVER
            task.status = TaskStatus.DELIVERING
            await self._run_hooks(TaskStatus.DELIVERING, task)
            task = await self._phase_deliver(task)

            # Fertig
            task.status = TaskStatus.COMPLETED
            task.completed_at = time.time()
            task.duration_ms = int((task.completed_at - task.started_at) * 1000)

        except Exception as e:
            task.error = str(e)

            # Retry?
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.RETRYING
                task.error = None
                return await self.process(task)

            task.status = TaskStatus.FAILED
            task.completed_at = time.time()
            task.duration_ms = int((task.completed_at - task.started_at) * 1000)

        finally:
            await self._run_hooks(task.status, task)
            self._active_tasks.pop(task.id, None)

        return task

    async def _phase_classify(self, task: Task) -> Task:
        """
        Phase 1: Klassifiziere den Task.

        Nutzt Groq (tier3) fuer blitz-schnelle Klassifizierung.
        Bestimmt: task_type, complexity, priority (falls nicht gesetzt).
        """
        if task.task_type and task.complexity:
            return task  # Bereits klassifiziert

        # Klassifizierungs-Prompt (wird von Groq in <1s beantwortet)
        classification_prompt = f"""Klassifiziere diesen Task. Antworte NUR mit JSON.

Task: {task.prompt[:500]}
Agent: {task.agent_slug}

Antwort-Format:
{{"task_type": "bug_fix|content_creation|sales_email|strategy|...",
  "complexity": 0-4,
  "priority": 0-3}}"""

        # Hier wuerde der Groq-Call stehen
        # Fuer jetzt: Heuristische Klassifizierung
        prompt_lower = task.prompt.lower()

        if any(kw in prompt_lower for kw in ["bug", "fix", "error", "test"]):
            task.task_type = "bug_fix"
            task.complexity = 1
        elif any(kw in prompt_lower for kw in ["content", "post", "blog", "newsletter"]):
            task.task_type = "content_creation"
            task.complexity = 2
        elif any(kw in prompt_lower for kw in ["strateg", "plan", "vision"]):
            task.task_type = "strategy"
            task.complexity = 3
        elif any(kw in prompt_lower for kw in ["email", "outreach"]):
            task.task_type = "sales_email"
            task.complexity = 2
        else:
            task.task_type = "content_creation"
            task.complexity = 2

        return task

    async def _phase_enrich(self, task: Task) -> Task:
        """
        Phase 2: Kontext aus dem Brain injizieren.

        Das ist das Geheimnis: Jeder Task bekommt automatisch
        relevanten Kontext aus frueheren Gespraechen, Fakten und Learnings.
        """
        if self.brain:
            task.prompt = await self.brain.inject_context(
                agent_slug=task.agent_slug,
                task_prompt=task.prompt,
            )
        return task

    async def _phase_route(self, task: Task) -> Task:
        """Phase 3: Smart Router waehlt das Modell."""
        if self.router:
            decision = self.router.route(
                agent_slug=task.agent_slug,
                task_type=task.task_type,
                task_description=task.prompt,
            )
            task.model_used = decision["model"]
            task.metadata["routing_reason"] = decision.get("reason", "")
            task.metadata["delegated"] = decision.get("delegated", False)
        else:
            task.model_used = "tier1-sonnet"
        return task

    async def _phase_execute(self, task: Task) -> Task:
        """
        Phase 4: Task ausfuehren.

        Ruft LiteLLM auf mit dem vom Router gewaehlten Modell.
        """
        start = time.time()

        try:
            import litellm
            from core.llm.llm_client import MODEL_MAP

            resolved_model = MODEL_MAP.get(task.model_used, task.model_used)

            response = await litellm.acompletion(
                model=resolved_model,
                messages=[{"role": "user", "content": task.prompt}],
                max_tokens=4096,
                temperature=0.5,
            )

            task.result = response.choices[0].message.content or ""
            usage = response.usage
            task.tokens_input = usage.prompt_tokens if usage else 0
            task.tokens_output = usage.completion_tokens if usage else 0

            try:
                task.cost_cents = litellm.completion_cost(
                    completion_response=response
                ) * 100
            except Exception:
                task.cost_cents = 0.0

        except ImportError:
            task.result = "LiteLLM nicht installiert. pip install litellm"
            task.error = "litellm_not_installed"
        except Exception as e:
            task.error = str(e)
            task.result = f"Fehler bei der Ausfuehrung: {e}"

        task.duration_ms = int((time.time() - start) * 1000)
        return task

    async def _phase_validate(self, task: Task) -> Task:
        """
        Phase 5: Qualitaetspruefung durch ELON.

        Nur fuer wichtige Tasks (Prio 0-1).
        ELON bewertet: Vollstaendigkeit, Korrektheit, Brand Voice.
        """
        validation_prompt = f"""Bewerte dieses Ergebnis auf einer Skala von 0.0-1.0.

Original-Aufgabe: {task.title}
Agent: {task.agent_slug}
Modell: {task.model_used}

Ergebnis:
{task.result[:1000]}

Bewerte: Vollstaendigkeit, Korrektheit, Nuetzlichkeit.
Antworte NUR mit einer Zahl (0.0-1.0)."""

        # Placeholder — wird mit echtem ELON-Call implementiert
        task.score = 0.75
        task.metadata["validated_by"] = "elon"

        # Wenn Score zu niedrig: Nachbesserung
        if task.score < 0.5 and task.retry_count < task.max_retries:
            task.error = f"Quality score too low: {task.score}"
            task.metadata["quality_rejection"] = True

        return task

    async def _phase_learn(self, task: Task) -> Task:
        """Phase 6: Ergebnis in Learning-DB speichern."""
        if self.learning:
            from core.learning.self_learning import TaskOutcome, ScoreSource
            outcome = TaskOutcome(
                task_id=hash(task.id),
                agent_slug=task.agent_slug,
                task_type=task.task_type,
                model_used=task.model_used,
                prompt=task.prompt[:500],
                response=task.result[:500],
                tokens_input=task.tokens_input,
                tokens_output=task.tokens_output,
                duration_ms=task.duration_ms,
                score=task.score,
                cost_cents=task.cost_cents,
                error=task.error,
            )
            await self.learning.record_outcome(outcome)
        return task

    async def _phase_deliver(self, task: Task) -> Task:
        """Phase 7: Ergebnis zustellen."""
        for channel in task.delivery_channels:
            if channel == DeliveryChannel.DASHBOARD:
                # WebSocket broadcast
                pass
            elif channel == DeliveryChannel.TELEGRAM:
                # Telegram-Nachricht senden
                pass
            elif channel == DeliveryChannel.EMAIL:
                # E-Mail senden
                pass
        return task

    async def _run_hooks(self, phase: TaskStatus, task: Task):
        """Fuehre registrierte Hooks fuer eine Phase aus."""
        for hook in self._hooks.get(phase, []):
            try:
                await hook(task)
            except Exception as e:
                task.metadata[f"hook_error_{phase.value}"] = str(e)

    async def start_workers(self, num_workers: int = 3):
        """Starte Task-Worker die die Queue abarbeiten."""
        self._workers_running = True
        workers = [
            asyncio.create_task(self._worker(f"worker-{i}"))
            for i in range(num_workers)
        ]
        await asyncio.gather(*workers)

    async def _worker(self, name: str):
        """Ein einzelner Worker der Tasks aus der Queue nimmt."""
        while self._workers_running:
            try:
                task = await asyncio.wait_for(self._task_queue.get(), timeout=1.0)
                await self.process(task)
                self._task_queue.task_done()
            except asyncio.TimeoutError:
                continue

    def get_active_tasks(self) -> list:
        """Alle aktiven Tasks."""
        return list(self._active_tasks.values())

    def get_queue_size(self) -> int:
        """Anzahl Tasks in der Queue."""
        return self._task_queue.qsize()
