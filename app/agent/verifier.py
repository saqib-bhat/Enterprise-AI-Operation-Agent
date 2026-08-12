from __future__ import annotations

from typing import Dict, Any
from app.config import settings


def verify(state: Dict[str, Any]) -> Dict[str, Any]:
    """Perform lightweight verification of claims against evidence in state."""
    attempts = state.get("verification_result", {}).get("attempts", 0)
    if attempts >= settings.max_verification_attempts:
        return {"ok": False, "reason": "max_attempts_exceeded"}

    ev = state.get("evidence", [])
    # Basic checks
    ok = True
    reasons = []

    # If calculations are present, ensure calculation results exist
    if state.get("calculations") and not any(e.get("source") == "calculator" for e in ev):
        ok = False
        reasons.append("Calculation results missing from evidence")

    # If RAG was selected, ensure retrieved_documents exist
    if "rag" in state.get("selected_tools", []) and not state.get("retrieved_documents"):
        ok = False
        reasons.append("RAG selected but no documents retrieved")

    # If SQL selected, ensure sql_results exist
    if "sql" in state.get("selected_tools", []) and not state.get("sql_results"):
        ok = False
        reasons.append("SQL selected but no results")

    res = {"ok": ok, "reasons": reasons, "attempts": attempts + 1}
    state["verification_result"] = res
    return res
