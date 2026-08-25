from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod


logger = logging.getLogger(__name__)


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
    """Groq Chat Completions provider wrapper.

    Uses the current Groq Chat Completions API endpoint.
    Network calls are executed only when `generate` is called.
    Tests should use `MockProvider` to avoid external requests.
    """

    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(
        self,
        api_key: Optional[str],
        model: str = "llama-3.1-8b-instant",
    ) -> None:
        self.api_key = api_key
        self.model = model

    @staticmethod
    def _classify_error(status_code: Optional[int]) -> Optional[str]:
        """Map an HTTP status code to a safe, category-level error message.

        Returns ``None`` for successful (2xx) responses. Otherwise returns a
        short message containing only the HTTP status code and a generic
        category. The response body and credentials are never included so the
        message is safe to surface to users and logs.
        """
        if status_code is None or (200 <= status_code < 300):
            return None
        if status_code in (401, 403):
            return f"Groq API request failed: authentication failure (status {status_code})"
        if status_code == 404:
            return f"Groq API request failed: endpoint/model failure (status {status_code})"
        if status_code == 429:
            return f"Groq API request failed: rate limit exceeded (status {status_code})"
        return f"Groq API request failed (status {status_code})"

    def generate(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("Groq API key not configured")

        # Lazy import to avoid pulling heavy deps during tests that use MockProvider
        try:
            import requests
        except Exception as e:
            raise RuntimeError("requests is required to call Groq API") from e

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            **{k: v for k, v in kwargs.items() if k not in {"stream"}},
        }

        # Execute the HTTP request. Transport-level failures (DNS, connection
        # errors, timeouts) are logged internally and surfaced as a safe,
        # generic category without exposing credentials or the response body.
        try:
            resp = requests.post(
                self.GROQ_API_URL,
                json=payload,
                headers=headers,
                timeout=30,
            )
        except Exception as e:
            logger.debug("Groq HTTP request error: %s", e)
            raise RuntimeError("Groq API request failed: network error") from None

        status = getattr(resp, "status_code", None)
        safe_error = self._classify_error(status)
        if safe_error is not None:
            logger.debug("Groq API returned non-success status %s", status)
            raise RuntimeError(safe_error) from None

        # Non-2xx already handled above. Parse the JSON body safely.
        try:
            data = resp.json()
        except Exception:
            logger.debug("Groq API returned an invalid (non-JSON) response")
            raise RuntimeError("Groq API returned an invalid response") from None

        # Normalize: extract text from choices[0].message.content
        text = ""
        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            # Malformed response — do not expose raw data
            raise RuntimeError("Malformed response from Groq API")

        return {"text": text, "provider": "groq"}
