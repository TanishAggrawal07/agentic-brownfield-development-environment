"""
Provider registry / selection (Phase 5).

get_active_provider() returns the configured provider to use, or None when no
provider is configured (the agent then runs in deterministic offline mode).

Selection:
  - BROWNFIELD_LLM_PROVIDER forces a specific provider by key (gemini,
    openrouter, openai, ollama) when set and available.
  - Otherwise the first available provider in ALL_PROVIDERS priority order.
"""

from __future__ import annotations
import os
import logging
from typing import Optional, List, Dict, Any

from backend.services.llm.base import LLMProvider
from backend.services.llm.providers import ALL_PROVIDERS

logger = logging.getLogger(__name__)


def _by_key() -> Dict[str, LLMProvider]:
    return {p.key: p for p in ALL_PROVIDERS}


def get_active_provider() -> Optional[LLMProvider]:
    """Return the provider to use, or None for offline mode."""
    forced = os.environ.get("BROWNFIELD_LLM_PROVIDER", "").strip().lower()
    providers = _by_key()

    if forced:
        provider = providers.get(forced)
        if provider and provider.available():
            return provider
        logger.warning(
            f"Forced LLM provider '{forced}' is not available; falling back to auto-select."
        )

    for provider in ALL_PROVIDERS:
        if provider.available():
            return provider
    return None


def list_providers() -> List[Dict[str, Any]]:
    """Describe all providers and their availability (for the UI / diagnostics)."""
    active = get_active_provider()
    active_key = active.key if active else None
    return [
        {
            "key": p.key,
            "model": p.model,
            "available": p.available(),
            "active": p.key == active_key,
        }
        for p in ALL_PROVIDERS
    ]
