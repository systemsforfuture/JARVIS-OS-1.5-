"""
JARVIS 1.5 — Prompt Loader
SYSTEMS™ · architectofscale.com

Lädt System-Prompts und Tool-Definitionen für jeden Agent.
Wird beim Start und bei jedem Task aufgerufen.

Ablauf:
  1. Base-Prompt laden (agent_base.md) — Anti-Halluzination-Regeln
  2. Agent-spezifischen Prompt laden (agents/{slug}.md)
  3. JARVIS Master-Prompt laden (jarvis_system.md) — nur für JARVIS
  4. Tool-Definitionen laden basierend auf Agent-Skills
  5. Brain-Kontext injizieren (relevante Memories)

Das Ergebnis ist ein vollständiger System-Prompt + Tools
der an das LLM gesendet wird.
"""

import os
import json
from pathlib import Path
from typing import Optional


# Pfade
BASE_DIR = Path(__file__).parent.parent.parent
PROMPTS_DIR = BASE_DIR / "prompts"
TOOLS_DIR = BASE_DIR / "skills" / "tools"

# Welcher Agent bekommt welche Tool-Sets
AGENT_TOOLS = {
    "jarvis": ["brain_tools", "task_tools", "research_tools", "communication_tools", "analytics_tools"],
    "elon": ["brain_tools", "task_tools", "analytics_tools", "research_tools"],
    "steve": ["brain_tools", "research_tools", "marketing_tools", "communication_tools"],
    "donald": ["brain_tools", "research_tools", "sales_tools", "communication_tools"],
    "archi": ["brain_tools", "dev_tools", "research_tools"],
    "donna": ["brain_tools", "operations_tools", "communication_tools", "research_tools"],
    "iris": ["brain_tools", "research_tools"],
    "satoshi": ["brain_tools", "research_tools", "analytics_tools"],
    "felix": ["brain_tools", "communication_tools", "analytics_tools", "research_tools"],
    "andreas": ["brain_tools", "analytics_tools", "research_tools"],
}


def load_system_prompt(agent_slug: str) -> str:
    """
    Lade den vollständigen System-Prompt für einen Agent.

    Zusammensetzung:
    1. agent_base.md (Anti-Halluzination für alle)
    2. agents/{slug}.md (Agent-spezifisch)
    3. jarvis_system.md (nur für JARVIS)
    """
    parts = []

    # 1. Base-Prompt (für alle Agents)
    base_path = PROMPTS_DIR / "agent_base.md"
    if base_path.exists():
        base_text = base_path.read_text(encoding="utf-8")
        # Variablen ersetzen
        agent_name = agent_slug.upper()
        agent_roles = {
            "jarvis": "Chief Intelligence Operator",
            "elon": "Analyst & Systemoptimierer",
            "steve": "Marketing & Content Lead",
            "donald": "Sales & Revenue Lead",
            "archi": "Dev & Infrastructure Lead",
            "donna": "Backoffice & Operations Lead",
            "iris": "Design & Creative Lead",
            "satoshi": "Crypto & Trading Specialist",
            "felix": "Customer Success Lead",
            "andreas": "Customer Success SFE Specialist",
        }
        base_text = base_text.replace("{AGENT_NAME}", agent_name)
        base_text = base_text.replace("{AGENT_ROLE}", agent_roles.get(agent_slug, "Agent"))
        parts.append(base_text)

    # 2. Agent-spezifischer Prompt
    agent_path = PROMPTS_DIR / "agents" / f"{agent_slug}.md"
    if agent_path.exists():
        parts.append(agent_path.read_text(encoding="utf-8"))

    # 3. JARVIS Master-Prompt (nur für JARVIS)
    if agent_slug == "jarvis":
        jarvis_path = PROMPTS_DIR / "jarvis_system.md"
        if jarvis_path.exists():
            parts.append(jarvis_path.read_text(encoding="utf-8"))

    return "\n\n".join(parts)


def load_tools(agent_slug: str) -> list:
    """
    Lade alle Tool-Definitionen für einen Agent.

    Gibt eine Liste von OpenAI-kompatiblen Tool-Definitionen zurück
    die direkt an die LLM API gesendet werden können.
    """
    tool_sets = AGENT_TOOLS.get(agent_slug, ["brain_tools", "research_tools"])
    all_tools = []

    for tool_set_name in tool_sets:
        tool_path = TOOLS_DIR / f"{tool_set_name}.json"
        if tool_path.exists():
            data = json.loads(tool_path.read_text(encoding="utf-8"))
            tools = data.get("tools", [])
            all_tools.extend(tools)

    return all_tools


def load_agent_config(agent_slug: str) -> dict:
    """
    Lade die vollständige Agent-Konfiguration.

    Gibt zurück:
    {
        "system_prompt": "...",      # Vollständiger System-Prompt
        "tools": [...],              # Tool-Definitionen
        "agent_slug": "steve",
        "agent_name": "STEVE",
        "tool_count": 12,
    }
    """
    system_prompt = load_system_prompt(agent_slug)
    tools = load_tools(agent_slug)

    return {
        "agent_slug": agent_slug,
        "agent_name": agent_slug.upper(),
        "system_prompt": system_prompt,
        "tools": tools,
        "tool_count": len(tools),
    }


def load_all_agent_configs() -> dict:
    """Lade Konfigurationen für alle Agents."""
    agents = [
        "jarvis", "elon", "steve", "donald", "archi",
        "donna", "iris", "satoshi", "felix", "andreas",
    ]
    return {slug: load_agent_config(slug) for slug in agents}
