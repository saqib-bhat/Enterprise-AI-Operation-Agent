from __future__ import annotations

from typing import Dict, Any
from app.config import settings


def verify(state: Dict[str, Any]) -> Dict[str, Any]:
    """Perform lightweight verification of claims against evidence in state."""
    attempts = state.get("verification_result", {}).get("attempts", 0)
    if attempts >= settings.max_verification_attempts:
        return {"ok": False, "reason": "max_attempts_exceeded"}

    ev = state.get("evidence", [])
    tool_results = state.get("tool_results", {})
    selected_tools = state.get("selected_tools", [])

    # Basic checks
    ok = True
    reasons = []

    # Check if any selected tool failed
    for tool in selected_tools:
        tool_result = tool_results.get(tool, {})

        if tool == "calculator":
            # Calculator stores results per operation rather than
            # using a top-level "success" field.
            if not isinstance(tool_result, dict) or not tool_result:
                ok = False
                reasons.append("Tool 'calculator' did not succeed")
                continue

            calculator_failed = False

            for operation_result in tool_result.values():
                if (
                    not isinstance(operation_result, dict)
                    or not operation_result.get("success", False)
                ):
                    calculator_failed = True
                    break

            if calculator_failed:
                ok = False
                reasons.append("Tool 'calculator' did not succeed")

        elif isinstance(tool_result, dict) and not tool_result.get("success", False):
            ok = False
            reasons.append(f"Tool '{tool}' did not succeed")
    # If calculations are present, ensure calculation results exist
    if state.get("calculations") and not any(e.get("source") == "calculator" for e in ev):
        ok = False
        reasons.append("Calculation results missing from evidence")

    # If RAG was selected, ensure retrieved_documents exist and are successful
    if "rag" in selected_tools:
        retrieved_docs = state.get("retrieved_documents", [])
        if not retrieved_docs:
            ok = False
            reasons.append("RAG selected but no documents retrieved")
        elif any(doc.get("success") is False for doc in retrieved_docs):
            ok = False
            reasons.append("RAG retrieval failed")

    # If SQL selected, ensure sql_results exist and are successful
    if "sql" in selected_tools:
        sql_results = state.get("sql_results")
        if not sql_results:
            ok = False
            reasons.append("SQL selected but no results")
        elif isinstance(sql_results, dict) and not sql_results.get("success", False):
            ok = False
            reasons.append("SQL execution failed")

    res = {"ok": ok, "reasons": reasons, "attempts": attempts + 1}
    state["verification_result"] = res
    return res
