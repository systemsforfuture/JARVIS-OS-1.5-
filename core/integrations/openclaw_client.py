"""
JARVIS 1.5 — OpenClaw Client
Manages agent configurations in OpenClaw from Python.

Features:
  - CRUD operations for agents
  - Sync agent configs (prompts, models, tools)
  - Health check
  - Batch operations
"""

import os
import logging
from typing import Optional

logger = logging.getLogger("jarvis.openclaw")


class OpenClawClient:
    """
    Client for OpenClaw API.
    Manages agents, prompts, and tools programmatically.
    """

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or os.getenv("OPENCLAW_URL", "http://localhost:8080")).rstrip("/")
        self._client = None

    async def _get_client(self):
        if not self._client:
            import httpx
            self._client = httpx.AsyncClient(timeout=30)
        return self._client

    async def health_check(self) -> dict:
        """Check if OpenClaw is reachable."""
        client = await self._get_client()
        for endpoint in ["/api/health", "/health", "/api/v1/health"]:
            try:
                resp = await client.get(f"{self.base_url}{endpoint}")
                if resp.status_code < 400:
                    return {"status": "ok", "endpoint": endpoint}
            except Exception:
                continue
        return {"status": "unreachable"}

    async def get_agents(self) -> list:
        """List all agents in OpenClaw."""
        client = await self._get_client()
        for endpoint in ["/api/agents", "/api/v1/agents", "/agents"]:
            try:
                resp = await client.get(f"{self.base_url}{endpoint}")
                if resp.status_code < 400:
                    return resp.json()
            except Exception:
                continue
        return []

    async def get_agent(self, slug: str) -> Optional[dict]:
        """Get single agent config from OpenClaw."""
        client = await self._get_client()
        for endpoint in [f"/api/agents/{slug}", f"/api/v1/agents/{slug}", f"/agents/{slug}"]:
            try:
                resp = await client.get(f"{self.base_url}{endpoint}")
                if resp.status_code < 400:
                    return resp.json()
            except Exception:
                continue
        return None

    async def upsert_agent(self, agent_config: dict) -> dict:
        """
        Create or update an agent in OpenClaw.
        Tries PUT then POST on multiple endpoints.

        agent_config should include:
          slug, name, role, model, system_prompt, tools, config
        """
        client = await self._get_client()
        slug = agent_config.get("slug", "")

        # Try PUT first (update)
        put_endpoints = [
            f"/api/agents/{slug}",
            f"/api/v1/agents/{slug}",
            f"/agents/{slug}",
        ]
        for endpoint in put_endpoints:
            try:
                resp = await client.put(
                    f"{self.base_url}{endpoint}",
                    json=agent_config,
                )
                if resp.status_code < 400:
                    logger.info(f"OpenClaw: updated agent '{slug}' via PUT {endpoint}")
                    return {"synced": True, "method": "PUT", "endpoint": endpoint}
            except Exception:
                continue

        # Try POST (create)
        post_endpoints = ["/api/agents", "/api/v1/agents"]
        for endpoint in post_endpoints:
            try:
                resp = await client.post(
                    f"{self.base_url}{endpoint}",
                    json=agent_config,
                )
                if resp.status_code < 400:
                    logger.info(f"OpenClaw: created agent '{slug}' via POST {endpoint}")
                    return {"synced": True, "method": "POST", "endpoint": endpoint}
            except Exception:
                continue

        logger.warning(f"OpenClaw: could not sync agent '{slug}'")
        return {"synced": False, "error": "All endpoints failed"}

    async def delete_agent(self, slug: str) -> bool:
        """Remove an agent from OpenClaw."""
        client = await self._get_client()
        for endpoint in [f"/api/agents/{slug}", f"/api/v1/agents/{slug}"]:
            try:
                resp = await client.delete(f"{self.base_url}{endpoint}")
                if resp.status_code < 400:
                    return True
            except Exception:
                continue
        return False

    async def sync_all_agents(self, agents: list) -> dict:
        """
        Sync a list of agent configs to OpenClaw.
        Returns summary of results.
        """
        results = []
        for agent in agents:
            result = await self.upsert_agent(agent)
            results.append({
                "slug": agent.get("slug"),
                "synced": result.get("synced", False),
            })

        synced = sum(1 for r in results if r["synced"])
        logger.info(f"OpenClaw: synced {synced}/{len(results)} agents")

        return {
            "total": len(results),
            "synced": synced,
            "failed": len(results) - synced,
            "details": results,
        }

    async def build_agent_config(
        self,
        slug: str,
        name: str,
        role: str,
        model: str = "tier1-sonnet",
        system_prompt: str = "",
        tools: list = None,
        temperature: float = 0.5,
        max_tokens: int = 4096,
    ) -> dict:
        """Build a standardized agent config payload."""
        from core.llm.llm_client import MODEL_MAP

        return {
            "slug": slug,
            "name": name,
            "role": role,
            "model": model,
            "resolved_model": MODEL_MAP.get(model, model),
            "system_prompt": system_prompt,
            "tools": tools or [],
            "config": {
                "temperature": temperature,
                "max_tokens": max_tokens,
                "litellm_url": os.getenv("LITELLM_URL", "http://jarvis-litellm:4000"),
            },
        }

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
