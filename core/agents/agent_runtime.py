"""
JARVIS 1.5 — Agent Runtime
Der Wrapper um JEDEN Agent-Call.

Jeder Agent-Aufruf durchläuft diese Pipeline:
  1. PRE-CALL: Kontext laden (Memories, Wissen, Learnings, Konversation)
  2. PRE-CALL: System-Prompt assemblieren (Base + Agent + Kontext)
  3. CALL: LLM aufrufen (über Smart Router)
  4. POST-CALL: Qualitätsprüfung (ELON Quality Gate)
  5. POST-CALL: Nachricht speichern (Conversation Store)
  6. POST-CALL: Outcome loggen (Self-Learning)
  7. POST-CALL: Wissen extrahieren und speichern
  8. POST-CALL: Auto-Improver benachrichtigen

KEIN Agent-Call geht am Runtime vorbei.
So lernt JARVIS aus JEDER Interaktion.
"""

import time
import uuid
import logging
import traceback
from datetime import datetime, timezone
from typing import Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger("jarvis.agent_runtime")


@dataclass
class AgentCall:
    agent_slug: str
    task_description: str
    task_type: str = "general"
    conversation_id: Optional[str] = None
    user_id: str = "dom"
    channel: str = "telegram"
    metadata: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class AgentResponse:
    content: str
    agent_slug: str
    model_used: str = "unknown"
    tokens_used: int = 0
    duration_ms: int = 0
    quality_score: float = 0.0
    cost_cents: float = 0.0
    context_used: str = ""
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class AgentRuntime:
    """
    Zentraler Runtime für alle Agent-Calls.
    Stellt sicher dass Memory, Learning und Quality bei JEDEM Call aktiv sind.
    """

    def __init__(
        self,
        context_manager,
        conversation_store,
        knowledge_base,
        learning_engine,
        learning_journal,
        elon_engine,
        data_collector,
        auto_improver,
        prompt_loader=None,
        smart_router=None,
        llm_client=None,
    ):
        self.context = context_manager
        self.conversations = conversation_store
        self.knowledge = knowledge_base
        self.learning = learning_engine
        self.journal = learning_journal
        self.elon = elon_engine
        self.collector = data_collector
        self.improver = auto_improver
        self.prompts = prompt_loader
        self.router = smart_router
        self.llm = llm_client

    async def execute(self, call: AgentCall) -> AgentResponse:
        """
        Haupteinstiegspunkt für jeden Agent-Call.
        Durchläuft die komplette Intelligence-Pipeline.
        """
        start_time = time.time()
        task_id = call.id

        logger.info(f"[{call.agent_slug}] Task started: {call.task_description[:80]}...")

        # ─── 1. Konversation sicherstellen ───
        if not call.conversation_id:
            call.conversation_id = await self.conversations.start_conversation(
                user_id=call.user_id, channel=call.channel
            )

        # ─── 2. User-Nachricht speichern ───
        await self.conversations.user_says(
            content=call.task_description,
            conversation_id=call.conversation_id,
        )

        # ─── 3. Data Collector: Task Start ───
        await self.collector.on_task_start(
            task_id=task_id,
            agent_slug=call.agent_slug,
            task_description=call.task_description,
        )

        try:
            # ─── 4. Kontext assemblieren ───
            context = await self.context.build_context(
                task_description=call.task_description,
                agent_slug=call.agent_slug,
                conversation_id=call.conversation_id,
                include_kpis=(call.agent_slug == "elon"),
            )

            # ─── 5. System-Prompt bauen ───
            system_prompt = await self._build_system_prompt(call, context)

            # ─── 6. Relevante Learnings laden ───
            learnings_context = await self.journal.get_context_string(call.agent_slug)
            if learnings_context:
                system_prompt += f"\n\n{learnings_context}"

            # ─── 7. Model auswählen (Smart Router) ───
            model = await self._select_model(call)

            # ─── 8. LLM aufrufen ───
            llm_response = await self._call_llm(
                system_prompt=system_prompt,
                user_message=call.task_description,
                model=model,
                agent_slug=call.agent_slug,
            )

            duration_ms = int((time.time() - start_time) * 1000)

            # ─── 9. Quality Gate ───
            quality_score = await self._quality_check(
                call, llm_response["content"], duration_ms
            )

            # ─── 10. Response bauen ───
            response = AgentResponse(
                content=llm_response["content"],
                agent_slug=call.agent_slug,
                model_used=model,
                tokens_used=llm_response.get("tokens", 0),
                duration_ms=duration_ms,
                quality_score=quality_score,
                cost_cents=llm_response.get("cost_cents", 0),
                context_used=context[:500],
                metadata=call.metadata,
            )

            # ─── 11. Agent-Antwort speichern ───
            await self.conversations.agent_says(
                content=response.content,
                agent_slug=call.agent_slug,
                conversation_id=call.conversation_id,
                model_used=model,
                tokens_used=response.tokens_used,
            )

            # ─── 12. Wissen extrahieren ───
            await self._extract_knowledge(call, response)

            # ─── 13. Outcome loggen ───
            await self._log_outcome(call, response)

            # ─── 14. Auto-Improver benachrichtigen ───
            await self.improver.on_task_completed()

            logger.info(
                f"[{call.agent_slug}] Task done: "
                f"{duration_ms}ms, score={quality_score:.2f}, "
                f"model={model}"
            )

            return response

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)

            logger.error(f"[{call.agent_slug}] Task failed: {error_msg}")

            # Fehler loggen
            await self.collector.on_error(
                task_id=task_id,
                agent_slug=call.agent_slug,
                error=e,
                context={"task": call.task_description},
            )

            # Fehler im Journal speichern
            await self.journal.log_failure(
                agent_slug=call.agent_slug,
                title=f"Task fehlgeschlagen: {call.task_description[:50]}",
                what_failed=call.task_description[:200],
                root_cause=error_msg,
                context={"traceback": traceback.format_exc()[:500]},
            )

            return AgentResponse(
                content=f"Fehler bei der Verarbeitung. Ich versuche einen anderen Ansatz.",
                agent_slug=call.agent_slug,
                duration_ms=duration_ms,
                error=error_msg,
            )

    # ─── System-Prompt bauen ───

    async def _build_system_prompt(self, call: AgentCall, context: str) -> str:
        """Assembliert den kompletten System-Prompt."""
        parts = []

        # Base prompt + Agent prompt laden
        if self.prompts:
            try:
                config = self.prompts.load_agent_config(call.agent_slug)
                parts.append(config.get("system_prompt", ""))
            except Exception:
                parts.append(f"Du bist {call.agent_slug} im JARVIS System.")
        else:
            parts.append(f"Du bist {call.agent_slug} im JARVIS System.")

        # Kontext einfügen
        if context:
            parts.append(context)

        # Datum & Meta
        parts.append(
            f"\n═══ AKTUELL ═══\n"
            f"Datum: {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M UTC')}\n"
            f"Agent: {call.agent_slug}\n"
            f"Task-ID: {call.id}\n"
            f"Kanal: {call.channel}"
        )

        return "\n\n".join(parts)

    # ─── Model Selection ───

    async def _select_model(self, call: AgentCall) -> str:
        """Wählt das beste Model über den Smart Router."""
        if self.router:
            try:
                route = await self.router.route(
                    agent_slug=call.agent_slug,
                    task_type=call.task_type,
                    task_description=call.task_description,
                )
                return route.get("model", "ollama/llama3")
            except Exception:
                pass

        # Fallback: Default-Modelle pro Agent
        defaults = {
            "jarvis": "kimi/k2.5",
            "elon": "claude/sonnet",
            "steve": "claude/sonnet",
            "archi": "claude/sonnet",
            "donald": "ollama/llama3",
            "donna": "ollama/llama3",
            "iris": "claude/haiku",
            "felix": "ollama/llama3",
            "satoshi": "groq/llama3",
            "andreas": "ollama/llama3",
        }
        return defaults.get(call.agent_slug, "ollama/llama3")

    # ─── LLM Call ───

    async def _call_llm(
        self,
        system_prompt: str,
        user_message: str,
        model: str,
        agent_slug: str,
    ) -> dict:
        """
        Ruft das LLM auf über den LLM Client (LiteLLM-basiert).
        Automatischer Fallback wenn ein Model nicht erreichbar ist.
        """
        if self.llm:
            try:
                response = await self.llm.complete(
                    system_prompt=system_prompt,
                    user_message=user_message,
                    model=model,
                    agent_slug=agent_slug,
                )
                return {
                    "content": response.content,
                    "tokens": response.tokens_input + response.tokens_output,
                    "cost_cents": response.cost_cents,
                }
            except Exception as e:
                logger.error(f"LLM call failed ({model}): {e}")
                raise

        # Fallback: Direkt über litellm (ohne LLMClient-Wrapper)
        try:
            import litellm
            from core.llm.llm_client import MODEL_MAP
            resolved = MODEL_MAP.get(model, model)
            response = await litellm.acompletion(
                model=resolved,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=4096,
            )
            content = response.choices[0].message.content or ""
            usage = response.usage
            return {
                "content": content,
                "tokens": (usage.prompt_tokens + usage.completion_tokens) if usage else 0,
                "cost_cents": 0.0,
            }
        except ImportError:
            logger.warning("litellm not available — returning error")
            raise RuntimeError("Kein LLM-Client konfiguriert. Bitte LiteLLM installieren.")

    # ─── Quality Check ───

    async def _quality_check(
        self,
        call: AgentCall,
        response_content: str,
        duration_ms: int
    ) -> float:
        """ELON Quality Gate."""
        try:
            report = await self.elon.quality_gate(
                agent_slug=call.agent_slug,
                task_description=call.task_description,
                response=response_content,
            )
            return report.get("total_score", 0.7) if isinstance(report, dict) else 0.7
        except Exception:
            return 0.7  # Default score wenn Quality Gate nicht erreichbar

    # ─── Wissen extrahieren ───

    async def _extract_knowledge(self, call: AgentCall, response: AgentResponse):
        """
        Extrahiert automatisch Wissen aus der Konversation.
        Speichert Fakten, Entscheidungen, Präferenzen in der Knowledge Base.
        """
        try:
            # Einfache Heuristik: Wenn User eine Entscheidung trifft
            content = call.task_description.lower()

            if any(word in content for word in ["ich will", "wir machen", "entscheidung", "beschlossen"]):
                await self.knowledge.learn_decision(
                    subject=f"Task {call.id[:8]}",
                    decision=call.task_description[:100],
                    reason=response.content[:200],
                    source="auto_extract",
                    agent_slug=call.agent_slug,
                )

            # Wenn es eine Korrektur ist
            if any(word in content for word in ["nein", "falsch", "nicht so", "korrigier"]):
                await self.journal.log_correction(
                    agent_slug=call.agent_slug,
                    title=f"Korrektur in {call.agent_slug}",
                    original="Vorherige Antwort",
                    corrected=call.task_description[:200],
                )

        except Exception:
            pass  # Knowledge-Extraction ist nice-to-have

    # ─── Outcome loggen ───

    async def _log_outcome(self, call: AgentCall, response: AgentResponse):
        """Speichert das Task-Ergebnis für Self-Learning."""
        try:
            from core.learning.self_learning import TaskOutcome
            outcome = TaskOutcome(
                task_id=call.id,
                agent_slug=call.agent_slug,
                task_type=call.task_type,
                task_description=call.task_description[:200],
                model_used=response.model_used,
                response=response.content[:500],
                tokens_used=response.tokens_used,
                duration_ms=response.duration_ms,
                cost_cents=response.cost_cents,
                error=response.error,
            )
            await self.learning.record_outcome(outcome)
        except Exception as e:
            logger.warning(f"Could not log outcome: {e}")

    # ─── Batch-Ausführung ───

    async def execute_batch(self, calls: list[AgentCall]) -> list[AgentResponse]:
        """Führt mehrere Agent-Calls sequentiell aus."""
        responses = []
        for call in calls:
            response = await self.execute(call)
            responses.append(response)
        return responses

    # ─── Agent an Agent Delegation ───

    async def delegate(
        self,
        from_agent: str,
        to_agent: str,
        task: str,
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> AgentResponse:
        """Ein Agent delegiert eine Aufgabe an einen anderen."""
        logger.info(f"Delegation: {from_agent} → {to_agent}: {task[:50]}...")

        # Delegation im Journal loggen
        await self.journal.log(
            agent_slug=from_agent,
            event_type="discovery",
            title=f"Delegation an {to_agent}",
            description=f"Task: {task[:200]}",
            applies_to=[from_agent, to_agent],
            impact_score=0.3,
        )

        call = AgentCall(
            agent_slug=to_agent,
            task_description=task,
            conversation_id=conversation_id,
            metadata={"delegated_from": from_agent, **kwargs},
        )
        return await self.execute(call)
