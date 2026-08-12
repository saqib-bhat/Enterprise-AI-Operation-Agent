from __future__ import annotations

from typing import List, Dict, Any

ALLOWED_TOOLS = {"sql", "rag", "calculator", "data_analysis"}


def route(plan: List[str]) -> List[str]:
    """Validate and convert planner output into an ordered list of tools to run."""
    selected: List[str] = []
    for p in plan:
        if p not in ALLOWED_TOOLS:
            raise ValueError(f"Invalid tool selection: {p}")
        if p not in selected:
            selected.append(p)
    return selected
