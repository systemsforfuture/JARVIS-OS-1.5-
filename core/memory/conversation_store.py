"""
JARVIS 1.5 — Conversation Store
Speichert JEDE Nachricht. JARVIS vergisst NICHTS.

Jede User-Nachricht, jede Agent-Antwort, jedes Tool-Ergebnis
wird persistent in Supabase gespeichert und ist jederzeit
durchsuchbar und abrufbar.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("jarvis.conversation_store")


@dataclass
class Message:
    role: str  # user, assistant, system, tool
    content: str
    agent_slug: str = "jarvis"
    conversation_id: Optional[str] = None
    model_used: Optional[str] = None
    tokens_used: int = 0
    metadata: dict = field(default_factory=dict)
    parent_message_id: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ConversationStore:
    """
    Speichert jede Nachricht in Supabase.
    Ermöglicht: Volltext-Suche, Konversations-History, Agent-Filter.
    """

    def __init__(self, db_client):
        self.db = db_client
        self._current_conversation_id: Optional[str] = None

    # ─── Konversation starten ───

    async def start_conversation(
        self,
        user_id: str = "dom",
        channel: str = "telegram",
        metadata: Optional[dict] = None
    ) -> str:
        conv_id = str(uuid.uuid4())
        self._current_conversation_id = conv_id

        try:
            await self.db.client.table("conversations").insert({
                "id": conv_id,
                "user_id": user_id,
                "channel": channel,
                "metadata": metadata or {},
                "started_at": datetime.now(timezone.utc).isoformat(),
            }).execute()
        except Exception as e:
            logger.warning(f"Could not store conversation start: {e}")

        logger.info(f"Conversation started: {conv_id}")
        return conv_id

    # ─── Nachricht speichern ───

    async def store_message(self, message: Message) -> str:
        if not message.conversation_id:
            if not self._current_conversation_id:
                self._current_conversation_id = await self.start_conversation()
            message.conversation_id = self._current_conversation_id

        try:
            data = {
                "id": message.id,
                "conversation_id": message.conversation_id,
                "agent_slug": message.agent_slug,
                "role": message.role,
                "content": message.content,
                "metadata": message.metadata,
                "tokens_used": message.tokens_used,
                "model_used": message.model_used,
                "parent_message_id": message.parent_message_id,
                "created_at": message.created_at,
            }
            await self.db.client.table("messages").insert(data).execute()
            logger.debug(f"Message stored: {message.role} [{message.agent_slug}]")
        except Exception as e:
            logger.error(f"Failed to store message: {e}")

        return message.id

    # ─── Schnell-Methoden ───

    async def user_says(self, content: str, **kwargs) -> str:
        return await self.store_message(Message(role="user", content=content, **kwargs))

    async def agent_says(self, content: str, agent_slug: str = "jarvis", **kwargs) -> str:
        return await self.store_message(Message(
            role="assistant", content=content, agent_slug=agent_slug, **kwargs
        ))

    async def system_note(self, content: str, **kwargs) -> str:
        return await self.store_message(Message(role="system", content=content, **kwargs))

    async def tool_result(self, content: str, agent_slug: str = "jarvis", **kwargs) -> str:
        return await self.store_message(Message(
            role="tool", content=content, agent_slug=agent_slug, **kwargs
        ))

    # ─── Konversation abrufen ───

    async def get_conversation(
        self,
        conversation_id: Optional[str] = None,
        limit: int = 50
    ) -> list[dict]:
        conv_id = conversation_id or self._current_conversation_id
        if not conv_id:
            return []

        try:
            result = await self.db.client.table("messages") \
                .select("*") \
                .eq("conversation_id", conv_id) \
                .order("created_at", desc=False) \
                .limit(limit) \
                .execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get conversation: {e}")
            return []

    # ─── Letzte N Nachrichten eines Agents ───

    async def get_recent_messages(
        self,
        agent_slug: Optional[str] = None,
        limit: int = 20,
        role: Optional[str] = None
    ) -> list[dict]:
        try:
            query = self.db.client.table("messages").select("*")
            if agent_slug:
                query = query.eq("agent_slug", agent_slug)
            if role:
                query = query.eq("role", role)
            result = await query.order("created_at", desc=True).limit(limit).execute()
            return list(reversed(result.data or []))
        except Exception as e:
            logger.error(f"Failed to get recent messages: {e}")
            return []

    # ─── Volltext-Suche über ALLE Nachrichten ───

    async def search(
        self,
        query: str,
        agent_slug: Optional[str] = None,
        limit: int = 20
    ) -> list[dict]:
        try:
            result = await self.db.client.rpc("search_messages", {
                "search_query": query,
                "agent_filter": agent_slug,
                "max_results": limit
            }).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Message search failed: {e}")
            # Fallback: einfache ILIKE-Suche
            return await self._fallback_search(query, agent_slug, limit)

    async def _fallback_search(
        self, query: str, agent_slug: Optional[str], limit: int
    ) -> list[dict]:
        try:
            q = self.db.client.table("messages").select("*") \
                .ilike("content", f"%{query}%")
            if agent_slug:
                q = q.eq("agent_slug", agent_slug)
            result = await q.order("created_at", desc=True).limit(limit).execute()
            return result.data or []
        except Exception:
            return []

    # ─── Konversation beenden ───

    async def end_conversation(
        self,
        conversation_id: Optional[str] = None,
        summary: Optional[str] = None
    ):
        conv_id = conversation_id or self._current_conversation_id
        if not conv_id:
            return

        try:
            update = {"ended_at": datetime.now(timezone.utc).isoformat()}
            if summary:
                update["summary"] = summary
            await self.db.client.table("conversations") \
                .update(update).eq("id", conv_id).execute()
        except Exception as e:
            logger.warning(f"Could not end conversation: {e}")

        if conv_id == self._current_conversation_id:
            self._current_conversation_id = None

    # ─── Konversations-Zusammenfassung generieren ───

    async def get_conversation_summary(
        self,
        conversation_id: Optional[str] = None
    ) -> dict:
        messages = await self.get_conversation(conversation_id, limit=200)
        if not messages:
            return {"total": 0, "summary": "Keine Nachrichten"}

        user_msgs = [m for m in messages if m.get("role") == "user"]
        agent_msgs = [m for m in messages if m.get("role") == "assistant"]
        agents_involved = list(set(m.get("agent_slug", "jarvis") for m in messages))
        total_tokens = sum(m.get("tokens_used", 0) for m in messages)

        return {
            "conversation_id": conversation_id or self._current_conversation_id,
            "total_messages": len(messages),
            "user_messages": len(user_msgs),
            "agent_messages": len(agent_msgs),
            "agents_involved": agents_involved,
            "total_tokens": total_tokens,
            "first_message": messages[0].get("created_at") if messages else None,
            "last_message": messages[-1].get("created_at") if messages else None,
            "topics": self._extract_topics(messages),
        }

    def _extract_topics(self, messages: list[dict]) -> list[str]:
        """Einfache Topic-Extraktion aus User-Nachrichten."""
        topics = []
        for m in messages:
            if m.get("role") == "user":
                content = m.get("content", "")
                # Erste 100 Zeichen als Topic-Hinweis
                if len(content) > 10:
                    topics.append(content[:100].strip())
        return topics[:10]  # max 10 Topics

    # ─── Alle Konversationen eines Users ───

    async def get_user_conversations(
        self,
        user_id: str = "dom",
        limit: int = 20
    ) -> list[dict]:
        try:
            result = await self.db.client.table("conversations") \
                .select("*") \
                .eq("user_id", user_id) \
                .order("started_at", desc=True) \
                .limit(limit) \
                .execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get user conversations: {e}")
            return []

    # ─── Statistiken ───

    async def get_stats(self) -> dict:
        try:
            total = await self.db.client.table("messages") \
                .select("id", count="exact").execute()
            convs = await self.db.client.table("conversations") \
                .select("id", count="exact").execute()
            return {
                "total_messages": total.count or 0,
                "total_conversations": convs.count or 0,
            }
        except Exception:
            return {"total_messages": 0, "total_conversations": 0}
