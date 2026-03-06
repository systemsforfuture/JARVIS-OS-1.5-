"""
JARVIS 1.5 — Smart Router
Highest quality at lowest cost.

Routing Strategy:
  - JARVIS + ELON: Sonnet (strategic, short outputs, save tokens)
  - Team Leaders (STEVE, DONALD, ARCHI, DONNA, IRIS, FELIX): Sonnet (quality work)
  - Sub-agents / Workers: Ollama local (0 EUR) for routine tasks
  - Groq: Speed tasks (classification, quick checks)

Leaders delegate routine tasks to Ollama workers automatically.
Leaders handle quality tasks themselves on Sonnet.
"""

import logging
from typing import Optional

logger = logging.getLogger("jarvis.router")


# ── Agent → Default Model Mapping ─────────────────────────
AGENT_MODELS = {
    # Boss-Level: Sonnet, short outputs
    "jarvis": "tier1-sonnet",
    "elon": "tier1-sonnet",
    # Team Leaders: Sonnet for quality
    "steve": "tier1-sonnet",
    "donald": "tier1-sonnet",
    "archi": "tier1-sonnet",
    "donna": "tier1-haiku",  # Backoffice can use Haiku (cheaper)
    "iris": "tier1-sonnet",
    "felix": "tier1-haiku",  # Support can use Haiku
    "andreas": "tier1-haiku",
    # Standby
    "satoshi": "tier1-sonnet",
}

# ── Task Complexity Classification ─────────────────────────
ROUTINE_TASKS = {
    # These get routed to Ollama (free)
    "hashtag_research", "keyword_research", "data_entry", "email_categorize",
    "lead_research", "crm_update", "template_fill", "formatting",
    "translation", "summarize", "test_write", "lint", "docs_write",
    "benchmark_lookup", "competitor_list", "health_score_calc",
    "ticket_categorize", "faq_answer", "schedule_check", "asset_resize",
    "seo_check", "price_check", "report_generate", "calendar_check",
    "invoice_parse", "data_extract", "content_schedule",
}

QUALITY_TASKS = {
    # These stay on Sonnet (paid, high quality)
    "strategy", "content_write", "cold_email", "proposal",
    "architecture", "security_review", "code_review", "design_decision",
    "churn_intervention", "upsell_strategy", "brand_design",
    "playbook_write", "battle_card", "coaching", "negotiation",
    "error_analysis", "optimization", "root_cause", "system_design",
    "compliance_decision", "contract_review",
}

SPEED_TASKS = {
    # These go to Groq (fast, cheap)
    "classify", "sentiment", "detect_intent", "quick_answer",
    "tag", "prioritize", "route", "validate",
}


class SmartRouter:
    """
    Routes tasks to the optimal model based on:
    1. Agent role (boss vs leader vs worker)
    2. Task complexity (routine vs quality vs speed)
    3. Cost optimization (Ollama for routine = 0 EUR)
    4. Token efficiency (bosses output less)
    """

    def __init__(self, db_client=None):
        self.db = db_client
        self._pattern_cache = {}

    def route(
        self,
        agent_slug: str,
        task_type: Optional[str] = None,
        task_description: str = "",
        force_model: Optional[str] = None,
    ) -> dict:
        """
        Determine optimal model and parameters for a task.

        Returns:
            {
                "model": "tier1-sonnet" | "tier2-llama" | "tier3-groq-fast",
                "max_tokens": int,
                "temperature": float,
                "delegated": bool,  # True if routed to Ollama worker
                "reason": str,
            }
        """
        # Forced model override
        if force_model:
            return {
                "model": force_model,
                "max_tokens": 4096,
                "temperature": 0.5,
                "delegated": False,
                "reason": f"forced: {force_model}",
            }

        # ── Step 1: Classify task complexity ───
        complexity = self._classify_task(task_type, task_description)

        # ── Step 2: Route based on complexity ───
        if complexity == "routine":
            return {
                "model": "tier2-llama",
                "max_tokens": 2048,
                "temperature": 0.3,
                "delegated": True,
                "reason": f"routine task → Ollama (0 EUR)",
            }

        if complexity == "speed":
            return {
                "model": "tier3-groq-fast",
                "max_tokens": 1024,
                "temperature": 0.2,
                "delegated": False,
                "reason": "speed task → Groq",
            }

        # ── Step 3: Quality tasks — agent-specific routing ───
        agent_model = AGENT_MODELS.get(agent_slug, "tier1-sonnet")

        # Boss agents: limit output tokens to save money
        if agent_slug in ("jarvis", "elon"):
            return {
                "model": agent_model,
                "max_tokens": 2048,  # Short outputs, save tokens
                "temperature": 0.4,
                "delegated": False,
                "reason": f"boss agent → {agent_model} (short output)",
            }

        # Team leaders: full quality
        return {
            "model": agent_model,
            "max_tokens": 4096,
            "temperature": self._get_temperature(agent_slug),
            "delegated": False,
            "reason": f"quality task → {agent_model}",
        }

    def should_delegate_to_worker(
        self,
        agent_slug: str,
        task_type: Optional[str] = None,
        task_description: str = "",
    ) -> bool:
        """Check if a team leader should delegate this task to an Ollama worker."""
        complexity = self._classify_task(task_type, task_description)
        return complexity == "routine"

    def get_worker_config(self, agent_slug: str) -> dict:
        """Get config for an Ollama worker under a team leader."""
        return {
            "model": "tier2-llama",
            "max_tokens": 2048,
            "temperature": 0.3,
            "parent_agent": agent_slug,
        }

    def _classify_task(
        self, task_type: Optional[str], description: str
    ) -> str:
        """Classify task as routine, quality, or speed."""
        # Explicit task type
        if task_type:
            if task_type in ROUTINE_TASKS:
                return "routine"
            if task_type in QUALITY_TASKS:
                return "quality"
            if task_type in SPEED_TASKS:
                return "speed"

        # Heuristic from description
        desc_lower = description.lower()

        routine_keywords = [
            "recherchiere", "liste", "formatiere", "zusammenfassung",
            "hashtag", "keyword", "template", "crm update", "kategorisier",
            "health score", "faq", "termin check", "resize", "translate",
            "benchmark", "schedule", "invoice", "extract", "parse",
        ]
        quality_keywords = [
            "strateg", "schreib", "erstell", "analysier", "optimier",
            "review", "entscheid", "design", "architektur", "security",
            "verhandl", "coaching", "playbook", "proposal", "brand",
            "churn", "upsell", "cold email", "content",
        ]
        speed_keywords = [
            "klassifizier", "kategorisier", "priorisier", "validier",
            "detect", "sentiment", "quick", "schnell",
        ]

        routine_score = sum(1 for kw in routine_keywords if kw in desc_lower)
        quality_score = sum(1 for kw in quality_keywords if kw in desc_lower)
        speed_score = sum(1 for kw in speed_keywords if kw in desc_lower)

        if speed_score > routine_score and speed_score > quality_score:
            return "speed"
        if routine_score > quality_score:
            return "routine"
        return "quality"

    def _get_temperature(self, agent_slug: str) -> float:
        """Get optimal temperature per agent."""
        temps = {
            "jarvis": 0.3, "elon": 0.4, "steve": 0.7,
            "donald": 0.5, "archi": 0.3, "donna": 0.4,
            "iris": 0.8, "satoshi": 0.2, "felix": 0.6,
            "andreas": 0.5,
        }
        return temps.get(agent_slug, 0.5)

    async def learn_from_outcome(
        self,
        agent_slug: str,
        task_type: str,
        model_used: str,
        score: float,
    ):
        """Learn from task outcomes to improve routing over time."""
        if not self.db:
            return
        try:
            cache_key = f"{agent_slug}:{task_type}"
            if cache_key not in self._pattern_cache:
                self._pattern_cache[cache_key] = []
            self._pattern_cache[cache_key].append({
                "model": model_used, "score": score,
            })

            # If we have enough data, check if a cheaper model performs well
            entries = self._pattern_cache[cache_key]
            if len(entries) >= 10:
                ollama_entries = [e for e in entries if "tier2" in e["model"]]
                sonnet_entries = [e for e in entries if "tier1" in e["model"]]

                if ollama_entries and sonnet_entries:
                    ollama_avg = sum(e["score"] for e in ollama_entries) / len(ollama_entries)
                    sonnet_avg = sum(e["score"] for e in sonnet_entries) / len(sonnet_entries)

                    # If Ollama performs within 10% of Sonnet, prefer Ollama
                    if ollama_avg >= sonnet_avg * 0.9:
                        logger.info(
                            f"SmartRouter: {cache_key} can use Ollama "
                            f"(score {ollama_avg:.2f} vs Sonnet {sonnet_avg:.2f})"
                        )
        except Exception as e:
            logger.debug(f"SmartRouter learn error: {e}")
