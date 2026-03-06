"""
JARVIS 1.5 — FastAPI Server
SYSTEMS™ · architectofscale.com

API-Server fuer:
  - OMI Wearable Webhooks
  - Health Check
  - Agent-API (Tasks erstellen, Status abfragen)

Wird von main.py gestartet: create_app(jarvis) → FastAPI
"""

import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger("jarvis.api")


def create_app(jarvis: dict) -> FastAPI:
    """
    Erstelle die FastAPI App mit allen Routen.
    jarvis-Dict enthält alle initialisierten Module.
    """
    app = FastAPI(
        title="JARVIS 1.5 API",
        version=jarvis.get("version", "1.5.0"),
        docs_url="/api/docs",
        redoc_url=None,
    )

    # ── CORS ──────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Health Check ──────────────────────────────────
    @app.get("/health")
    async def health():
        return {
            "status": "online",
            "version": jarvis.get("version", "1.5.0"),
            "modules": len(jarvis),
        }

    # ── OMI Wearable Webhooks ─────────────────────────
    omi = jarvis.get("omi")
    if omi:
        @app.post("/omi/memory")
        async def omi_memory(request: Request):
            data = await request.json()
            result = await omi.handle_webhook("memory_created", data)
            return JSONResponse(content=result)

        @app.post("/omi/transcript")
        async def omi_transcript(request: Request):
            data = await request.json()
            result = await omi.handle_webhook("realtime_transcript", data)
            return JSONResponse(content=result)

        @app.post("/omi/audio")
        async def omi_audio(request: Request):
            body = await request.body()
            result = await omi.handle_webhook("audio_bytes", body)
            return JSONResponse(content=result)

        @app.post("/omi/chat-tool")
        async def omi_chat_tool(request: Request):
            data = await request.json()
            result = await omi.handle_webhook("chat_tool", data)
            return JSONResponse(content=result)

        @app.get("/omi/setup-status")
        async def omi_setup_status():
            return {"is_setup_completed": True}

        @app.get("/.well-known/omi-tools.json")
        async def omi_tools_manifest():
            return omi.get_tools_manifest()

        logger.info("OMI webhook routes registered")

    # ── Task API ──────────────────────────────────────
    runtime = jarvis.get("runtime")
    if runtime:
        @app.post("/api/task")
        async def create_task(request: Request):
            from core.agents.agent_runtime import AgentCall
            data = await request.json()
            call = AgentCall(
                agent_slug=data.get("agent", "jarvis"),
                task_type=data.get("type", "general"),
                task_description=data.get("prompt", ""),
                user_id=data.get("user_id", "api"),
                conversation_id=data.get("conversation_id"),
                channel="api",
            )
            result = await runtime.execute(call)
            return JSONResponse(content={
                "status": "completed",
                "response": result.content,
                "agent": result.agent_slug,
                "model": result.model_used,
            })

    # ── Knowledge API ─────────────────────────────────
    knowledge = jarvis.get("knowledge")
    if knowledge:
        @app.get("/api/knowledge/search")
        async def search_knowledge(q: str, limit: int = 10):
            results = await knowledge.search(query=q, limit=limit)
            return {"results": results}

    # ── Skills API ─────────────────────────────────────
    skills = jarvis.get("skills")
    if skills:
        @app.get("/api/skills")
        async def list_all_skills():
            return skills.get_stats()

        @app.get("/api/skills/{agent_slug}")
        async def list_agent_skills(agent_slug: str):
            agent_skills = await skills.get_agent_skills(agent_slug)
            return {
                "agent": agent_slug,
                "skills": [{"id": s["id"], "name": s["name"], "category": s.get("category")} for s in agent_skills],
                "count": len(agent_skills),
            }

        @app.get("/api/skills/detail/{skill_id:path}")
        async def get_skill_detail(skill_id: str):
            skill = await skills.get_skill_by_id(skill_id)
            if not skill:
                return JSONResponse(status_code=404, content={"error": "Skill not found"})
            return skill

        logger.info("Skills API routes registered")

    logger.info("JARVIS API server initialized")
    return app
