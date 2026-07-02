"""
LLM provider interface (Phase 5).

A provider is a thin adapter that turns a (system, prompt) pair into text.
Implementations live in providers.py. The agent depends only on this interface,
keeping model vendors fully pluggable.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResult:
    """Outcome of a generation call."""
    text: str
    provider: str
    model: str
    ok: bool = True
    error: Optional[str] = None


class LLMProvider(ABC):
    """Abstract base for all model providers."""

    #: short identifier, e.g. "gemini", "ollama"
    key: str = "base"

    @property
    @abstractmethod
    def model(self) -> str:
        """The model id this provider will call."""
        raise NotImplementedError

    @abstractmethod
    def available(self) -> bool:
        """True when the provider is configured (keys / model set)."""
        raise NotImplementedError

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.2,
        timeout: int = 45,
    ) -> LLMResult:
        """Generate a completion. Implementations must not raise — return an
        LLMResult with ok=False on failure so callers can fall back gracefully."""
        raise NotImplementedError
