"""
JARVIS 1.5 — Knowledge Base
Langzeit-Wissen: Fakten, Entscheidungen, Kontakte, Regeln.

JARVIS speichert jedes Fakt, jede Entscheidung, jede Präferenz.
Altes Wissen wird nie gelöscht — nur als superseded markiert.
Beziehungen zwischen Entitäten werden als Knowledge Graph gespeichert.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger("jarvis.knowledge_base")

VALID_CATEGORIES = {
    "fact", "decision", "preference", "procedure",
    "contact", "product", "client", "project",
    "rule", "insight", "goal", "metric"
}


@dataclass
class KnowledgeEntry:
    category: str
    subject: str
    predicate: str
    object: str
    confidence: float = 1.0
    source: Optional[str] = None
    source_message_id: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    agent_slug: Optional[str] = None
    valid_until: Optional[str] = None


class KnowledgeBase:
    """
    Langzeit-Wissens-Speicher.
    Subject-Predicate-Object Triplets mit Versionierung.
    """

    def __init__(self, db_client):
        self.db = db_client

    # ─── Wissen speichern ───

    async def learn(self, entry: KnowledgeEntry) -> str:
        if entry.category not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category: {entry.category}")

        # Prüfe ob es bereits bestehendes Wissen zum gleichen Thema gibt
        existing = await self._find_existing(
            entry.subject, entry.predicate, entry.agent_slug
        )

        knowledge_id = str(uuid.uuid4())

        try:
            data = {
                "id": knowledge_id,
                "category": entry.category,
                "subject": entry.subject,
                "predicate": entry.predicate,
                "object": entry.object,
                "confidence": entry.confidence,
                "source": entry.source,
                "source_message_id": entry.source_message_id,
                "tags": entry.tags,
                "agent_slug": entry.agent_slug,
                "valid_until": entry.valid_until,
            }
            await self.db.client.table("knowledge").insert(data).execute()

            # Altes Wissen als superseded markieren
            if existing:
                await self.db.client.table("knowledge") \
                    .update({"superseded_by": knowledge_id}) \
                    .eq("id", existing["id"]) \
                    .execute()
                logger.info(
                    f"Knowledge updated: {entry.subject} | "
                    f"{entry.predicate} = {entry.object} "
                    f"(supersedes {existing['id'][:8]})"
                )
            else:
                logger.info(
                    f"Knowledge stored: {entry.subject} | "
                    f"{entry.predicate} = {entry.object}"
                )
        except Exception as e:
            logger.error(f"Failed to store knowledge: {e}")

        return knowledge_id

    # ─── Schnell-Methoden ───

    async def learn_fact(self, subject: str, predicate: str, obj: str, **kwargs) -> str:
        return await self.learn(KnowledgeEntry(
            category="fact", subject=subject, predicate=predicate, object=obj, **kwargs
        ))

    async def learn_decision(self, subject: str, decision: str, reason: str, **kwargs) -> str:
        return await self.learn(KnowledgeEntry(
            category="decision", subject=subject, predicate=decision,
            object=reason, **kwargs
        ))

    async def learn_preference(self, subject: str, pref: str, value: str, **kwargs) -> str:
        return await self.learn(KnowledgeEntry(
            category="preference", subject=subject, predicate=pref,
            object=value, **kwargs
        ))

    async def learn_contact(self, name: str, info_type: str, value: str, **kwargs) -> str:
        return await self.learn(KnowledgeEntry(
            category="contact", subject=name, predicate=info_type,
            object=value, **kwargs
        ))

    async def learn_rule(self, context: str, rule: str, details: str, **kwargs) -> str:
        return await self.learn(KnowledgeEntry(
            category="rule", subject=context, predicate=rule,
            object=details, **kwargs
        ))

    # ─── Wissen abrufen ───

    async def recall(
        self,
        subject: Optional[str] = None,
        category: Optional[str] = None,
        agent_slug: Optional[str] = None,
        tags: Optional[list[str]] = None,
        limit: int = 20
    ) -> list[dict]:
        try:
            query = self.db.client.table("knowledge") \
                .select("*") \
                .is_("superseded_by", "null")

            if subject:
                query = query.ilike("subject", f"%{subject}%")
            if category:
                query = query.eq("category", category)
            if agent_slug:
                query = query.or_(
                    f"agent_slug.eq.{agent_slug},agent_slug.is.null"
                )
            if tags:
                query = query.contains("tags", tags)

            result = await query \
                .order("confidence", desc=True) \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()

            # Access count erhöhen
            for entry in (result.data or []):
                await self._mark_accessed(entry["id"])

            return result.data or []
        except Exception as e:
            logger.error(f"Knowledge recall failed: {e}")
            return []

    # ─── Volltext-Suche ───

    async def search(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 20
    ) -> list[dict]:
        try:
            result = await self.db.client.rpc("search_knowledge", {
                "search_query": query,
                "cat_filter": category,
                "max_results": limit
            }).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Knowledge search failed: {e}")
            return await self._fallback_search(query, category, limit)

    async def _fallback_search(self, query: str, category: Optional[str], limit: int):
        try:
            q = self.db.client.table("knowledge").select("*") \
                .is_("superseded_by", "null") \
                .or_(
                    f"subject.ilike.%{query}%,"
                    f"predicate.ilike.%{query}%,"
                    f"object.ilike.%{query}%"
                )
            if category:
                q = q.eq("category", category)
            result = await q.order("confidence", desc=True).limit(limit).execute()
            return result.data or []
        except Exception:
            return []

    # ─── Alles über ein Thema ───

    async def everything_about(self, subject: str) -> dict:
        facts = await self.recall(subject=subject)
        relationships = await self.get_relationships(subject)

        organized = {}
        for f in facts:
            cat = f.get("category", "unknown")
            if cat not in organized:
                organized[cat] = []
            organized[cat].append({
                "predicate": f["predicate"],
                "value": f["object"],
                "confidence": f["confidence"],
                "source": f.get("source"),
            })

        return {
            "subject": subject,
            "knowledge": organized,
            "relationships": relationships,
            "total_facts": len(facts),
        }

    # ─── Beziehungen (Knowledge Graph) ───

    async def add_relationship(
        self,
        entity_a: str,
        entity_a_type: str,
        relation: str,
        entity_b: str,
        entity_b_type: str,
        strength: float = 1.0,
        metadata: Optional[dict] = None,
        source: Optional[str] = None
    ) -> str:
        rel_id = str(uuid.uuid4())
        try:
            await self.db.client.table("entity_relationships").upsert({
                "id": rel_id,
                "entity_a": entity_a,
                "entity_a_type": entity_a_type,
                "relation": relation,
                "entity_b": entity_b,
                "entity_b_type": entity_b_type,
                "strength": strength,
                "metadata": metadata or {},
                "source": source,
            }, on_conflict="entity_a,relation,entity_b").execute()
            logger.info(f"Relationship: {entity_a} --[{relation}]--> {entity_b}")
        except Exception as e:
            logger.error(f"Failed to store relationship: {e}")
        return rel_id

    async def get_relationships(
        self,
        entity: str,
        relation: Optional[str] = None
    ) -> list[dict]:
        try:
            # Beziehungen in beide Richtungen suchen
            q_a = self.db.client.table("entity_relationships") \
                .select("*").ilike("entity_a", f"%{entity}%")
            q_b = self.db.client.table("entity_relationships") \
                .select("*").ilike("entity_b", f"%{entity}%")

            if relation:
                q_a = q_a.eq("relation", relation)
                q_b = q_b.eq("relation", relation)

            result_a = await q_a.execute()
            result_b = await q_b.execute()

            all_rels = (result_a.data or []) + (result_b.data or [])
            # Deduplizieren
            seen = set()
            unique = []
            for r in all_rels:
                if r["id"] not in seen:
                    seen.add(r["id"])
                    unique.append(r)
            return unique
        except Exception as e:
            logger.error(f"Failed to get relationships: {e}")
            return []

    # ─── Kontext für Prompt-Injection ───

    async def get_context_for_task(
        self,
        task_description: str,
        agent_slug: Optional[str] = None,
        max_entries: int = 15
    ) -> str:
        """Generiert Wissens-Kontext für eine Aufgabe."""
        relevant = await self.search(task_description, limit=max_entries)

        if not relevant:
            return ""

        lines = ["=== BEKANNTES WISSEN ==="]
        for entry in relevant:
            line = f"- {entry['subject']}: {entry['predicate']} → {entry['object']}"
            if entry.get("confidence", 1.0) < 0.8:
                line += f" (Konfidenz: {entry['confidence']:.0%})"
            lines.append(line)

        return "\n".join(lines)

    # ─── Statistiken ───

    async def get_stats(self) -> dict:
        try:
            total = await self.db.client.table("knowledge") \
                .select("id", count="exact") \
                .is_("superseded_by", "null").execute()
            rels = await self.db.client.table("entity_relationships") \
                .select("id", count="exact").execute()
            return {
                "active_knowledge_entries": total.count or 0,
                "relationships": rels.count or 0,
            }
        except Exception:
            return {"active_knowledge_entries": 0, "relationships": 0}

    # ─── Interne Helfer ───

    async def _find_existing(
        self, subject: str, predicate: str, agent_slug: Optional[str]
    ) -> Optional[dict]:
        try:
            query = self.db.client.table("knowledge") \
                .select("*") \
                .eq("subject", subject) \
                .eq("predicate", predicate) \
                .is_("superseded_by", "null")
            if agent_slug:
                query = query.eq("agent_slug", agent_slug)
            else:
                query = query.is_("agent_slug", "null")
            result = await query.limit(1).execute()
            return result.data[0] if result.data else None
        except Exception:
            return None

    async def _mark_accessed(self, knowledge_id: str):
        try:
            await self.db.client.table("knowledge").update({
                "access_count": "access_count + 1",  # Supabase increment
                "last_accessed": datetime.now(timezone.utc).isoformat()
            }).eq("id", knowledge_id).execute()
        except Exception:
            pass
