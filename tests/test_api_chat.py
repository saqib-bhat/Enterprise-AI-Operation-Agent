"""Tests for the FastAPI chat endpoint."""

from fastapi.testclient import TestClient

from app.api.main import app
from app.config import settings

client = TestClient(app)


def setup_mock_provider(monkeypatch):
    """Configure the LLM provider to use mock mode."""
    monkeypatch.setattr(settings, "llm_provider", "mock")
    # Reset factory cache
    import app.llm.factory as _f
    _f._provider_instance = None


def test_chat_success(monkeypatch):
    """Test successful chat request."""
    setup_mock_provider(monkeypatch)
    
    response = client.post("/chat", json={"query": "What was July revenue?"})
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "query" in data
    assert "answer" in data
    assert "tools_used" in data
    assert "evidence" in data
    assert "verification" in data
    assert "errors" in data
    assert "latency" in data
    
    # Verify query is echoed back
    assert data["query"] == "What was July revenue?"
    
    # Verify answer is not empty
    assert isinstance(data["answer"], str)
    assert len(data["answer"]) > 0
    
    # Verify tools_used is a list
    assert isinstance(data["tools_used"], list)
    
    # Verify evidence is a list
    assert isinstance(data["evidence"], list)
    
    # Verify verification is a dict
    assert isinstance(data["verification"], dict)
    
    # Verify errors is a list
    assert isinstance(data["errors"], list)
    
    # Verify latency is a dict
    assert isinstance(data["latency"], dict)


def test_chat_empty_query(monkeypatch):
    """Test that empty query is rejected."""
    setup_mock_provider(monkeypatch)
    
    response = client.post("/chat", json={"query": ""})
    
    assert response.status_code == 422  # Validation error


def test_chat_missing_query(monkeypatch):
    """Test that missing query is rejected."""
    setup_mock_provider(monkeypatch)
    
    response = client.post("/chat", json={})
    
    assert response.status_code == 422  # Validation error


def test_chat_error_handling(monkeypatch):
    """Test that errors from agent are captured in response."""
    setup_mock_provider(monkeypatch)
    
    # This query should trigger SQL and potentially other tools
    response = client.post("/chat", json={"query": "What was July revenue?"})
    
    assert response.status_code == 200
    data = response.json()
    
    # Even if there are errors, the response should still be valid
    assert "errors" in data
    assert isinstance(data["errors"], list)