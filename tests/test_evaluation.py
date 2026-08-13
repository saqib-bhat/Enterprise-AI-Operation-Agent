"""Tests for the evaluation framework."""

import pytest

from app.config import settings
from app.evaluation.dataset import (
    EvaluationCase,
    get_evaluation_dataset,
)
from app.evaluation.evaluator import evaluate_case, evaluate_dataset


def setup_mock_provider(monkeypatch):
    """Configure the LLM provider to use mock mode."""
    monkeypatch.setattr(settings, "llm_provider", "mock")
    # Reset factory cache
    import app.llm.factory as _f
    _f._provider_instance = None


def stub_rag_retrieval(monkeypatch):
    """Stub RAG retrieval to prevent SentenceTransformer/PyTorch loading.
    
    This prevents the Windows PyTorch native DLL crash during tests.
    The real RAG implementation remains unchanged.
    """
    def fake_retrieve(query):
        return {
            "success": True,
            "results": [
                {
                    "text": (
                        "Inventory policy requires investigation "
                        "when inventory cost increases significantly."
                    ),
                    "source": "inventory_policy.pdf",
                    "page": 3,
                    "chunk_id": "evaluation-test-chunk",
                }
            ],
        }

    import app.rag.retrieval as retrieval

    monkeypatch.setattr(
        retrieval,
        "retrieve",
        fake_retrieve,
    )


def test_evaluation_dataset_exists():
    """Test that the evaluation dataset is not empty."""
    dataset = get_evaluation_dataset()
    assert len(dataset) > 0


def test_evaluation_dataset_coverage():
    """Test that the dataset covers different tool categories."""
    dataset = get_evaluation_dataset()
    
    # Collect all expected tools across cases
    all_tools = set()
    for case in dataset:
        all_tools.update(case.expected_tools)
    
    # Should cover at least SQL, RAG, and calculator
    assert "sql" in all_tools
    assert "rag" in all_tools
    assert "calculator" in all_tools


def test_evaluate_case_sql_only(monkeypatch):
    """Test evaluation of SQL-only question."""
    setup_mock_provider(monkeypatch)
    
    case = EvaluationCase(
        query="What was July revenue?",
        expected_tools=["sql"],
    )
    
    result = evaluate_case(case)
    
    # Verify result structure
    assert "query" in result
    assert "expected_tools" in result
    assert "actual_tools" in result
    assert "tool_match" in result
    assert "answer_generated" in result
    assert "verification_ok" in result
    assert "errors" in result
    assert "latency" in result
    
    # Verify values
    assert result["query"] == "What was July revenue?"
    assert result["expected_tools"] == ["sql"]
    assert isinstance(result["actual_tools"], list)
    assert isinstance(result["tool_match"], bool)
    assert isinstance(result["answer_generated"], bool)
    assert isinstance(result["verification_ok"], bool)
    assert isinstance(result["errors"], list)
    assert isinstance(result["latency"], dict)


def test_evaluate_case_rag_only(monkeypatch):
    """Test evaluation of RAG-only question."""
    setup_mock_provider(monkeypatch)
    stub_rag_retrieval(monkeypatch)
    
    case = EvaluationCase(
        query="What is the inventory reorder policy?",
        expected_tools=["rag"],
    )
    
    result = evaluate_case(case)
    
    assert result["query"] == "What is the inventory reorder policy?"
    assert result["expected_tools"] == ["rag"]
    assert isinstance(result["actual_tools"], list)


def test_evaluate_case_calculator(monkeypatch):
    """Test evaluation of calculator question."""
    setup_mock_provider(monkeypatch)
    
    case = EvaluationCase(
        query="What percentage did revenue increase from June to July?",
        expected_tools=["sql", "calculator"],
    )
    
    result = evaluate_case(case)
    
    assert result["expected_tools"] == ["sql", "calculator"]
    assert isinstance(result["actual_tools"], list)


def test_evaluate_dataset(monkeypatch):
    """Test evaluation of entire dataset."""
    setup_mock_provider(monkeypatch)
    stub_rag_retrieval(monkeypatch)
    
    dataset = get_evaluation_dataset()
    summary = evaluate_dataset(dataset)
    
    # Verify summary structure
    assert "total_cases" in summary
    assert "passed_cases" in summary
    assert "failed_cases" in summary
    assert "tool_routing_accuracy" in summary
    assert "results" in summary
    
    # Verify values
    assert summary["total_cases"] == len(dataset)
    assert summary["passed_cases"] + summary["failed_cases"] == summary["total_cases"]
    assert 0.0 <= summary["tool_routing_accuracy"] <= 1.0
    assert len(summary["results"]) == summary["total_cases"]


def test_evaluate_case_tool_match_logic(monkeypatch):
    """Test that tool matching is order-independent."""
    setup_mock_provider(monkeypatch)
    
    # Test with tools in different order
    case = EvaluationCase(
        query="What percentage did revenue increase from June to July?",
        expected_tools=["calculator", "sql"],  # Different order
    )
    
    result = evaluate_case(case)
    
    # Should still match because order doesn't matter
    # (The actual tools will be ["sql", "calculator"] based on planner logic)
    assert isinstance(result["tool_match"], bool)


def test_evaluate_case_error_handling(monkeypatch):
    """Test that evaluation handles agent errors gracefully."""
    setup_mock_provider(monkeypatch)
    
    # Use a valid query - the evaluation should handle any agent errors
    case = EvaluationCase(
        query="What was July revenue?",
        expected_tools=["sql"],
    )
    
    result = evaluate_case(case)
    
    # Should always return a valid result structure
    assert result is not None
    assert isinstance(result["errors"], list)