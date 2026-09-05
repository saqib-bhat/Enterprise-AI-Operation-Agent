from __future__ import annotations

from typing import Dict, Any

from app.config import settings


def verify(state: Dict[str, Any]) -> Dict[str, Any]:
    """Perform lightweight verification of claims against tool evidence."""

    previous_verification = state.get("verification_result", {})
    attempts = previous_verification.get("attempts", 0)

    if attempts >= settings.max_verification_attempts:
        return {
            "ok": False,
            "reasons": ["max_attempts_exceeded"],
            "attempts": attempts + 1,
        }

    evidence = state.get("evidence", []) or []
    tool_results = state.get("tool_results", {}) or {}
    selected_tools = state.get("selected_tools", []) or []

    ok = bool(selected_tools)
    reasons = []

    if not selected_tools:
        reasons.append("No tool was selected for this request")

    # ---------------------------------------------------------
    # Tool execution checks
    # ---------------------------------------------------------
    for tool in selected_tools:

        tool_result = tool_results.get(tool, {})

        # Calculator stores results per operation.
        if tool == "calculator":

            if not isinstance(tool_result, dict) or not tool_result:
                ok = False
                reasons.append(
                    "Tool 'calculator' did not succeed"
                )
                continue

            for operation_result in tool_result.values():

                if (
                    not isinstance(operation_result, dict)
                    or not operation_result.get("success", False)
                ):
                    ok = False
                    reasons.append(
                        "Tool 'calculator' did not succeed"
                    )
                    break

        # All other tools use a top-level success field.
        elif isinstance(tool_result, dict):

            if not tool_result.get("success", False):
                ok = False
                reasons.append(
                    f"Tool '{tool}' did not succeed"
                )

    # ---------------------------------------------------------
    # Calculator evidence
    # ---------------------------------------------------------
    if state.get("calculations"):

        has_calculator_evidence = any(
            isinstance(item, dict)
            and item.get("source") == "calculator"
            for item in evidence
        )

        if not has_calculator_evidence:
            ok = False
            reasons.append(
                "Calculation results missing from evidence"
            )

    # ---------------------------------------------------------
    # RAG verification
    # ---------------------------------------------------------
    if "rag" in selected_tools:

        rag_result = tool_results.get("rag", {})

        # RAG itself must execute successfully.
        if not isinstance(rag_result, dict):
            ok = False
            reasons.append(
                "RAG returned an invalid result"
            )

        elif not rag_result.get("success", False):
            ok = False
            reasons.append(
                "RAG retrieval failed"
            )

        else:

            rag_results = rag_result.get("results", [])

            # A successful RAG call with zero documents is
            # valid execution but insufficient evidence.
            if not isinstance(rag_results, list):
                ok = False
                reasons.append(
                    "RAG returned invalid results"
                )

            elif len(rag_results) == 0:
                ok = False
                reasons.append(
                    "RAG retrieval succeeded but returned "
                    "no relevant documents"
                )

            else:

                # Verify that the retrieved documents were
                # actually converted into evidence.
                rag_evidence = [
                    item
                    for item in evidence
                    if (
                        isinstance(item, dict)
                        and item.get("source") == "rag"
                    )
                ]

                if not rag_evidence:
                    ok = False
                    reasons.append(
                        "RAG results are missing from evidence"
                    )

    # ---------------------------------------------------------
    # SQL verification
    # ---------------------------------------------------------
    if "sql" in selected_tools:

        sql_results = state.get("sql_results")

        if not sql_results:
            ok = False
            reasons.append(
                "SQL selected but no results"
            )

        elif (
            isinstance(sql_results, dict)
            and not sql_results.get("success", False)
        ):
            ok = False
            reasons.append(
                "SQL execution failed"
            )

    # ---------------------------------------------------------
    # Final verification result
    # ---------------------------------------------------------
    result = {
        "ok": ok,
        "reasons": reasons,
        "attempts": attempts + 1,
    }

    state["verification_result"] = result

    return result