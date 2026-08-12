from __future__ import annotations

from typing import Dict, Any, List


def collect_evidence(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    evidence: List[Dict[str, Any]] = []
    # collect SQL evidence
    sql = state.get("sql_results")
    if sql:
        evidence.append({"source": "sql", "summary": "SQL query results", "rows": sql.get("row_count", 0)})

    # collect RAG evidence
    docs = state.get("retrieved_documents", []) or []
    for d in docs:
        # expect d to have metadata with source/page/chunk_id if available
        evidence.append({"source": "rag", "doc": d})

    # calculator results
    calc = state.get("calculations", {})
    if calc:
        evidence.append({"source": "calculator", "results": calc})

    # data analysis
    da = state.get("tool_results", {}).get("data_analysis")
    if da:
        evidence.append({"source": "data_analysis", "results": da})

    state["evidence"] = evidence
    return evidence
