"""
JARVIS 1.5 — Skill Installer
SYSTEMS™ · architectofscale.com

Laedt alle Skills aus dem Manifest und installiert sie automatisch in OpenClaw.
Wird beim JARVIS-Start ausgefuehrt.

Flow:
  1. skills_manifest.json laden
  2. Fuer jeden Agenten: Skills + shared_skills zusammenfuegen
  3. Agent-Config mit Skills an OpenClaw pushen (upsert)
  4. Ergebnis in DB loggen

So hat jeder Agent beim Start sofort alle Tools verfuegbar.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("jarvis.skills")

MANIFEST_PATH = Path(__file__).parent.parent.parent / "config" / "openclaw" / "skills_manifest.json"


class SkillInstaller:
    """
    Installiert alle Skills aus dem Manifest in OpenClaw.
    Jeder Agent bekommt seine spezifischen + alle shared Skills.
    """

    def __init__(self, openclaw_client=None, db_client=None, prompt_loader=None):
        self.openclaw = openclaw_client
        self.db = db_client
        self.prompts = prompt_loader
        self.manifest = None
        self._installed_count = 0
        self._failed_count = 0

    async def load_manifest(self) -> dict:
        """Lade das Skills-Manifest."""
        manifest_path = os.getenv("SKILLS_MANIFEST_PATH", str(MANIFEST_PATH))
        try:
            with open(manifest_path, "r") as f:
                self.manifest = json.load(f)
            logger.info(f"Skills manifest loaded: {len(self.manifest.get('agent_skills', {}))} agents")
            return self.manifest
        except FileNotFoundError:
            logger.error(f"Skills manifest not found: {manifest_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in skills manifest: {e}")
            return {}

    async def install_all(self) -> dict:
        """
        Installiere alle Skills fuer alle Agenten in OpenClaw.
        Haupteinstiegspunkt — wird beim JARVIS-Start aufgerufen.
        """
        if not self.manifest:
            await self.load_manifest()

        if not self.manifest:
            return {"installed": 0, "failed": 0, "error": "No manifest"}

        if not self.openclaw:
            logger.warning("No OpenClaw client — skills stored locally only")
            return await self._store_locally()

        # OpenClaw erreichbar?
        health = await self.openclaw.health_check()
        if health.get("status") != "ok":
            logger.warning("OpenClaw not reachable — skills stored locally")
            return await self._store_locally()

        results = []
        agent_skills = self.manifest.get("agent_skills", {})
        shared_skills = self.manifest.get("shared_skills", {}).get("skills", [])

        for agent_slug, agent_data in agent_skills.items():
            try:
                result = await self._install_agent_skills(
                    agent_slug=agent_slug,
                    agent_data=agent_data,
                    shared_skills=shared_skills,
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to install skills for {agent_slug}: {e}")
                results.append({"agent": agent_slug, "synced": False, "error": str(e)})
                self._failed_count += 1

        summary = {
            "installed": self._installed_count,
            "failed": self._failed_count,
            "agents": len(results),
            "total_skills": sum(r.get("skill_count", 0) for r in results),
            "details": results,
        }

        logger.info(
            f"Skills installed: {summary['total_skills']} skills "
            f"across {summary['agents']} agents "
            f"({self._installed_count} synced, {self._failed_count} failed)"
        )

        # In DB loggen
        await self._log_installation(summary)

        return summary

    async def _install_agent_skills(
        self,
        agent_slug: str,
        agent_data: dict,
        shared_skills: list,
    ) -> dict:
        """Installiere Skills fuer einen einzelnen Agenten."""
        agent_name = agent_data.get("name", agent_slug.upper())
        agent_role = agent_data.get("role", "Agent")
        agent_specific_skills = agent_data.get("skills", [])

        # Agent-spezifische + shared Skills zusammenfuegen
        all_skills = agent_specific_skills + shared_skills
        skill_count = len(all_skills)

        # Tool-Definitionen fuer OpenClaw formatieren
        tools = []
        for skill in all_skills:
            # Service-Abhaengigkeit pruefen
            if skill.get("requires_service"):
                service = skill["requires_service"]
                if not self._is_service_available(service):
                    logger.debug(f"  Skipping {skill['id']}: requires {service}")
                    continue

            tools.append({
                "id": skill["id"],
                "name": skill["name"],
                "description": skill["description"],
                "category": skill.get("category", "general"),
                "parameters": skill.get("parameters", {}),
                "endpoint": f"/api/skills/{skill['id']}/execute",
            })

        # System-Prompt laden
        system_prompt = ""
        if self.prompts:
            try:
                config = self.prompts.load_agent_config(agent_slug)
                system_prompt = config.get("system_prompt", "")
            except Exception:
                pass

        # Agent-Config fuer OpenClaw bauen
        agent_config = {
            "slug": agent_slug,
            "name": agent_name,
            "role": agent_role,
            "model": self._get_agent_model(agent_slug),
            "system_prompt": system_prompt,
            "tools": tools,
            "config": {
                "max_tokens": 4096,
                "temperature": self._get_agent_temperature(agent_slug),
                "skill_count": len(tools),
                "version": self.manifest.get("version", "1.5.0"),
            },
        }

        # An OpenClaw pushen
        result = await self.openclaw.upsert_agent(agent_config)

        if result.get("synced"):
            self._installed_count += 1
            logger.info(f"  {agent_name}: {len(tools)} skills installed")
        else:
            self._failed_count += 1
            logger.warning(f"  {agent_name}: sync failed")

        return {
            "agent": agent_slug,
            "name": agent_name,
            "skill_count": len(tools),
            "synced": result.get("synced", False),
        }

    def _get_agent_model(self, agent_slug: str) -> str:
        """Default-Modell pro Agent (wird vom SmartRouter ueberschrieben)."""
        leader_models = {
            "jarvis": "kimi/k2.5",
            "elon": "anthropic/claude-sonnet-4-20250514",
            "steve": "anthropic/claude-sonnet-4-20250514",
            "archi": "anthropic/claude-sonnet-4-20250514",
        }
        worker_models = {
            "donald": "ollama/llama3.1:8b",
            "donna": "ollama/llama3.1:8b",
            "iris": "anthropic/claude-haiku-4-5-20251001",
            "felix": "ollama/llama3.1:8b",
            "satoshi": "groq/llama-3.1-8b-instant",
            "andreas": "ollama/llama3.1:8b",
        }
        return leader_models.get(agent_slug, worker_models.get(agent_slug, "ollama/llama3.1:8b"))

    def _get_agent_temperature(self, agent_slug: str) -> float:
        """Kreativitaet pro Agent."""
        temps = {
            "jarvis": 0.3,   # Praezise Orchestrierung
            "elon": 0.2,     # Analytisch, datengetrieben
            "steve": 0.7,    # Kreativ fuer Content
            "donald": 0.5,   # Ueberzeugend aber faktenbasiert
            "archi": 0.2,    # Exakter Code
            "donna": 0.3,    # Organisiert, praezise
            "iris": 0.8,     # Maximale Kreativitaet
            "satoshi": 0.2,  # Exakte Zahlen
            "felix": 0.5,    # Empathisch aber korrekt
            "andreas": 0.4,  # Analytisch mit Kreativitaet
        }
        return temps.get(agent_slug, 0.5)

    def _is_service_available(self, service: str) -> bool:
        """Pruefe ob ein externer Service konfiguriert ist."""
        service_env_map = {
            "postiz": "POSTIZ_URL",
            "n8n": "N8N_PORT",
            "hubspot": "HUBSPOT_API_KEY",
            "airtable": "AIRTABLE_API_KEY",
        }
        env_key = service_env_map.get(service)
        if not env_key:
            return True  # Unbekannter Service = erlauben
        return bool(os.getenv(env_key))

    async def _store_locally(self) -> dict:
        """
        Speichere Skills lokal in der DB wenn OpenClaw nicht erreichbar ist.
        Werden beim naechsten Start synchronisiert.
        """
        if not self.db or not self.manifest:
            return {"installed": 0, "failed": 0, "stored_locally": True}

        agent_skills = self.manifest.get("agent_skills", {})
        shared_skills = self.manifest.get("shared_skills", {}).get("skills", [])
        total_skills = 0

        for agent_slug, agent_data in agent_skills.items():
            skills = agent_data.get("skills", []) + shared_skills
            total_skills += len(skills)

            try:
                await self.db.upsert("memory", {
                    "key": f"skills:{agent_slug}",
                    "value": json.dumps({
                        "agent": agent_slug,
                        "name": agent_data.get("name"),
                        "role": agent_data.get("role"),
                        "skills": [s["id"] for s in skills],
                        "skill_count": len(skills),
                        "pending_sync": True,
                    }),
                    "category": "system_config",
                })
            except Exception as e:
                logger.debug(f"Could not store skills for {agent_slug}: {e}")

        logger.info(f"Skills stored locally: {total_skills} skills for {len(agent_skills)} agents (pending OpenClaw sync)")
        return {"installed": 0, "stored_locally": True, "total_skills": total_skills}

    async def _log_installation(self, summary: dict):
        """Logge die Installation in der DB."""
        if not self.db:
            return
        try:
            await self.db.upsert("memory", {
                "key": "skills:last_install",
                "value": json.dumps({
                    "installed": summary["installed"],
                    "failed": summary["failed"],
                    "total_skills": summary["total_skills"],
                    "agents": summary["agents"],
                    "version": self.manifest.get("version", "unknown"),
                }),
                "category": "system_config",
            })
        except Exception:
            pass

    async def get_agent_skills(self, agent_slug: str) -> list:
        """Gib alle Skills eines Agenten zurueck (fuer Runtime)."""
        if not self.manifest:
            await self.load_manifest()
        if not self.manifest:
            return []

        agent_data = self.manifest.get("agent_skills", {}).get(agent_slug, {})
        shared = self.manifest.get("shared_skills", {}).get("skills", [])
        return agent_data.get("skills", []) + shared

    async def get_skill_by_id(self, skill_id: str) -> Optional[dict]:
        """Finde einen spezifischen Skill per ID."""
        if not self.manifest:
            await self.load_manifest()
        if not self.manifest:
            return None

        # In agent skills suchen
        for agent_data in self.manifest.get("agent_skills", {}).values():
            for skill in agent_data.get("skills", []):
                if skill["id"] == skill_id:
                    return skill

        # In shared skills suchen
        for skill in self.manifest.get("shared_skills", {}).get("skills", []):
            if skill["id"] == skill_id:
                return skill

        return None

    def get_stats(self) -> dict:
        """Statistiken ueber installierte Skills."""
        if not self.manifest:
            return {"loaded": False}

        agent_skills = self.manifest.get("agent_skills", {})
        shared_count = len(self.manifest.get("shared_skills", {}).get("skills", []))

        stats = {"agents": {}, "shared_skills": shared_count, "total": 0}
        for slug, data in agent_skills.items():
            count = len(data.get("skills", []))
            stats["agents"][slug] = count
            stats["total"] += count + shared_count

        return stats
