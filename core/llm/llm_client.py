"""
JARVIS 1.5 — LLM Client
Einheitlicher Client für alle LLM-Aufrufe.

Nutzt LiteLLM als Proxy — damit funktioniert:
  - Claude (Anthropic)
  - GPT (OpenAI)
  - Kimi (Moonshot)
  - Ollama (lokal, 0 EUR)
  - Groq (schnell)

Alle Aufrufe gehen durch diesen Client.
Retry, Fallback, Logging — alles eingebaut.
"""

import os
import time
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger("jarvis.llm")

# Model-Mapping: Interne Namen → LiteLLM-Modellnamen
MODEL_MAP = {
    # Tier 0 — Kimi (Strategie)
    "tier0-kimi": "openai/moonshot-v1-128k",
    "tier0-kimi-thinking": "openai/moonshot-v1-128k",
    # Tier 1 — Claude (Qualität)
    "tier1-opus": "anthropic/claude-opus-4-6",
    "tier1-sonnet": "anthropic/claude-sonnet-4-6",
    "tier1-haiku": "anthropic/claude-haiku-4-5-20251001",
    # Tier 2 — Ollama (lokal, kostenlos)
    "tier2-qwen-coder": "ollama/qwen2.5-coder:32b",
    "tier2-llama": "ollama/llama3.1:70b",
    "tier2-qwen-general": "ollama/qwen2.5:32b",
    # Tier 3 — Groq (Speed)
    "tier3-groq-fast": "groq/llama-3.3-70b-versatile",
    "tier3-groq-small": "groq/llama-3.1-8b-instant",
    # Fallbacks
    "fallback-gpt4o": "openai/gpt-4o",
    # Direkte Namen
    "kimi/k2.5": "openai/moonshot-v1-128k",
    "claude/opus": "anthropic/claude-opus-4-6",
    "claude/sonnet": "anthropic/claude-sonnet-4-6",
    "claude/haiku": "anthropic/claude-haiku-4-5-20251001",
    "ollama/llama3": "ollama/llama3.1:70b",
    "groq/llama3": "groq/llama-3.3-70b-versatile",
}


@dataclass
class LLMResponse:
    content: str
    model: str
    tokens_input: int = 0
    tokens_output: int = 0
    cost_cents: float = 0.0
    duration_ms: int = 0
    finish_reason: str = "stop"


class LLMClient:
    """
    Einheitlicher LLM-Client.
    Nutzt LiteLLM für alle Aufrufe.
    """

    def __init__(self, litellm_url: Optional[str] = None, litellm_key: Optional[str] = None):
        self.litellm_url = litellm_url or os.getenv("LITELLM_URL", "http://jarvis-litellm:4000")
        self.litellm_key = litellm_key or os.getenv("LITELLM_MASTER_KEY", "")

        # LiteLLM konfigurieren
        try:
            import litellm
            litellm.api_base = self.litellm_url
            litellm.api_key = self.litellm_key
            litellm.drop_params = True
            litellm.set_verbose = False
            self._litellm = litellm
            logger.info(f"LLM Client ready (LiteLLM: {self.litellm_url})")
        except ImportError:
            self._litellm = None
            logger.warning("litellm not installed — using httpx fallback")

    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        model: str = "tier1-sonnet",
        max_tokens: int = 4096,
        temperature: float = 0.5,
        agent_slug: str = "jarvis",
    ) -> LLMResponse:
        """
        Sende eine Completion-Anfrage.
        Nutzt LiteLLM oder direkten HTTP-Fallback.
        """
        resolved_model = MODEL_MAP.get(model, model)
        start = time.time()

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        try:
            if self._litellm:
                return await self._call_litellm(
                    messages, resolved_model, max_tokens, temperature, start
                )
            else:
                return await self._call_http(
                    messages, resolved_model, max_tokens, temperature, start
                )
        except Exception as e:
            logger.error(f"LLM call failed ({resolved_model}): {e}")
            # Fallback versuchen
            return await self._try_fallback(
                messages, model, max_tokens, temperature, start, str(e)
            )

    async def _call_litellm(
        self, messages, model, max_tokens, temperature, start
    ) -> LLMResponse:
        """LiteLLM SDK Call."""
        response = await self._litellm.acompletion(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        duration_ms = int((time.time() - start) * 1000)
        content = response.choices[0].message.content or ""
        usage = response.usage

        # Kosten aus LiteLLM
        cost = 0.0
        try:
            cost = self._litellm.completion_cost(completion_response=response) * 100
        except Exception:
            pass

        return LLMResponse(
            content=content,
            model=model,
            tokens_input=usage.prompt_tokens if usage else 0,
            tokens_output=usage.completion_tokens if usage else 0,
            cost_cents=round(cost, 4),
            duration_ms=duration_ms,
            finish_reason=response.choices[0].finish_reason or "stop",
        )

    async def _call_http(
        self, messages, model, max_tokens, temperature, start
    ) -> LLMResponse:
        """HTTP Fallback wenn LiteLLM nicht installiert."""
        import httpx

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.litellm_url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.litellm_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        duration_ms = int((time.time() - start) * 1000)
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})

        return LLMResponse(
            content=content,
            model=model,
            tokens_input=usage.get("prompt_tokens", 0),
            tokens_output=usage.get("completion_tokens", 0),
            duration_ms=duration_ms,
        )

    async def _try_fallback(
        self, messages, original_model, max_tokens, temperature, start, error
    ) -> LLMResponse:
        """Versuche Fallback-Modelle."""
        fallback_chain = {
            "tier0-kimi": ["tier1-opus", "tier1-sonnet"],
            "tier0-kimi-thinking": ["tier0-kimi", "tier1-opus"],
            "tier1-opus": ["tier1-sonnet", "tier1-haiku"],
            "tier1-sonnet": ["tier1-haiku", "tier2-llama"],
            "tier1-haiku": ["tier2-llama", "tier3-groq-fast"],
            "tier2-qwen-coder": ["tier2-llama", "tier1-haiku"],
            "tier2-llama": ["tier2-qwen-general", "tier3-groq-fast"],
            "tier2-qwen-general": ["tier2-llama", "tier3-groq-fast"],
            "tier3-groq-fast": ["tier3-groq-small", "tier2-llama"],
        }

        fallbacks = fallback_chain.get(original_model, ["tier1-sonnet", "tier2-llama"])

        for fb_model in fallbacks:
            resolved = MODEL_MAP.get(fb_model, fb_model)
            logger.warning(f"Trying fallback: {original_model} → {fb_model}")
            try:
                if self._litellm:
                    return await self._call_litellm(
                        messages, resolved, max_tokens, temperature, start
                    )
                else:
                    return await self._call_http(
                        messages, resolved, max_tokens, temperature, start
                    )
            except Exception:
                continue

        # Alles fehlgeschlagen
        return LLMResponse(
            content=f"Alle Modelle nicht erreichbar. Ursprünglicher Fehler: {error}",
            model=original_model,
            duration_ms=int((time.time() - start) * 1000),
            finish_reason="error",
        )

    async def generate(
        self,
        prompt: str,
        model: str = "tier2-llama",
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> str:
        """
        Einfacher Generate-Aufruf (fuer Cron Jobs, OMI Processor etc.).
        Gibt nur den Text-Content zurueck.
        """
        response = await self.complete(
            system_prompt="Du bist ein hilfreicher Assistent. Antworte kurz und praezise.",
            user_message=prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.content
