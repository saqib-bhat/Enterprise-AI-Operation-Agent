"""Deterministic evaluation framework for the Enterprise AI Operations Agent.

This module provides evaluation functions that run the existing LangGraph agent
and compare its behavior against expected outcomes in a deterministic manner.
"""

from typing import Dict, List, Any, Optional

from app.agent.graph import run_graph
from app.evaluation.dataset import EvaluationCase


def evaluate_case(case: EvaluationCase) -> Dict[str, Any]:
    """Evaluate a single test case against the agent.
    
    Runs the existing run_graph() and compares the actual tool selection
    against expected tools. Records whether an answer was produced,
    verification status, and captures any errors.
    
    Args:
        case: EvaluationCase with query and expected tools
        
    Returns:
        Dictionary with structured evaluation results:
        {
            "query": str,
            "expected_tools": list[str],
            "actual_tools": list[str],
            "tool_match": bool,
            "answer_generated": bool,
            "verification_ok": bool,
            "errors": list[str],
            "latency": dict[str, float],
        }
    """
    try:
        # Run the existing LangGraph agent
        state = run_graph(case.query)
        
        # Extract actual tools selected
        actual_tools = state.get("selected_tools", [])
        
        # Check if tool selection matches expected (order-independent)
        tool_match = set(actual_tools) == set(case.expected_tools)
        
        # Check if answer was generated
        answer_generated = bool(state.get("final_answer"))
        
        # Check verification status
        verification_result = state.get("verification_result", {})
        verification_ok = verification_result.get("ok", False)
        
        # Capture errors
        errors = state.get("errors", [])
        
        # Capture latency
        latency = state.get("latency", {})
        
        return {
            "query": case.query,
            "expected_tools": case.expected_tools,
            "actual_tools": actual_tools,
            "tool_match": tool_match,
            "answer_generated": answer_generated,
            "verification_ok": verification_ok,
            "errors": errors,
            "latency": latency,
        }
        
    except Exception as e:
        # Return structured error result
        return {
            "query": case.query,
            "expected_tools": case.expected_tools,
            "actual_tools": [],
            "tool_match": False,
            "answer_generated": False,
            "verification_ok": False,
            "errors": ["Agent execution failed"],
            "latency": {},
        }


def evaluate_dataset(
    cases: List[EvaluationCase],
) -> Dict[str, Any]:
    """Evaluate the entire dataset.
    
    Args:
        cases: List of EvaluationCase objects
        
    Returns:
        Dictionary with aggregate summary:
        {
            "total_cases": int,
            "passed_cases": int,
            "failed_cases": int,
            "tool_routing_accuracy": float,
            "results": list[dict],  # Individual case results
        }
    """
    results = []
    passed_cases = 0
    
    for case in cases:
        result = evaluate_case(case)
        results.append(result)
        
        # A case passes if tool routing is correct and answer was generated
        if result["tool_match"] and result["answer_generated"]:
            passed_cases += 1
    
    total_cases = len(cases)
    failed_cases = total_cases - passed_cases
    tool_routing_accuracy = (
        sum(1 for r in results if r["tool_match"]) / total_cases
        if total_cases > 0
        else 0.0
    )
    
    return {
        "total_cases": total_cases,
        "passed_cases": passed_cases,
        "failed_cases": failed_cases,
        "tool_routing_accuracy": tool_routing_accuracy,
        "results": results,
    }