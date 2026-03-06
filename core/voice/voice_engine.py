"""
JARVIS 1.5 — Voice Engine
SYSTEMS™ · architectofscale.com

JARVIS kann SPRECHEN und HOEREN.

Features:
  - Text-to-Speech (TTS): ElevenLabs, OpenAI TTS, Edge TTS (kostenlos)
  - Speech-to-Text (STT): Whisper (lokal via Ollama oder OpenAI API)
  - Telegram Voice: Sprachnachrichten empfangen und mit Sprache antworten
  - OMI Voice Commands: Direkte Sprachsteuerung

TTS Hierarchy:
  1. ElevenLabs (bestes Voice Cloning, kostenpflichtig)
  2. OpenAI TTS (sehr gut, guenstig)
  3. Edge TTS (kostenlos, gut genug fuer Alltag)
"""

import os
import io
import logging
import tempfile
from typing import Optional
from pathlib import Path

logger = logging.getLogger("jarvis.voice")


class VoiceEngine:
    """
    Sprach-Engine fuer JARVIS.
    Kann Text in Sprache und Sprache in Text umwandeln.
    """

    def __init__(self, llm_client=None):
        self.llm = llm_client
        self.elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.default_voice = os.getenv("JARVIS_VOICE", "onyx")  # OpenAI voice
        self.elevenlabs_voice_id = os.getenv("ELEVENLABS_VOICE_ID", "")
        self._tts_provider = self._detect_tts_provider()
        self._stt_provider = self._detect_stt_provider()

        logger.info(f"Voice Engine: TTS={self._tts_provider}, STT={self._stt_provider}")

    def _detect_tts_provider(self) -> str:
        if self.elevenlabs_key:
            return "elevenlabs"
        if self.openai_key:
            return "openai"
        return "edge"

    def _detect_stt_provider(self) -> str:
        ollama_url = os.getenv("OLLAMA_URL") or os.getenv("OLLAMA_API_BASE")
        if ollama_url:
            return "whisper_local"
        if self.openai_key:
            return "whisper_api"
        return "none"

    # ═══════════════════════════════════════════════════
    # TEXT-TO-SPEECH
    # ═══════════════════════════════════════════════════

    async def text_to_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> Optional[bytes]:
        """
        Konvertiere Text in Sprache.
        Gibt Audio-Bytes zurueck (MP3 oder OGG).
        """
        provider = provider or self._tts_provider
        voice = voice or self.default_voice

        # Text kuerzen fuer TTS (max ~4000 Zeichen)
        if len(text) > 4000:
            text = text[:3950] + "... und so weiter."

        try:
            if provider == "elevenlabs":
                return await self._tts_elevenlabs(text, voice)
            elif provider == "openai":
                return await self._tts_openai(text, voice)
            else:
                return await self._tts_edge(text, voice)
        except Exception as e:
            logger.error(f"TTS failed ({provider}): {e}")
            # Fallback chain
            if provider == "elevenlabs":
                return await self.text_to_speech(text, provider="openai")
            elif provider == "openai":
                return await self.text_to_speech(text, provider="edge")
            return None

    async def _tts_elevenlabs(self, text: str, voice: str) -> bytes:
        """ElevenLabs TTS — beste Qualitaet."""
        import httpx

        voice_id = self.elevenlabs_voice_id or "21m00Tcm4TlvDq8ikWAM"  # Default: Rachel

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                headers={
                    "xi-api-key": self.elevenlabs_key,
                    "Content-Type": "application/json",
                },
                json={
                    "text": text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.8,
                        "style": 0.3,
                    },
                },
            )
            resp.raise_for_status()
            return resp.content

    async def _tts_openai(self, text: str, voice: str) -> bytes:
        """OpenAI TTS — sehr gut, guenstig."""
        import httpx

        voice_map = {
            "jarvis": "onyx",
            "female": "nova",
            "default": "onyx",
        }
        openai_voice = voice_map.get(voice, voice)

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.openai.com/v1/audio/speech",
                headers={
                    "Authorization": f"Bearer {self.openai_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "tts-1",
                    "input": text,
                    "voice": openai_voice,
                    "response_format": "opus",
                },
            )
            resp.raise_for_status()
            return resp.content

    async def _tts_edge(self, text: str, voice: str) -> bytes:
        """Edge TTS — kostenlos, Microsoft Neural Voices."""
        try:
            import edge_tts

            voice_map = {
                "jarvis": "de-DE-ConradNeural",
                "female": "de-DE-KatjaNeural",
                "default": "de-DE-ConradNeural",
                "english": "en-US-GuyNeural",
            }
            edge_voice = voice_map.get(voice, "de-DE-ConradNeural")

            communicate = edge_tts.Communicate(text, edge_voice)
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            return audio_data

        except ImportError:
            logger.warning("edge-tts not installed: pip install edge-tts")
            return b""

    # ═══════════════════════════════════════════════════
    # SPEECH-TO-TEXT
    # ═══════════════════════════════════════════════════

    async def speech_to_text(
        self,
        audio_data: bytes,
        language: str = "de",
    ) -> str:
        """
        Konvertiere Sprache in Text.
        Akzeptiert: OGG, MP3, WAV, M4A
        """
        try:
            if self._stt_provider == "whisper_api":
                return await self._stt_openai(audio_data, language)
            elif self._stt_provider == "whisper_local":
                return await self._stt_local(audio_data, language)
            else:
                logger.warning("No STT provider available")
                return ""
        except Exception as e:
            logger.error(f"STT failed: {e}")
            return ""

    async def _stt_openai(self, audio_data: bytes, language: str) -> str:
        """OpenAI Whisper API."""
        import httpx

        # Audio als Datei senden
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {self.openai_key}"},
                files={"file": ("audio.ogg", audio_data, "audio/ogg")},
                data={"model": "whisper-1", "language": language},
            )
            resp.raise_for_status()
            return resp.json().get("text", "")

    async def _stt_local(self, audio_data: bytes, language: str) -> str:
        """Lokales Whisper via Ollama oder standalone."""
        import httpx

        ollama_url = os.getenv("OLLAMA_URL", "http://jarvis-ollama:11434")

        # Versuch 1: Ollama (wenn whisper model gepullt)
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{ollama_url}/api/generate",
                    json={
                        "model": "whisper",
                        "prompt": "Transcribe this audio",
                    },
                    timeout=60,
                )
                if resp.status_code < 400:
                    return resp.json().get("response", "")
        except Exception:
            pass

        # Versuch 2: Standalone whisper binary
        try:
            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
                f.write(audio_data)
                tmp_path = f.name

            import subprocess
            result = subprocess.run(
                ["whisper", tmp_path, "--language", language, "--model", "base"],
                capture_output=True, text=True, timeout=120,
            )
            os.unlink(tmp_path)
            return result.stdout.strip()
        except Exception:
            return ""

    # ═══════════════════════════════════════════════════
    # TELEGRAM VOICE INTEGRATION
    # ═══════════════════════════════════════════════════

    async def handle_voice_message(self, audio_data: bytes) -> dict:
        """
        Verarbeite eine Telegram-Sprachnachricht.
        Returns: {"text": "transkribierter text", "audio_reply": bytes}
        """
        # 1. Sprache → Text
        transcript = await self.speech_to_text(audio_data)
        if not transcript:
            return {"text": "", "audio_reply": None, "error": "Konnte Audio nicht transkribieren"}

        logger.info(f"Voice transcript: {transcript[:80]}...")

        return {
            "text": transcript,
            "audio_reply": None,  # Wird vom Caller mit Agent-Response befuellt
        }

    async def reply_with_voice(self, text: str) -> Optional[bytes]:
        """Erstelle eine Sprach-Antwort fuer einen Text."""
        return await self.text_to_speech(text)

    # ═══════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════

    def get_available_voices(self) -> dict:
        """Liste aller verfuegbaren Stimmen."""
        voices = {
            "edge_tts": {
                "de-DE-ConradNeural": "Deutsch maennlich",
                "de-DE-KatjaNeural": "Deutsch weiblich",
                "en-US-GuyNeural": "English male",
                "en-US-JennyNeural": "English female",
            },
        }
        if self.openai_key:
            voices["openai"] = {
                "onyx": "Deep male (JARVIS default)",
                "nova": "Warm female",
                "alloy": "Neutral",
                "echo": "Male medium",
                "fable": "British male",
                "shimmer": "Soft female",
            }
        if self.elevenlabs_key:
            voices["elevenlabs"] = {
                "custom": f"Voice ID: {self.elevenlabs_voice_id or 'not set'}",
            }
        return voices

    def get_status(self) -> dict:
        return {
            "tts_provider": self._tts_provider,
            "stt_provider": self._stt_provider,
            "default_voice": self.default_voice,
            "elevenlabs": bool(self.elevenlabs_key),
            "openai_tts": bool(self.openai_key),
        }
