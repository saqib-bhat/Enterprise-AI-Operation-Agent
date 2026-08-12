from __future__ import annotations

from typing import Any, Dict, Optional
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract LLM provider interface for Phase 6."""

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """Generate text from prompt. Returns a dict with at least a `text` key."""


class MockProvider(LLMProvider):
    """A lightweight mock provider for tests and local use.

    It returns deterministic outputs and tracks call counts.
    """

    def __init__(self) -> None:
        self.calls = 0

    def generate(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        self.calls += 1
        return {
            "text": f"mocked response to: {prompt}",
            "provider": "mock",
            "call_index": self.calls,
        }


class GroqProvider(LLMProvider):
    """Groq Free provider wrapper.

    This implementation is intentionally minimal: network calls are executed
    only when `invoke` is called, and tests should use `MockProvider` to avoid
    external requests.
    """

    def __init__(self, api_key: Optional[str], model: str = "gpt-4.1-mini") -> None:
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("Groq API key not configured")

        # Lazy import to avoid pulling heavy deps during tests that use MockProvider
        try:
            import requests
        except Exception as e:
            raise RuntimeError("requests is required to call Groq API") from e

        url = "https://api.groq.ai/v1/engines/groq-2/completions"
        payload = {
            "model": self.model,
            "prompt": prompt,
            **{k: v for k, v in kwargs.items() if k not in {"stream"}},
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}

        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # Normalise to simple shape
        text = ""
        if isinstance(data, dict):
            # attempt to find a textual output
            text = data.get("text") or data.get("output") or str(data)

        return {"text": text, "provider": "groq", "raw": data}
