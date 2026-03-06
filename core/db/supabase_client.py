"""
JARVIS 1.5 — Supabase Client
SYSTEMS™ · architectofscale.com

Zentraler Datenbank-Client fuer alle Core-Module.
Verbindet sich mit Supabase und stellt CRUD-Operationen bereit.

Jedes Modul (Brain, Learning, ELON) nutzt diesen Client.
Keine direkte DB-Kommunikation in anderen Modulen.
"""

import os
import json
import hashlib
from datetime import datetime, timezone
from typing import Optional


class SupabaseClient:
    """
    Supabase Client Wrapper fuer JARVIS.

    Initialisierung:
        client = SupabaseClient()
        await client.connect()

    Alle Methoden sind async und geben Python-Dicts zurueck.
    """

    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        self.url = url or os.getenv("SUPABASE_URL", "")
        self.key = key or os.getenv("SUPABASE_SERVICE_KEY", "")
        self.client = None

    async def connect(self):
        """Verbinde mit Supabase."""
        try:
            from supabase import create_client
            self.client = create_client(self.url, self.key)
        except ImportError:
            # Fallback: Supabase SDK nicht installiert — nutze REST direkt
            self.client = SupabaseRESTFallback(self.url, self.key)

    # ══════════════════════════════════════
    # TASK OUTCOMES
    # ══════════════════════════════════════

    async def store_task_outcome(self, outcome: dict) -> dict:
        """Speichere ein Task-Ergebnis in task_outcomes."""
        data = {
            "task_id": outcome.get("task_id"),
            "agent_slug": outcome["agent_slug"],
            "task_type": outcome["task_type"],
            "model_used": outcome["model_used"],
            "prompt_hash": hashlib.sha256(
                outcome.get("prompt", "").encode()
            ).hexdigest()[:16],
            "prompt_preview": outcome.get("prompt", "")[:500],
            "response_preview": outcome.get("response", "")[:500],
            "tokens_input": outcome.get("tokens_input", 0),
            "tokens_output": outcome.get("tokens_output", 0),
            "duration_ms": outcome.get("duration_ms", 0),
            "cost_cents": outcome.get("cost_cents", 0),
            "score": outcome.get("score", 0),
            "score_source": outcome.get("score_source", "auto"),
            "error": outcome.get("error"),
            "metadata": outcome.get("metadata", {}),
        }
        return await self._insert("task_outcomes", data)

    async def get_task_outcomes(
        self,
        agent_slug: Optional[str] = None,
        task_type: Optional[str] = None,
        limit: int = 100,
        days: int = 30,
    ) -> list:
        """Hole Task-Outcomes mit Filtern."""
        query = self.client.table("task_outcomes").select("*")
        if agent_slug:
            query = query.eq("agent_slug", agent_slug)
        if task_type:
            query = query.eq("task_type", task_type)
        query = query.gte(
            "created_at",
            datetime.now(timezone.utc).isoformat(),
        ).order("created_at", desc=True).limit(limit)
        result = query.execute()
        return result.data if result.data else []

    async def get_agent_outcomes(self, agent_slug: str, days: int = 7) -> list:
        """Hole alle Outcomes fuer einen Agent der letzten N Tage."""
        result = (
            self.client.table("task_outcomes")
            .select("*")
            .eq("agent_slug", agent_slug)
            .order("created_at", desc=True)
            .limit(500)
            .execute()
        )
        return result.data if result.data else []

    # ══════════════════════════════════════
    # ERROR LOG
    # ══════════════════════════════════════

    async def log_error(self, error: dict) -> dict:
        """Speichere einen Fehler. Wenn gleicher Fehler existiert, erhoehe Counter."""
        # Pruefen ob gleicher Fehler schon existiert
        existing = (
            self.client.table("error_log")
            .select("id, occurrences")
            .eq("agent_slug", error["agent_slug"])
            .eq("error_type", error["error_type"])
            .eq("error_message", error["error_message"])
            .eq("resolved", False)
            .limit(1)
            .execute()
        )

        if existing.data:
            # Gleicher Fehler — Counter erhoehen
            row = existing.data[0]
            return await self._update("error_log", row["id"], {
                "occurrences": row["occurrences"] + 1,
                "last_seen": datetime.now(timezone.utc).isoformat(),
            })

        # Neuer Fehler
        data = {
            "task_id": error.get("task_id"),
            "agent_slug": error["agent_slug"],
            "error_type": error["error_type"],
            "error_message": error["error_message"],
            "error_context": error.get("error_context", {}),
            "severity": error.get("severity", "medium"),
        }
        return await self._insert("error_log", data)

    async def get_unresolved_errors(
        self,
        agent_slug: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> list:
        """Hole alle ungeloesten Fehler."""
        query = (
            self.client.table("error_log")
            .select("*")
            .eq("resolved", False)
            .order("occurrences", desc=True)
        )
        if agent_slug:
            query = query.eq("agent_slug", agent_slug)
        if severity:
            query = query.eq("severity", severity)
        result = query.execute()
        return result.data if result.data else []

    async def resolve_error(self, error_id: str, solution_id: str) -> dict:
        """Markiere einen Fehler als geloest."""
        return await self._update("error_log", error_id, {
            "resolved": True,
            "resolution_id": solution_id,
        })

    # ══════════════════════════════════════
    # ERROR SOLUTIONS (ELON)
    # ══════════════════════════════════════

    async def store_solution(self, solution: dict) -> dict:
        """Speichere eine Fehler-Loesung von ELON."""
        data = {
            "error_id": solution["error_id"],
            "error_type": solution["error_type"],
            "root_cause": solution["root_cause"],
            "solution": solution["solution"],
            "solution_type": solution["solution_type"],
            "implementation": solution.get("implementation", {}),
        }
        return await self._insert("error_solutions", data)

    async def apply_solution(self, solution_id: str, applied_by: str) -> dict:
        """Markiere eine Loesung als angewendet."""
        return await self._update("error_solutions", solution_id, {
            "applied": True,
            "applied_at": datetime.now(timezone.utc).isoformat(),
            "applied_by": applied_by,
        })

    async def rate_solution(self, solution_id: str, effectiveness: float) -> dict:
        """Bewerte die Effektivitaet einer Loesung (0-1)."""
        return await self._update("error_solutions", solution_id, {
            "effectiveness": effectiveness,
        })

    async def get_solutions_for_error_type(self, error_type: str) -> list:
        """Hole alle Loesungen fuer einen Fehlertyp (sortiert nach Effektivitaet)."""
        result = (
            self.client.table("error_solutions")
            .select("*")
            .eq("error_type", error_type)
            .eq("applied", True)
            .order("effectiveness", desc=True)
            .execute()
        )
        return result.data if result.data else []

    # ══════════════════════════════════════
    # PATTERNS
    # ══════════════════════════════════════

    async def upsert_pattern(self, pattern: dict) -> dict:
        """Speichere oder aktualisiere ein Pattern."""
        data = {
            "pattern_key": pattern["pattern_key"],
            "agent_slug": pattern["agent_slug"],
            "task_type": pattern["task_type"],
            "description": pattern.get("description", ""),
            "best_model": pattern.get("best_model"),
            "avg_score": pattern.get("avg_score", 0),
            "avg_duration_ms": pattern.get("avg_duration_ms", 0),
            "avg_cost_cents": pattern.get("avg_cost_cents", 0),
            "occurrences": pattern.get("occurrences", 1),
            "model_scores": pattern.get("model_scores", {}),
            "recommendation": pattern.get("recommendation", ""),
            "last_seen": datetime.now(timezone.utc).isoformat(),
        }
        result = (
            self.client.table("patterns")
            .upsert(data, on_conflict="pattern_key")
            .execute()
        )
        return result.data[0] if result.data else {}

    async def get_pattern(self, agent_slug: str, task_type: str) -> Optional[dict]:
        """Hole Pattern fuer Agent+TaskType."""
        result = (
            self.client.table("patterns")
            .select("*")
            .eq("pattern_key", f"{agent_slug}:{task_type}")
            .eq("status", "active")
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    async def get_all_patterns(self, agent_slug: Optional[str] = None) -> list:
        """Hole alle aktiven Patterns."""
        query = (
            self.client.table("patterns")
            .select("*")
            .eq("status", "active")
            .order("occurrences", desc=True)
        )
        if agent_slug:
            query = query.eq("agent_slug", agent_slug)
        result = query.execute()
        return result.data if result.data else []

    # ══════════════════════════════════════
    # OPTIMIZATIONS (ELON)
    # ══════════════════════════════════════

    async def store_optimization(self, optimization: dict) -> dict:
        """Speichere einen Optimierungsvorschlag."""
        data = {
            "agent_slug": optimization["agent_slug"],
            "category": optimization["category"],
            "title": optimization["title"],
            "current_state": optimization["current_state"],
            "suggested_state": optimization["suggested_state"],
            "expected_impact": optimization.get("expected_impact", ""),
            "confidence": optimization.get("confidence", 0),
            "evidence": optimization.get("evidence", []),
        }
        return await self._insert("optimizations", data)

    async def apply_optimization(
        self,
        opt_id: str,
        result_before: dict,
        approved_by: str = "elon",
    ) -> dict:
        """Markiere Optimierung als angewendet."""
        return await self._update("optimizations", opt_id, {
            "status": "applied",
            "approved_by": approved_by,
            "applied_at": datetime.now(timezone.utc).isoformat(),
            "result_before": result_before,
        })

    async def rate_optimization(self, opt_id: str, result_after: dict, effectiveness: float) -> dict:
        """Bewerte eine angewendete Optimierung."""
        return await self._update("optimizations", opt_id, {
            "result_after": result_after,
            "effectiveness": effectiveness,
        })

    async def get_pending_optimizations(self, agent_slug: Optional[str] = None) -> list:
        """Hole alle vorgeschlagenen Optimierungen."""
        query = (
            self.client.table("optimizations")
            .select("*")
            .eq("status", "proposed")
            .order("confidence", desc=True)
        )
        if agent_slug:
            query = query.eq("agent_slug", agent_slug)
        result = query.execute()
        return result.data if result.data else []

    # ══════════════════════════════════════
    # MEMORY (BRAIN)
    # ══════════════════════════════════════

    async def store_memory(self, memory: dict) -> dict:
        """Speichere einen Memory-Eintrag."""
        # Check ob gleicher Key existiert
        existing = (
            self.client.table("memory")
            .select("id, access_count, confidence")
            .eq("agent_slug", memory["agent_slug"])
            .eq("key", memory["key"])
            .limit(1)
            .execute()
        )

        if existing.data:
            # Update existierend
            row = existing.data[0]
            return await self._update("memory", row["id"], {
                "value": memory["value"],
                "confidence": max(row["confidence"] or 0, memory.get("confidence", 1.0)),
                "metadata": memory.get("metadata", {}),
                "tags": memory.get("tags", []),
            })

        data = {
            "agent_slug": memory["agent_slug"],
            "memory_type": memory["memory_type"],
            "key": memory["key"],
            "value": memory["value"],
            "priority": memory.get("priority", "normal"),
            "confidence": memory.get("confidence", 1.0),
            "tags": memory.get("tags", []),
            "metadata": memory.get("metadata", {}),
            "expires_at": memory.get("expires_at"),
        }
        return await self._insert("memory", data)

    async def recall_memories(
        self,
        agent_slug: str,
        memory_type: Optional[str] = None,
        tags: Optional[list] = None,
        limit: int = 20,
        include_global: bool = True,
    ) -> list:
        """Hole relevante Memories."""
        agents = [agent_slug]
        if include_global and agent_slug != "jarvis":
            agents.append("jarvis")

        query = (
            self.client.table("memory")
            .select("*")
            .in_("agent_slug", agents)
            .order("access_count", desc=True)
            .limit(limit)
        )
        if memory_type:
            query = query.eq("memory_type", memory_type)
        if tags:
            query = query.overlaps("tags", tags)

        result = query.execute()
        memories = result.data if result.data else []

        # Access count erhoehen fuer abgerufene Memories
        for mem in memories:
            await self._update("memory", mem["id"], {
                "access_count": (mem.get("access_count") or 0) + 1,
                "last_accessed": datetime.now(timezone.utc).isoformat(),
            })

        return memories

    async def search_memories(self, agent_slug: str, query_text: str, limit: int = 10) -> list:
        """Textsuche in Memories (nutzt Supabase Full Text Search)."""
        # Supabase unterstuetzt textSearch auf text-Spalten
        result = (
            self.client.table("memory")
            .select("*")
            .or_(f"agent_slug.eq.{agent_slug},agent_slug.eq.jarvis")
            .textSearch("value", query_text, config="german")
            .limit(limit)
            .execute()
        )
        return result.data if result.data else []

    async def cleanup_expired_memories(self) -> int:
        """Loesche abgelaufene Memories."""
        now = datetime.now(timezone.utc).isoformat()
        result = (
            self.client.table("memory")
            .delete()
            .lt("expires_at", now)
            .not_.is_("expires_at", "null")
            .execute()
        )
        return len(result.data) if result.data else 0

    # ══════════════════════════════════════
    # AGENT PERFORMANCE
    # ══════════════════════════════════════

    async def store_performance_snapshot(self, snapshot: dict) -> dict:
        """Speichere einen Performance-Snapshot."""
        return await self._insert("agent_performance", snapshot)

    async def get_performance_history(
        self,
        agent_slug: str,
        periods: int = 12,
    ) -> list:
        """Hole Performance-History fuer einen Agent."""
        result = (
            self.client.table("agent_performance")
            .select("*")
            .eq("agent_slug", agent_slug)
            .order("period_start", desc=True)
            .limit(periods)
            .execute()
        )
        return result.data if result.data else []

    async def update_agent_config(self, agent_slug: str, config: dict) -> dict:
        """Update Agent-Konfiguration (von ELON Optimizer)."""
        result = (
            self.client.table("agents")
            .update({"config": config})
            .eq("slug", agent_slug)
            .execute()
        )
        return result.data[0] if result.data else {}

    async def update_agent_performance(self, agent_slug: str, performance: dict) -> dict:
        """Update Agent Performance-Metriken."""
        result = (
            self.client.table("agents")
            .update({"performance": performance})
            .eq("slug", agent_slug)
            .execute()
        )
        return result.data[0] if result.data else {}

    # ══════════════════════════════════════
    # KPI SNAPSHOTS
    # ══════════════════════════════════════

    async def store_kpi(self, name: str, value: float, target: float = 0, unit: str = "", trend: str = "stable") -> dict:
        """Speichere einen KPI-Wert."""
        data = {
            "kpi_name": name,
            "kpi_value": value,
            "kpi_target": target,
            "kpi_unit": unit,
            "kpi_trend": trend,
        }
        result = (
            self.client.table("kpi_snapshots")
            .upsert(data, on_conflict="snapshot_date,kpi_name")
            .execute()
        )
        return result.data[0] if result.data else {}

    # ══════════════════════════════════════
    # AUDIT LOG
    # ══════════════════════════════════════

    async def audit(self, agent_slug: str, action: str, category: str = "system", details: dict = None) -> dict:
        """Schreibe einen Audit-Log-Eintrag."""
        data = {
            "agent_slug": agent_slug,
            "action": action,
            "category": category,
            "details": details or {},
        }
        return await self._insert("audit_log", data)

    # ══════════════════════════════════════
    # INTERNAL HELPERS
    # ══════════════════════════════════════

    async def _insert(self, table: str, data: dict) -> dict:
        """Insert in eine Tabelle."""
        result = self.client.table(table).insert(data).execute()
        return result.data[0] if result.data else {}

    async def _update(self, table: str, id: str, data: dict) -> dict:
        """Update by ID."""
        result = self.client.table(table).update(data).eq("id", id).execute()
        return result.data[0] if result.data else {}

    async def _delete(self, table: str, id: str) -> bool:
        """Delete by ID."""
        self.client.table(table).delete().eq("id", id).execute()
        return True


class SupabaseRESTFallback:
    """
    Fallback wenn supabase-py nicht installiert ist.
    Nutzt httpx fuer direkte REST-API-Aufrufe.
    """

    def __init__(self, url: str, key: str):
        self.url = url.rstrip("/")
        self.key = key
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def table(self, name: str):
        return RESTTableQuery(self.url, self.headers, name)


class RESTTableQuery:
    """Minimale REST-basierte Query-API als Fallback."""

    def __init__(self, base_url: str, headers: dict, table: str):
        self.base_url = f"{base_url}/rest/v1/{table}"
        self.headers = headers
        self._params = {}
        self._data = None
        self._method = "GET"

    def select(self, columns: str = "*"):
        self._params["select"] = columns
        return self

    def insert(self, data):
        self._data = data
        self._method = "POST"
        return self

    def update(self, data):
        self._data = data
        self._method = "PATCH"
        return self

    def upsert(self, data, on_conflict=""):
        self._data = data
        self._method = "POST"
        self.headers["Prefer"] = "resolution=merge-duplicates,return=representation"
        if on_conflict:
            self._params["on_conflict"] = on_conflict
        return self

    def delete(self):
        self._method = "DELETE"
        return self

    def eq(self, column, value):
        self._params[column] = f"eq.{value}"
        return self

    def in_(self, column, values):
        self._params[column] = f"in.({','.join(values)})"
        return self

    def overlaps(self, column, values):
        self._params[column] = f"ov.{{{','.join(values)}}}"
        return self

    def gte(self, column, value):
        self._params[column] = f"gte.{value}"
        return self

    def lt(self, column, value):
        self._params[column] = f"lt.{value}"
        return self

    def not_(self):
        return self

    def is_(self, column, value):
        self._params[column] = f"is.{value}"
        return self

    def textSearch(self, column, query, config="german"):
        self._params[column] = f"fts({config}).{query}"
        return self

    def order(self, column, desc=False):
        direction = "desc" if desc else "asc"
        self._params["order"] = f"{column}.{direction}"
        return self

    def limit(self, count):
        self.headers["Range"] = f"0-{count - 1}"
        return self

    def execute(self):
        import httpx

        if self._method == "GET":
            resp = httpx.get(self.base_url, headers=self.headers, params=self._params)
        elif self._method == "POST":
            resp = httpx.post(
                self.base_url, headers=self.headers,
                params=self._params, json=self._data,
            )
        elif self._method == "PATCH":
            resp = httpx.patch(
                self.base_url, headers=self.headers,
                params=self._params, json=self._data,
            )
        elif self._method == "DELETE":
            resp = httpx.delete(
                self.base_url, headers=self.headers, params=self._params,
            )
        else:
            resp = None

        data = resp.json() if resp and resp.status_code < 400 else []
        return type("Result", (), {"data": data if isinstance(data, list) else [data]})()
