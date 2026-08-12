from app import llm
from app.config import settings


def test_factory_returns_mock_by_default(monkeypatch):
    # Ensure default settings -> groq in config, but for hermetic tests we set to mock
    monkeypatch.setattr(settings, "llm_provider", "mock")
    provider = llm.get_provider()
    assert provider is not None
    assert provider.generate("hello")["provider"] == "mock"


def test_mock_provider_is_deterministic():
    p = llm.MockProvider()
    r1 = p.generate("a")
    r2 = p.generate("b")
    assert r1["call_index"] == 1
    assert r2["call_index"] == 2
    assert "mocked response to: a" in r1["text"]


def test_selecting_groq_provider_returns_instance(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "groq")
    # ensure factory returns a fresh instance (clear cached singleton)
    import app.llm.factory as _factory
    _factory._provider_instance = None
    # do not call network methods — just validate factory wiring
    provider = llm.get_provider()
    from app.llm.providers import GroqProvider

    assert isinstance(provider, GroqProvider)
    # GroqProvider should reflect settings for the API key (may be None in CI)
    assert getattr(provider, "api_key", None) == settings.groq_api_key
