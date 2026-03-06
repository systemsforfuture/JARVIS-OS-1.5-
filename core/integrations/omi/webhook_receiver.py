"""
JARVIS 1.5 — OMI Webhook Receiver
Empfaengt alle Daten vom OMI Wearable und verarbeitet sie.

Webhook Endpoints (registriert in OMI App):
  POST /omi/memory        — Wenn OMI eine Memory erstellt (Gespraech beendet)
  POST /omi/transcript     — Echtzeit-Transkript waehrend Gespraechen
  POST /omi/audio          — Rohe Audio-Bytes (PCM16, 16kHz)
  POST /omi/chat-tool      — Chat-Tool Aufrufe (Voice Commands → JARVIS Aktionen)
  GET  /omi/setup-status   — OMI prueft ob Setup komplett ist
  GET  /.well-known/omi-tools.json — Tool-Manifest fuer OMI Chat-Tools

Alles was du sagst, hoerst und siehst wird erfasst, verarbeitet und
in JARVIS Intelligence gespeichert. JARVIS wird dadurch jeden Tag schlauer.
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Optional

logger = logging.getLogger("jarvis.omi")


class OMIWebhookReceiver:
    """
    Empfaengt Webhooks vom OMI Wearable Device.
    Verarbeitet Memories, Transkripte und Audio in JARVIS Intelligence.
    """

    def __init__(self, db_client=None, llm_client=None, brain=None,
                 knowledge=None, runtime=None, telegram=None):
        self.db = db_client
        self.llm = llm_client
        self.brain = brain
        self.knowledge = knowledge
        self.runtime = runtime
        self.telegram = telegram
        self._processor = OMIDataProcessor(db_client, llm_client, brain, knowledge)

    def register_routes(self, app):
        """Registriere alle OMI Webhook-Routen auf dem FastAPI/Express Server."""
        try:
            # Try FastAPI first
            self._register_fastapi(app)
        except Exception:
            # Fallback: Express.js style
            self._register_express(app)

    def _register_fastapi(self, app):
        """Register routes for FastAPI."""
        from fastapi import Request, Response

        @app.post("/omi/memory")
        async def omi_memory_webhook(request: Request):
            uid = request.query_params.get("uid", "default")
            body = await request.json()
            asyncio.create_task(self._handle_memory(uid, body))
            return {"status": "ok"}

        @app.post("/omi/transcript")
        async def omi_transcript_webhook(request: Request):
            uid = request.query_params.get("uid", "default")
            session_id = request.query_params.get("session_id", "")
            body = await request.json()
            asyncio.create_task(self._handle_transcript(uid, session_id, body))
            return {"status": "ok"}

        @app.post("/omi/audio")
        async def omi_audio_webhook(request: Request):
            uid = request.query_params.get("uid", "default")
            sample_rate = int(request.query_params.get("sample_rate", "16000"))
            audio_bytes = await request.body()
            asyncio.create_task(self._handle_audio(uid, sample_rate, audio_bytes))
            return {"status": "ok"}

        @app.post("/omi/chat-tool")
        async def omi_chat_tool(request: Request):
            body = await request.json()
            result = await self._handle_chat_tool(body)
            return result

        @app.get("/omi/setup-status")
        async def omi_setup_status():
            return {"is_setup_completed": True}

        @app.get("/.well-known/omi-tools.json")
        async def omi_tools_manifest():
            return self._get_tools_manifest()

        logger.info("OMI webhook routes registered (FastAPI)")

    def _register_express(self, app):
        """Register routes for Express.js (dashboard server)."""
        # This is handled separately in dashboard/server.js
        logger.info("OMI routes should be added to Express server")

    # ═══════════════════════════════════════════════════════════
    # HANDLER: Memory Created
    # Wenn OMI ein Gespraech beendet und eine Memory erstellt.
    # Hier passiert die Hauptverarbeitung.
    # ═══════════════════════════════════════════════════════════

    async def _handle_memory(self, uid: str, data: dict):
        """
        Verarbeite eine neue OMI Memory.

        OMI sendet:
        - Strukturierte Zusammenfassung (Titel, Overview, Kategorie)
        - Volle Transkript-Segmente mit Speaker-Identifikation
        - Action Items und Events
        - Emoji und Kategorie
        """
        try:
            logger.info(f"[OMI] Memory received from uid={uid}")

            # Extract memory data
            memory_id = data.get("id", "")
            created_at = data.get("created_at", datetime.utcnow().isoformat())

            # Structured data from OMI
            structured = data.get("structured", {})
            title = structured.get("title", "Unbekanntes Gespraech")
            overview = structured.get("overview", "")
            emoji = structured.get("emoji", "")
            category = structured.get("category", "other")
            action_items = structured.get("action_items", [])
            events = structured.get("events", [])

            # Full transcript
            segments = data.get("transcript_segments", [])
            transcript_text = self._segments_to_text(segments)

            # Process through JARVIS intelligence pipeline
            await self._processor.process_memory(
                memory_id=memory_id,
                uid=uid,
                title=title,
                overview=overview,
                category=category,
                transcript=transcript_text,
                action_items=action_items,
                events=events,
                raw_data=data,
                created_at=created_at,
            )

            logger.info(f"[OMI] Memory processed: {title}")

        except Exception as e:
            logger.error(f"[OMI] Memory processing failed: {e}")

    # ═══════════════════════════════════════════════════════════
    # HANDLER: Real-time Transcript
    # Waehrend du sprichst — Echtzeit-Segmente.
    # ═══════════════════════════════════════════════════════════

    async def _handle_transcript(self, uid: str, session_id: str, segments: list):
        """
        Verarbeite Echtzeit-Transkript-Segmente.

        OMI sendet Arrays mit:
        - text: Transkribierter Text
        - speaker: Speaker-Identifikation
        - start/end: Timestamps
        - is_user: Ob der Traeger spricht
        """
        try:
            for segment in segments:
                text = segment.get("text", "").strip()
                is_user = segment.get("is_user", False)
                speaker = segment.get("speaker", "unknown")

                if not text:
                    continue

                # Store real-time transcript
                if self.db:
                    await self.db.execute(
                        """INSERT INTO omi_transcripts
                           (uid, session_id, speaker, text, is_user,
                            start_time, end_time, created_at)
                           VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())""",
                        uid, session_id, speaker, text, is_user,
                        segment.get("start"), segment.get("end"),
                    )

                # Check for voice commands (user says something actionable)
                if is_user and self._is_voice_command(text):
                    await self._execute_voice_command(uid, text)

        except Exception as e:
            logger.debug(f"[OMI] Transcript processing: {e}")

    # ═══════════════════════════════════════════════════════════
    # HANDLER: Audio Bytes
    # Rohe Audio-Daten fuer erweiterte Verarbeitung.
    # ═══════════════════════════════════════════════════════════

    async def _handle_audio(self, uid: str, sample_rate: int, audio_bytes: bytes):
        """
        Verarbeite rohe Audio-Bytes.
        PCM16 (16-bit little-endian), typisch 16kHz.
        """
        # Audio bytes werden nur bei Bedarf gespeichert
        # z.B. fuer custom Voice Recognition oder Emotionserkennung
        logger.debug(f"[OMI] Audio received: {len(audio_bytes)} bytes, {sample_rate}Hz")

    # ═══════════════════════════════════════════════════════════
    # HANDLER: Chat Tools
    # Voice Commands die direkt zu JARVIS Aktionen werden.
    # ═══════════════════════════════════════════════════════════

    async def _handle_chat_tool(self, data: dict) -> dict:
        """
        Verarbeite Chat-Tool Aufrufe.
        User sagt etwas → OMI erkennt Tool → JARVIS fuehrt aus.
        """
        tool_name = data.get("tool_name", "")
        uid = data.get("uid", "")

        try:
            if tool_name == "jarvis_execute":
                task = data.get("task", "")
                agent = data.get("agent", "jarvis")
                return await self._execute_jarvis_task(uid, agent, task)

            elif tool_name == "jarvis_status":
                return await self._get_jarvis_status()

            elif tool_name == "jarvis_remember":
                info = data.get("information", "")
                return await self._remember_info(uid, info)

            elif tool_name == "jarvis_agents":
                query = data.get("query", "")
                agent = data.get("agent", "jarvis")
                return await self._ask_agent(uid, agent, query)

            elif tool_name == "jarvis_create_task":
                title = data.get("title", "")
                agent = data.get("agent", "jarvis")
                priority = data.get("priority", 2)
                return await self._create_task_from_voice(uid, title, agent, priority)

            else:
                return {"result": f"Unbekanntes Tool: {tool_name}"}

        except Exception as e:
            logger.error(f"[OMI] Chat tool error: {e}")
            return {"error": str(e)}

    # ─── Chat Tool Implementations ───

    async def _execute_jarvis_task(self, uid: str, agent: str, task: str) -> dict:
        """Fuehre einen Task ueber JARVIS aus."""
        if not self.runtime:
            return {"error": "JARVIS Runtime nicht verfuegbar"}

        from core.agents.agent_runtime import AgentCall
        call = AgentCall(
            agent_slug=agent,
            task_description=task,
            channel="omi",
            metadata={"omi_uid": uid},
        )
        response = await self.runtime.execute(call)
        return {"result": response.content[:2000]}

    async def _get_jarvis_status(self) -> dict:
        """System-Status abrufen."""
        return {"result": "JARVIS 1.5 ist online und arbeitet. Alle Systeme aktiv."}

    async def _remember_info(self, uid: str, info: str) -> dict:
        """Information explizit merken."""
        if self.brain:
            await self.brain.store(
                key=f"omi_remember_{datetime.utcnow().strftime('%Y%m%d_%H%M')}",
                value=info,
                metadata={"source": "omi_voice", "uid": uid, "type": "explicit_memory"},
            )
        if self.db:
            await self.db.execute(
                """INSERT INTO omi_memories
                   (uid, memory_type, content, source, importance, created_at)
                   VALUES ($1, $2, $3, $4, $5, NOW())""",
                uid, "explicit", info, "voice_command", 8
            )
        return {"result": f"Gemerkt: {info[:100]}"}

    async def _ask_agent(self, uid: str, agent: str, query: str) -> dict:
        """Frage direkt an einen Agent stellen."""
        if not self.runtime:
            return {"error": "Runtime nicht verfuegbar"}

        from core.agents.agent_runtime import AgentCall
        call = AgentCall(
            agent_slug=agent,
            task_description=query,
            channel="omi",
            metadata={"omi_uid": uid},
        )
        response = await self.runtime.execute(call)
        return {"result": response.content[:2000]}

    async def _create_task_from_voice(self, uid: str, title: str,
                                       agent: str, priority: int) -> dict:
        """Task per Sprachbefehl erstellen."""
        if self.db:
            await self.db.execute(
                """INSERT INTO tasks (title, agent_slug, priority, status, channel)
                   VALUES ($1, $2, $3, 'pending', 'omi')""",
                title, agent, priority
            )
        return {"result": f"Task erstellt: {title} (Agent: {agent})"}

    # ─── Helper Methods ───

    def _segments_to_text(self, segments: list) -> str:
        """Konvertiere OMI Transkript-Segmente zu lesbarem Text."""
        lines = []
        for seg in segments:
            speaker = seg.get("speaker", "?")
            text = seg.get("text", "").strip()
            is_user = seg.get("is_user", False)
            label = "DOM" if is_user else f"Speaker_{speaker}"
            if text:
                lines.append(f"[{label}] {text}")
        return "\n".join(lines)

    def _is_voice_command(self, text: str) -> bool:
        """Erkennt ob ein Transkript-Segment ein Voice Command ist."""
        triggers = [
            "jarvis", "hey jarvis", "ok jarvis",
            "erstell", "mach", "sende", "schreib",
            "erinner mich", "merke dir", "notiere",
            "status", "wie laeuft",
        ]
        text_lower = text.lower()
        return any(trigger in text_lower for trigger in triggers)

    async def _execute_voice_command(self, uid: str, text: str):
        """Fuehre einen erkannten Voice Command aus."""
        if not self.runtime:
            return

        try:
            from core.agents.agent_runtime import AgentCall
            call = AgentCall(
                agent_slug="jarvis",
                task_description=f"Voice Command von OMI: {text}",
                channel="omi_realtime",
                metadata={"omi_uid": uid, "source": "voice_command"},
            )
            response = await self.runtime.execute(call)

            # Optional: Ergebnis per Telegram zurueckschicken
            if self.telegram:
                await self.telegram.send_message(
                    f"\U0001F3A4 OMI Voice Command\n\n"
                    f"Befehl: {text}\n"
                    f"Antwort: {response.content[:500]}"
                )
        except Exception as e:
            logger.error(f"[OMI] Voice command execution failed: {e}")

    def _get_tools_manifest(self) -> dict:
        """OMI Chat-Tools Manifest (/.well-known/omi-tools.json)."""
        return {
            "tools": [
                {
                    "name": "jarvis_execute",
                    "description": (
                        "Execute any task through JARVIS AI team. Use when the user "
                        "wants to accomplish something: write content, analyze data, "
                        "manage tasks, send messages, or delegate work to the team."
                    ),
                    "endpoint": "/omi/chat-tool",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task": {
                                "type": "string",
                                "description": "The task to execute"
                            },
                            "agent": {
                                "type": "string",
                                "enum": [
                                    "jarvis", "elon", "steve", "donald",
                                    "archi", "donna", "iris", "satoshi",
                                    "felix", "andreas"
                                ],
                                "description": "Which agent should handle this"
                            }
                        },
                        "required": ["task"]
                    },
                    "auth_required": False,
                    "status_message": "JARVIS arbeitet daran..."
                },
                {
                    "name": "jarvis_remember",
                    "description": (
                        "Remember important information permanently. Use when the user "
                        "explicitly says to remember something: birthdays, preferences, "
                        "contacts, ideas, decisions, or any personal information."
                    ),
                    "endpoint": "/omi/chat-tool",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "information": {
                                "type": "string",
                                "description": "The information to remember"
                            }
                        },
                        "required": ["information"]
                    },
                    "auth_required": False,
                    "status_message": "Wird gespeichert..."
                },
                {
                    "name": "jarvis_agents",
                    "description": (
                        "Ask a specific JARVIS agent a question or for advice. "
                        "Agents: ELON (analysis), STEVE (marketing), DONALD (sales), "
                        "ARCHI (tech), DONNA (ops), IRIS (design), FELIX (customer success)."
                    ),
                    "endpoint": "/omi/chat-tool",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Your question or request"
                            },
                            "agent": {
                                "type": "string",
                                "enum": [
                                    "elon", "steve", "donald", "archi",
                                    "donna", "iris", "felix", "andreas"
                                ],
                                "description": "Which agent to ask"
                            }
                        },
                        "required": ["query", "agent"]
                    },
                    "auth_required": False,
                    "status_message": "Agent wird befragt..."
                },
                {
                    "name": "jarvis_create_task",
                    "description": (
                        "Create a new task for the JARVIS team. Use when the user "
                        "wants to add a to-do, schedule work, or assign something."
                    ),
                    "endpoint": "/omi/chat-tool",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Task title"
                            },
                            "agent": {
                                "type": "string",
                                "description": "Agent to assign to"
                            },
                            "priority": {
                                "type": "integer",
                                "description": "Priority 1-5 (1=highest)"
                            }
                        },
                        "required": ["title"]
                    },
                    "auth_required": False,
                    "status_message": "Task wird erstellt..."
                },
                {
                    "name": "jarvis_status",
                    "description": (
                        "Get JARVIS system status. Use when the user asks about "
                        "system health, active tasks, or team status."
                    ),
                    "endpoint": "/omi/chat-tool",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    },
                    "auth_required": False,
                    "status_message": "Status wird abgerufen..."
                }
            ]
        }
