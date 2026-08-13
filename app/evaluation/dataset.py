"""Evaluation dataset for the Enterprise AI Operations Agent.

This module defines a small set of representative test cases covering
different tool routing scenarios for deterministic evaluation.
"""

from typing import Dict, List, Any


class EvaluationCase:
    """Represents a single evaluation test case."""
    
    def __init__(
        self,
        query: str,
        expected_tools: List[str],
        description: str = "",
    ):
        self.query = query
        self.expected_tools = expected_tools
        self.description = description


# Evaluation dataset covering different tool routing scenarios
EVALUATION_DATASET: List[EvaluationCase] = [
    # SQL-only questions
    EvaluationCase(
        query="What was July revenue?",
        expected_tools=["sql"],
        description="Simple revenue query - should route to SQL only",
    ),
    EvaluationCase(
        query="What was June revenue?",
        expected_tools=["sql"],
        description="June revenue query - should route to SQL only",
    ),
    
    # RAG-only questions
    EvaluationCase(
        query="What is the inventory reorder policy?",
        expected_tools=["rag"],
        description="Policy question - should route to RAG only",
    ),
    EvaluationCase(
        query="Explain the SOP for vendor management.",
        expected_tools=["rag"],
        description="SOP question - should route to RAG only",
    ),
    
    # Calculator/mathematical questions
    EvaluationCase(
        query="What percentage did revenue increase from June to July?",
        expected_tools=["sql", "calculator"],
        description="Percentage calculation - needs SQL data and calculator",
    ),
    EvaluationCase(
        query="Calculate the growth rate in inventory cost from June to July.",
        expected_tools=["sql", "calculator"],
        description="Growth rate calculation - needs SQL data and calculator",
    ),
    
    # Multi-tool questions (SQL + RAG)
    EvaluationCase(
        query="Why did inventory cost increase in July and does this violate policy?",
        expected_tools=["sql", "rag"],
        description="Multi-tool: SQL for data, RAG for policy violation check",
    ),
]


def get_evaluation_dataset() -> List[EvaluationCase]:
    """Return the evaluation dataset."""
    return EVALUATION_DATASET