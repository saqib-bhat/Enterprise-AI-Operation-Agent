from __future__ import annotations

from typing import Optional
from app.config import settings
from .providers import LLMProvider, MockProvider, GroqProvider


_provider_instance: Optional[LLMProvider] = None


def get_provider() -> LLMProvider:
    """Return a configured LLM provider instance based on app settings.

    Respects the `settings.llm_provider` value. Supported values:
    - "mock" -> MockProvider (for tests)
    - "groq" -> GroqProvider (requires `settings.groq_api_key`)
    """
    global _provider_instance
    if _provider_instance is not None:
        return _provider_instance

    provider = settings.llm_provider.lower()
    if provider == "mock":
        _provider_instance = MockProvider()
    elif provider == "groq":
        _provider_instance = GroqProvider(api_key=settings.groq_api_key, model=settings.groq_model)
    else:
        # Default to mock to keep tests hermetic and safe
        _provider_instance = MockProvider()

    return _provider_instance
