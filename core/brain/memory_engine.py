"""
JARVIS 1.5 — Brain / Memory Engine (Supabase-Backed)
SYSTEMS™ · architectofscale.com

Das zentrale Gedaechtnis von JARVIS. Alles wird in Supabase gespeichert.
Nichts geht verloren. Jeder Agent hat Zugriff auf relevante Memories.

Memory-Typen:
  - fact:       Harte Fakten (Firmenname, Kontakte, Zahlen)
  - learning:   Gelerntes aus Tasks (Was hat funktioniert?)
  - preference: Praeferenzen von DOM (Schreibstil, Vorlieben)
  - context:    Kontext aus Gespraechen (Worum ging es?)
  - decision:   Getroffene Entscheidungen (Was wurde entschieden?)
  - error:      Fehler und Probleme (Was ist schiefgelaufen?)
  - pattern:    Erkannte Muster (Wiederkehrende Situationen)
  - relation:   Beziehungen (Wer kennt wen? Wer ist Kunde?)

Hierarchie:
  Agent-spezifisch -> Team-Level -> Global (jarvis)

Context Injection:
  Automatisch werden relevante Memories in jeden Task-Prompt
  injiziert. Das ist das Geheimnis warum JARVIS immer den
  richtigen Kontext hat.
"""

import time
from typing import Optional
from enum import Enum


class MemoryType(Enum):
    FACT = "fact"
    LEARNING = "learning"
    PREFERENCE = "preference"
    CONTEXT = "context"
    DECISION = "decision"
    ERROR = "error"
    PATTERN = "pattern"
    RELATION = "relation"


class MemoryPriority(Enum):
    CRITICAL = "critical"     # Nie vergessen
    HIGH = "high"             # 1 Jahr
    NORMAL = "normal"         # 30 Tage
    LOW = "low"               # 7 Tage
    EPHEMERAL = "ephemeral"   # 24 Stunden


# TTL in Sekunden nach Prioritaet
TTL_MAP = {
    MemoryPriority.CRITICAL: None,
    MemoryPriority.HIGH: 365 * 24 * 3600,
    MemoryPriority.NORMAL: 30 * 24 * 3600,
    MemoryPriority.LOW: 7 * 24 * 3600,
    MemoryPriority.EPHEMERAL: 24 * 3600,
}


class MemoryEngine:
    """
    Zentrales Gedaechtnis-System — gespeichert in Supabase.

    Jeder store() und recall() geht direkt in die Datenbank.
    Kein In-Memory-Cache noetig — Supabase ist schnell genug.

    Features:
    1. Hierarchisches Speichern (Agent -> Global)
    2. Relevanz-basiertes Abrufen (Prioritaet + Zugriffshaeufigkeit)
    3. Automatisches Vergessen (TTL basierend auf Prioritaet)
    4. Assoziatives Erinnern (Tags + Textsuche)
    5. Context Injection in Task-Prompts
    """

    def __init__(self, db=None):
        """
        Args:
            db: SupabaseClient Instanz
        """
        self.db = db

    async def store(
        self,
        agent_slug: str,
        memory_type: MemoryType,
        key: str,
        value: str,
        priority: MemoryPriority = MemoryPriority.NORMAL,
        tags: list = None,
        metadata: dict = None,
        confidence: float = 1.0,
    ) -> dict:
        """
        Speichere einen Memory-Eintrag in Supabase.

        Wenn der Key schon existiert, wird er aktualisiert (Upsert).
        TTL wird automatisch basierend auf Prioritaet gesetzt.
        """
        # TTL berechnen
        ttl = TTL_MAP.get(priority)
        expires_at = None
        if ttl:
            from datetime import datetime, timezone, timedelta
            expires_at = (datetime.now(timezone.utc) + timedelta(seconds=ttl)).isoformat()

        if not self.db:
            return {}

        return await self.db.store_memory({
            "agent_slug": agent_slug,
            "memory_type": memory_type.value,
            "key": key,
            "value": value,
            "priority": priority.value,
            "confidence": confidence,
            "tags": tags or [],
            "metadata": metadata or {},
            "expires_at": expires_at,
        })

    async def recall(
        self,
        agent_slug: str,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[list] = None,
        limit: int = 20,
        include_global: bool = True,
    ) -> list:
        """
        Erinnere dich an relevante Memories.

        Sucht:
        1. Agent-spezifische Memories
        2. Globale Memories (agent=jarvis) wenn include_global=True

        Sortiert nach Zugriffshaeufigkeit (meistgenutzt = relevanteste).
        """
        if not self.db:
            return []

        return await self.db.recall_memories(
            agent_slug=agent_slug,
            memory_type=memory_type.value if memory_type else None,
            tags=tags,
            limit=limit,
            include_global=include_global,
        )

    async def search(self, agent_slug: str, query: str, limit: int = 10) -> list:
        """
        Volltextsuche in Memories.
        Nutzt Supabase Full Text Search (German config).
        """
        if not self.db:
            return []
        return await self.db.search_memories(agent_slug, query, limit)

    async def forget(self, agent_slug: str, key: str) -> bool:
        """Vergesse einen spezifischen Memory-Eintrag."""
        if not self.db:
            return False
        memories = await self.db.recall_memories(agent_slug=agent_slug, limit=1000)
        for m in memories:
            if m.get("key") == key:
                await self.db._delete("memory", m["id"])
                return True
        return False

    async def cleanup(self) -> int:
        """Loesche abgelaufene Memories."""
        if not self.db:
            return 0
        return await self.db.cleanup_expired_memories()

    async def get_agent_knowledge(self, agent_slug: str) -> dict:
        """Hole das gesamte Wissen eines Agents als strukturiertes Dict."""
        knowledge = {}

        for mem_type in MemoryType:
            memories = await self.recall(
                agent_slug=agent_slug,
                memory_type=mem_type,
                limit=50,
                include_global=False,
            )
            key = mem_type.value + "s"
            knowledge[key] = [
                {
                    "key": m.get("key", ""),
                    "value": m.get("value", ""),
                    "confidence": m.get("confidence", 1.0),
                    "access_count": m.get("access_count", 0),
                }
                for m in memories
            ]

        return knowledge

    async def inject_context(self, agent_slug: str, task_prompt: str) -> str:
        """
        Automatisch relevanten Kontext in einen Task-Prompt injizieren.

        Sucht nach relevanten Memories per Textsuche und fuegt
        sie als Kontext-Block vor dem eigentlichen Prompt ein.

        Das ist das Geheimnis warum JARVIS immer den richtigen Kontext hat.
        """
        if not self.db:
            return task_prompt

        # 1. Textsuche fuer relevante Memories
        search_results = await self.search(agent_slug, task_prompt, limit=5)

        # 2. Fakten und Praeferenzen laden (immer relevant)
        facts = await self.recall(
            agent_slug=agent_slug,
            memory_type=MemoryType.FACT,
            limit=5,
        )
        preferences = await self.recall(
            agent_slug=agent_slug,
            memory_type=MemoryType.PREFERENCE,
            limit=3,
        )

        # 3. Error-Memories laden (damit gleiche Fehler vermieden werden)
        error_memories = await self.recall(
            agent_slug=agent_slug,
            memory_type=MemoryType.ERROR,
            limit=3,
        )

        # Deduplizieren
        all_memories = []
        seen_keys = set()

        for m in search_results + facts + preferences + error_memories:
            key = m.get("key", "")
            if key not in seen_keys:
                seen_keys.add(key)
                all_memories.append(m)

        if not all_memories:
            return task_prompt

        # Kontext-Block aufbauen
        context_parts = []
        for mem in all_memories:
            mtype = mem.get("memory_type", "fact")
            labels = {
                "fact": "FAKT",
                "learning": "GELERNT",
                "preference": "PRAEFERENZ",
                "context": "KONTEXT",
                "decision": "ENTSCHEIDUNG",
                "error": "FEHLER-VERMEIDUNG",
                "pattern": "MUSTER",
                "relation": "BEZIEHUNG",
            }
            label = labels.get(mtype, "INFO")
            context_parts.append(f"[{label}] {mem.get('key', '')}: {mem.get('value', '')}")

        context_block = "\n".join(context_parts)

        return f"""--- KONTEXT AUS JARVIS BRAIN ---
{context_block}
--- ENDE KONTEXT ---

{task_prompt}"""

    async def store_learning(
        self,
        agent_slug: str,
        what_happened: str,
        what_learned: str,
        tags: list = None,
    ):
        """Shortcut: Ein Learning speichern."""
        return await self.store(
            agent_slug=agent_slug,
            memory_type=MemoryType.LEARNING,
            key=f"learning_{int(time.time())}",
            value=f"Was passiert: {what_happened}. Was gelernt: {what_learned}",
            priority=MemoryPriority.HIGH,
            tags=tags or ["learning"],
        )

    async def store_error_prevention(
        self,
        agent_slug: str,
        error_description: str,
        prevention: str,
    ):
        """Shortcut: Fehler-Vermeidung speichern (von ELON nach Fehler-Loesung)."""
        return await self.store(
            agent_slug=agent_slug,
            memory_type=MemoryType.ERROR,
            key=f"prevent_{int(time.time())}",
            value=f"FEHLER: {error_description}. VERMEIDUNG: {prevention}",
            priority=MemoryPriority.CRITICAL,
            tags=["error", "prevention"],
        )
