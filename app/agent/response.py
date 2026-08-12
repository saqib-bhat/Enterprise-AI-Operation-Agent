from __future__ import annotations

from typing import Dict, Any
from app.llm.factory import get_provider


def generate_response(state: Dict[str, Any]) -> Dict[str, Any]:
    provider = get_provider()
    # Build a factual response payload from state — avoid fabrication
    answer = state.get("final_answer") or ""
    key_findings = []
    for e in state.get("evidence", []):
        key_findings.append({"source": e.get("source"), "summary": e.get("summary") or e.get("results") or e.get("doc")})

    payload = {
        "Answer": answer,
        "Key Findings": key_findings,
        "Evidence": state.get("evidence", []),
        "Sources": [e.get("source") for e in state.get("evidence", [])],
        "Tools Used": state.get("selected_tools", []),
        "Limitations": "Responses are based on tool outputs and may be incomplete.",
    }

    # Optionally call LLM to produce a polished textual answer (MockProvider in tests)
    if provider:
        prompt = f"Draft a concise answer using the following payload: {payload}"
        resp = provider.generate(prompt)
        text = (resp or {}).get("text")
        if text:
            payload["Answer"] = text

    state["final_response"] = payload
    return payload
