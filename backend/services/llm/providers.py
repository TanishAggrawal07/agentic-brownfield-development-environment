"""
Concrete LLM providers (Phase 5).

All providers use the stdlib (urllib) so the agent adds no new dependencies,
consistent with the existing ai_service. Each provider reads its own
configuration from environment variables and never raises from generate().

Environment variables:
  Gemini      GEMINI_API_KEY            (+ optional GEMINI_MODEL)
  OpenRouter  OPENROUTER_API_KEY        (+ optional OPENROUTER_MODEL)
  OpenAI      OPENAI_API_KEY            (+ optional OPENAI_MODEL)
  Ollama      OLLAMA_MODEL              (+ optional OLLAMA_HOST, default
                                         http://localhost:11434)
"""

from __future__ import annotations
import os
import json
import logging
import urllib.request
import urllib.error
from typing import Optional

from backend.services.llm.base import LLMProvider, LLMResult

logger = logging.getLogger(__name__)


def _http_post_json(url: str, payload: dict, headers: dict, timeout: int) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


# ---------------------------------------------------------------------------
# Gemini
# ---------------------------------------------------------------------------

class GeminiProvider(LLMProvider):
    key = "gemini"

    @property
    def model(self) -> str:
        return os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

    def available(self) -> bool:
        return bool(os.environ.get("GEMINI_API_KEY"))

    def generate(self, prompt, system=None, temperature=0.2, timeout=45) -> LLMResult:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return LLMResult("", self.key, self.model, ok=False, error="missing GEMINI_API_KEY")
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={api_key}"
        )
        parts = []
        if system:
            parts.append({"text": system})
        parts.append({"text": prompt})
        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {"temperature": temperature},
        }
        try:
            data = _http_post_json(url, payload, {}, timeout)
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return LLMResult(text, self.key, self.model)
        except Exception as exc:
            logger.error(f"Gemini generate failed: {exc}")
            return LLMResult("", self.key, self.model, ok=False, error=str(exc))


# ---------------------------------------------------------------------------
# OpenAI-compatible base (OpenAI, OpenRouter)
# ---------------------------------------------------------------------------

class _OpenAICompatProvider(LLMProvider):
    """Shared logic for the OpenAI Chat Completions wire format."""

    _url: str = ""
    _env_key: str = ""

    def _api_key(self) -> Optional[str]:
        return os.environ.get(self._env_key)

    def available(self) -> bool:
        return bool(self._api_key())

    def _extra_headers(self) -> dict:
        return {}

    def generate(self, prompt, system=None, temperature=0.2, timeout=45) -> LLMResult:
        api_key = self._api_key()
        if not api_key:
            return LLMResult("", self.key, self.model, ok=False, error=f"missing {self._env_key}")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {"model": self.model, "messages": messages, "temperature": temperature}
        headers = {"Authorization": f"Bearer {api_key}", **self._extra_headers()}
        try:
            data = _http_post_json(self._url, payload, headers, timeout)
            text = data["choices"][0]["message"]["content"]
            return LLMResult(text, self.key, self.model)
        except Exception as exc:
            logger.error(f"{self.key} generate failed: {exc}")
            return LLMResult("", self.key, self.model, ok=False, error=str(exc))


class OpenAIProvider(_OpenAICompatProvider):
    key = "openai"
    _url = "https://api.openai.com/v1/chat/completions"
    _env_key = "OPENAI_API_KEY"

    @property
    def model(self) -> str:
        return os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


class OpenRouterProvider(_OpenAICompatProvider):
    key = "openrouter"
    _url = "https://openrouter.ai/api/v1/chat/completions"
    _env_key = "OPENROUTER_API_KEY"

    @property
    def model(self) -> str:
        return os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini")

    def _extra_headers(self) -> dict:
        # OpenRouter recommends identifying the calling app.
        return {
            "HTTP-Referer": os.environ.get("OPENROUTER_REFERER", "http://localhost:8000"),
            "X-Title": "Brownfield IDE",
        }


# ---------------------------------------------------------------------------
# Ollama (local LLMs)
# ---------------------------------------------------------------------------

class OllamaProvider(LLMProvider):
    key = "ollama"

    @property
    def model(self) -> str:
        return os.environ.get("OLLAMA_MODEL", "llama3")

    def _host(self) -> str:
        return os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")

    def available(self) -> bool:
        # Opt-in via OLLAMA_MODEL so we don't probe localhost when unused.
        return bool(os.environ.get("OLLAMA_MODEL"))

    def generate(self, prompt, system=None, temperature=0.2, timeout=120) -> LLMResult:
        url = f"{self._host()}/api/chat"
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        try:
            data = _http_post_json(url, payload, {}, timeout)
            text = data.get("message", {}).get("content", "")
            if not text:
                return LLMResult("", self.key, self.model, ok=False, error="empty response")
            return LLMResult(text, self.key, self.model)
        except Exception as exc:
            logger.error(f"Ollama generate failed: {exc}")
            return LLMResult("", self.key, self.model, ok=False, error=str(exc))


# Registry order = selection priority when no provider is forced.
ALL_PROVIDERS = [
    GeminiProvider(),
    OpenRouterProvider(),
    OpenAIProvider(),
    OllamaProvider(),
]
