"""
JARVIS 1.5 — Context Manager
Das Gehirn hinter jeder Antwort.

VOR jeder Antwort assembliert der Context Manager relevanten Kontext
aus ALLEN Quellen:
  1. Aktuelle Konversation (letzte N Nachrichten)
  2. Relevantes Langzeit-Wissen (Knowledge Base)
  3. Relevante Erinnerungen (Memory Engine)
  4. Lern-Journal (vergangene Erfolge/Fehler)
  5. Agent-spezifische Daten
  6. Aktuelle KPIs und Performance

Das Ergebnis wird in den System-Prompt injiziert.
JARVIS vergisst NICHTS — der Context Manager sorgt dafür.
"""

import logging
from typing import Optional

logger = logging.getLogger("jarvis.context_manager")


class ContextManager:
    """
    Assembliert vor jeder Agent-Antwort den optimalen Kontext.
    Ziel: Der Agent hat IMMER alle relevanten Informationen.
    """

    def __init__(
        self,
        conversation_store,
        knowledge_base,
        memory_engine,
        db_client
    ):
        self.conversations = conversation_store
        self.knowledge = knowledge_base
        self.memory = memory_engine
        self.db = db_client

    async def build_context(
        self,
        task_description: str,
        agent_slug: str = "jarvis",
        conversation_id: Optional[str] = None,
        include_conversation: bool = True,
        include_knowledge: bool = True,
        include_memories: bool = True,
        include_learnings: bool = True,
        include_kpis: bool = False,
        max_conversation_messages: int = 20,
        max_knowledge_entries: int = 15,
        max_memories: int = 10,
        max_learnings: int = 10,
    ) -> str:
        """
        Baut den kompletten Kontext für einen Agent-Call.
        Wird VOR jeder LLM-Anfrage aufgerufen.
        """
        sections = []

        # ─── 1. Konversations-Historie ───
        if include_conversation:
            conv_context = await self._get_conversation_context(
                conversation_id, max_conversation_messages
            )
            if conv_context:
                sections.append(conv_context)

        # ─── 2. Relevantes Wissen ───
        if include_knowledge:
            knowledge_context = await self._get_knowledge_context(
                task_description, agent_slug, max_knowledge_entries
            )
            if knowledge_context:
                sections.append(knowledge_context)

        # ─── 3. Erinnerungen ───
        if include_memories:
            memory_context = await self._get_memory_context(
                task_description, agent_slug, max_memories
            )
            if memory_context:
                sections.append(memory_context)

        # ─── 4. Lern-Journal ───
        if include_learnings:
            learning_context = await self._get_learning_context(
                task_description, agent_slug, max_learnings
            )
            if learning_context:
                sections.append(learning_context)

        # ─── 5. KPIs ───
        if include_kpis:
            kpi_context = await self._get_kpi_context(agent_slug)
            if kpi_context:
                sections.append(kpi_context)

        if not sections:
            return ""

        full_context = "\n\n".join(sections)

        # Kontext-Snapshot speichern für Debugging/Replay
        await self._save_snapshot(agent_slug, conversation_id, full_context)

        logger.info(
            f"Context built for {agent_slug}: "
            f"{len(sections)} sections, {len(full_context)} chars"
        )
        return full_context

    # ─── Konversations-Kontext ───

    async def _get_conversation_context(
        self, conversation_id: Optional[str], limit: int
    ) -> str:
        try:
            messages = await self.conversations.get_conversation(
                conversation_id, limit=limit
            )
            if not messages:
                return ""

            lines = ["═══ AKTUELLE KONVERSATION ═══"]
            for msg in messages[-limit:]:
                role = msg.get("role", "?")
                agent = msg.get("agent_slug", "")
                content = msg.get("content", "")
                # Kürzen wenn nötig
                if len(content) > 500:
                    content = content[:500] + "..."

                if role == "user":
                    lines.append(f"USER: {content}")
                elif role == "assistant":
                    prefix = f"[{agent.upper()}]" if agent != "jarvis" else "JARVIS"
                    lines.append(f"{prefix}: {content}")
                elif role == "tool":
                    lines.append(f"TOOL ({agent}): {content[:200]}")

            return "\n".join(lines)
        except Exception as e:
            logger.warning(f"Could not load conversation context: {e}")
            return ""

    # ─── Wissens-Kontext ───

    async def _get_knowledge_context(
        self, task: str, agent_slug: str, limit: int
    ) -> str:
        try:
            context = await self.knowledge.get_context_for_task(
                task, agent_slug=agent_slug, max_entries=limit
            )
            return context
        except Exception as e:
            logger.warning(f"Could not load knowledge context: {e}")
            return ""

    # ─── Memory-Kontext ───

    async def _get_memory_context(
        self, task: str, agent_slug: str, limit: int
    ) -> str:
        try:
            # Relevante Memories suchen
            memories = await self.memory.search(task, limit=limit)
            if not memories:
                return ""

            lines = ["═══ RELEVANTE ERINNERUNGEN ═══"]
            for mem in memories:
                mtype = mem.get("memory_type", "")
                content = mem.get("content", "")
                priority = mem.get("priority", "normal")
                if priority in ("critical", "high"):
                    lines.append(f"⚠ [{mtype.upper()}] {content}")
                else:
                    lines.append(f"- [{mtype}] {content}")

            return "\n".join(lines)
        except Exception as e:
            logger.warning(f"Could not load memory context: {e}")
            return ""

    # ─── Lern-Journal Kontext ───

    async def _get_learning_context(
        self, task: str, agent_slug: str, limit: int
    ) -> str:
        try:
            # Relevante Learnings aus dem Journal suchen
            result = await self.db.client.table("learning_journal") \
                .select("*") \
                .eq("agent_slug", agent_slug) \
                .order("impact_score", desc=True) \
                .limit(limit) \
                .execute()

            entries = result.data or []
            if not entries:
                return ""

            lines = ["═══ VERGANGENE LEARNINGS ═══"]
            for entry in entries:
                event = entry.get("event_type", "")
                title = entry.get("title", "")
                lesson = entry.get("lesson_learned", "")
                times = entry.get("times_applied", 0)

                if lesson:
                    lines.append(
                        f"- [{event}] {title}: {lesson}"
                        f"{f' (angewendet: {times}x)' if times > 0 else ''}"
                    )
                else:
                    lines.append(f"- [{event}] {title}")

            return "\n".join(lines)
        except Exception as e:
            logger.warning(f"Could not load learning context: {e}")
            return ""

    # ─── KPI Kontext ───

    async def _get_kpi_context(self, agent_slug: str) -> str:
        try:
            result = await self.db.client.table("kpi_snapshots") \
                .select("*") \
                .order("snapshot_date", desc=True) \
                .limit(1) \
                .execute()

            if not result.data:
                return ""

            kpi = result.data[0]
            metrics = kpi.get("metrics", {})

            lines = ["═══ AKTUELLE KPIs ═══"]
            for key, value in metrics.items():
                lines.append(f"- {key}: {value}")

            return "\n".join(lines)
        except Exception as e:
            logger.warning(f"Could not load KPI context: {e}")
            return ""

    # ─── Snapshot für Debugging ───

    async def _save_snapshot(
        self,
        agent_slug: str,
        conversation_id: Optional[str],
        context: str
    ):
        try:
            await self.db.client.table("context_snapshots").insert({
                "agent_slug": agent_slug,
                "conversation_id": conversation_id,
                "snapshot_type": "checkpoint",
                "active_context": {"context_text": context[:5000]},
                "summary": context[:200],
            }).execute()
        except Exception:
            pass  # Snapshot ist nice-to-have, kein Fehler wenn es nicht klappt

    # ─── Zusammenfassung erstellen ───

    async def summarize_session(
        self,
        conversation_id: Optional[str] = None
    ) -> str:
        summary = await self.conversations.get_conversation_summary(conversation_id)
        knowledge_stats = await self.knowledge.get_stats()

        return (
            f"Session: {summary.get('total_messages', 0)} Nachrichten, "
            f"{len(summary.get('agents_involved', []))} Agents beteiligt. "
            f"Wissensbasis: {knowledge_stats.get('active_knowledge_entries', 0)} Einträge, "
            f"{knowledge_stats.get('relationships', 0)} Beziehungen."
        )
