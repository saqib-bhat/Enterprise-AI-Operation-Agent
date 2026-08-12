"""Minimal one-request Groq smoke test for Phase 6.

Behaviours:
- Uses existing `.env` via `app.config.settings`.
- Aborts if the configured provider is not Groq (no network call).
- Makes exactly one Groq API request and prints a short preview of the response.
- Never prints the API key.
"""
from __future__ import annotations

from app.config import settings
from app.llm.factory import get_provider
from app.llm.providers import GroqProvider


def main() -> None:
    provider = get_provider()
    if not isinstance(provider, GroqProvider):
        print(f"SKIP: configured provider is not Groq (found {type(provider).__name__})")
        return

    # Single, short prompt for a smoke request
    prompt = "Return a single short confirmation sentence: 'Groq smoke test success.'"

    try:
        resp = provider.generate(prompt)
    except Exception as e:
        # Surface an error message but do not print secrets
        print("ERROR: Groq request failed:", str(e))
        return

    text = (resp or {}).get("text", "")
    preview = text.strip().replace("\n", " ")[:200]
    print("OK: Groq smoke request succeeded")
    print("Preview:", preview)


if __name__ == "__main__":
    main()
