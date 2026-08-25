from app import llm
from app.config import settings
from app.llm.providers import GroqProvider, MockProvider
from unittest.mock import MagicMock, patch


def test_factory_returns_mock_by_default(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "mock")
    provider = llm.get_provider()
    assert provider is not None
    assert provider.generate("hello")["provider"] == "mock"


def test_mock_provider_is_deterministic():
    p = MockProvider()
    r1 = p.generate("a")
    r2 = p.generate("b")
    assert r1["call_index"] == 1
    assert r2["call_index"] == 2
    assert "mocked response to: a" in r1["text"]


def test_selecting_groq_provider_returns_instance(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "groq")
    import app.llm.factory as _factory
    _factory._provider_instance = None
    provider = llm.get_provider()
    assert isinstance(provider, GroqProvider)
    assert getattr(provider, "api_key", None) == settings.groq_api_key


def test_groq_provider_missing_api_key():
    provider = GroqProvider(api_key=None)
    try:
        provider.generate("test")
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "not configured" in str(e)


def test_groq_provider_sends_correct_request():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "July revenue was $470,884.04.",
                }
            }
        ]
    }

    mock_post = MagicMock(return_value=mock_response)
    mock_requests = MagicMock(post=mock_post)

    with patch.dict("sys.modules", {"requests": mock_requests}):
        provider = GroqProvider(
            api_key="test-key-not-real",
            model="llama-3.1-8b-instant",
        )
        result = provider.generate("What was July revenue?")

    call_args = mock_post.call_args
    assert "https://api.groq.com/openai/v1/chat/completions" in str(call_args[0][0])

    headers = call_args[1].get("headers", {})
    assert "Authorization" in headers
    assert "Bearer test-key-not-real" in headers["Authorization"]
    assert headers.get("Content-Type") == "application/json"

    payload = call_args[1].get("json", {})
    assert "model" in payload
    assert "messages" in payload
    assert payload["messages"] == [{"role": "user", "content": "What was July revenue?"}]

    assert result["text"] == "July revenue was $470,884.04."
    assert result["provider"] == "groq"


def test_groq_provider_handles_http_failure():
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.raise_for_status.side_effect = Exception("Unauthorized")
    mock_response.json.return_value = {"error": "Unauthorized"}

    mock_post = MagicMock(return_value=mock_response)

    with patch.dict("sys.modules", {"requests": MagicMock(post=mock_post)}):
        provider = GroqProvider(api_key="test-key-not-real")
        try:
            provider.generate("test")
            assert False, "Should have raised RuntimeError"
        except RuntimeError as e:
            assert "request failed" in str(e).lower()
            assert "test-key-not-real" not in str(e)
            assert "Unauthorized" not in str(e)


def test_groq_provider_handles_malformed_response():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"unexpected": "response format"}

    mock_post = MagicMock(return_value=mock_response)

    with patch.dict("sys.modules", {"requests": MagicMock(post=mock_post)}):
        provider = GroqProvider(api_key="test-key-not-real")
        try:
            provider.generate("test")
            assert False, "Should have raised RuntimeError"
        except RuntimeError as e:
            assert "malformed" in str(e).lower()
            assert "unexpected" not in str(e).lower()


def test_response_generation_remains_provider_agnostic(monkeypatch):
    from app.agent.response import generate_response

    monkeypatch.setattr(settings, "llm_provider", "mock")
    import app.llm.factory as _f
    _f._provider_instance = None

    state = {
        "user_query": "What was July revenue?",
        "selected_tools": ["sql"],
        "sql_results": {
            "success": True,
            "columns": ["july_revenue"],
            "rows": [(470884.04,)],
        },
        "calculations": {},
        "retrieved_documents": [],
        "evidence": [{"source": "sql", "summary": "SQL query results", "rows": 1}],
        "verification_result": {"ok": True, "reasons": [], "attempts": 1},
        "final_answer": "July revenue was $470,884.04",
    }

    result = generate_response(state)

    assert result is not None
    assert "Answer" in result
    assert "Key Findings" in result
    assert "Tools Used" in result
    assert "Sources" in result
    assert "Evidence" in result
    assert "Limitations" in result

    assert "july_revenue: 470884.04" in result["Answer"] or "mocked" in result["Answer"].lower()


def test_groq_provider_401_is_authentication_failure():
    """HTTP 401 must map to an authentication-failure category, not endpoint."""
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.raise_for_status.return_value = None
    # The response body must never be surfaced to the caller.
    mock_response.json.return_value = {
        "error": "Unauthorized",
        "detail": "invalid key test-key-not-real",
    }

    mock_post = MagicMock(return_value=mock_response)

    with patch.dict("sys.modules", {"requests": MagicMock(post=mock_post)}):
        provider = GroqProvider(api_key="test-key-not-real")
        try:
            provider.generate("test")
            assert False, "Should have raised RuntimeError"
        except RuntimeError as e:
            msg = str(e)
            assert "401" in msg
            assert "authentication" in msg.lower()
            # Credentials must never appear in the safe error message.
            assert "test-key-not-real" not in msg
            # Response body must never appear in the safe error message.
            assert "Unauthorized" not in msg
            assert "invalid key" not in msg


def test_groq_provider_403_is_authentication_failure():
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "error": "Forbidden",
        "detail": "test-key-not-real",
    }

    mock_post = MagicMock(return_value=mock_response)

    with patch.dict("sys.modules", {"requests": MagicMock(post=mock_post)}):
        provider = GroqProvider(api_key="test-key-not-real")
        try:
            provider.generate("test")
            assert False, "Should have raised RuntimeError"
        except RuntimeError as e:
            msg = str(e)
            assert "403" in msg
            assert "authentication" in msg.lower()
            assert "test-key-not-real" not in msg
            assert "Forbidden" not in msg


def test_groq_provider_404_is_endpoint_model_failure():
    """HTTP 404 (the smoke-test failure) must map to endpoint/model failure."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "error": "Not Found",
        "detail": "model gpt-4.1-mini is not available",
    }

    mock_post = MagicMock(return_value=mock_response)

    with patch.dict("sys.modules", {"requests": MagicMock(post=mock_post)}):
        provider = GroqProvider(api_key="test-key-not-real")
        try:
            provider.generate("test")
            assert False, "Should have raised RuntimeError"
        except RuntimeError as e:
            msg = str(e)
            assert "404" in msg
            assert "endpoint/model" in msg.lower()
            assert "test-key-not-real" not in msg
            assert "Not Found" not in msg
            assert "gpt-4.1-mini" not in msg


def test_groq_provider_429_is_rate_limit():
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"error": "Too Many Requests"}

    mock_post = MagicMock(return_value=mock_response)

    with patch.dict("sys.modules", {"requests": MagicMock(post=mock_post)}):
        provider = GroqProvider(api_key="test-key-not-real")
        try:
            provider.generate("test")
            assert False, "Should have raised RuntimeError"
        except RuntimeError as e:
            msg = str(e)
            assert "429" in msg
            assert "rate limit" in msg.lower()
            assert "test-key-not-real" not in msg
            assert "Too Many Requests" not in msg


def test_groq_provider_500_is_other_http_error():
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"error": "Internal Server Error"}

    mock_post = MagicMock(return_value=mock_response)

    with patch.dict("sys.modules", {"requests": MagicMock(post=mock_post)}):
        provider = GroqProvider(api_key="test-key-not-real")
        try:
            provider.generate("test")
            assert False, "Should have raised RuntimeError"
        except RuntimeError as e:
            msg = str(e)
            assert "500" in msg
            assert "request failed" in msg.lower()
            assert "test-key-not-real" not in msg
            assert "Internal Server Error" not in msg


def test_groq_provider_network_error_is_safe():
    """Transport failures surface a safe category without leaking internals."""
    mock_post = MagicMock(side_effect=Exception("connection refused to api.groq.com:443"))

    with patch.dict("sys.modules", {"requests": MagicMock(post=mock_post)}):
        provider = GroqProvider(api_key="test-key-not-real")
        try:
            provider.generate("test")
            assert False, "Should have raised RuntimeError"
        except RuntimeError as e:
            msg = str(e)
            assert "network" in msg.lower()
            assert "test-key-not-real" not in msg
            assert "connection refused" not in msg
            assert "api.groq.com" not in msg


def test_groq_provider_classify_error_helper():
    """Directly verify the safe status-code -> category mapping."""
    classify = GroqProvider._classify_error
    assert classify(200) is None
    assert classify(201) is None
    assert "authentication" in classify(401).lower()
    assert "authentication" in classify(403).lower()
    assert "endpoint/model" in classify(404).lower()
    assert "rate limit" in classify(429).lower()
    assert "404" in classify(404)
    assert "500" in classify(500)
    assert "status" in classify(400).lower()
