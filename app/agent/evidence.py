from __future__ import annotations

from typing import Dict, Any, List


def collect_evidence(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Collect structured evidence produced by the agent tools."""

    evidence: List[Dict[str, Any]] = []

    # ---------------------------------------------------------
    # SQL evidence
    # ---------------------------------------------------------
    sql = state.get("sql_results")

    if sql:
        evidence.append(
            {
                "source": "sql",
                "summary": "SQL query results",
                "columns": sql.get("columns", []),
                "rows": sql.get("rows", []),
                "row_count": sql.get("row_count", 0),
            }
        )

    # ---------------------------------------------------------
    # RAG evidence
    # ---------------------------------------------------------
    docs = state.get("retrieved_documents", []) or []

    for doc in docs:
        if not isinstance(doc, dict):
            continue

        # Handle failed retrieval results.
        if doc.get("success") is False:
            evidence.append(
                {
                    "source": "rag",
                    "summary": "RAG retrieval failed",
                    "error": doc.get("error", "Unknown RAG error"),
                }
            )
            continue

        # RAG documents may expose metadata directly or inside
        # a metadata dictionary depending on the retrieval layer.
        metadata = doc.get("metadata", {})

        if not isinstance(metadata, dict):
            metadata = {}

        source = (
            doc.get("source")
            or metadata.get("source")
            or "Unknown document"
        )

        page = (
            doc.get("page")
            or metadata.get("page")
        )

        chunk_id = (
            doc.get("chunk_id")
            or metadata.get("chunk_id")
        )

        text = (
            doc.get("text")
            or metadata.get("text")
            or ""
        )

        chunk_index = (
            doc.get("chunk_index")
            or metadata.get("chunk_index")
        )

        rag_evidence = {
            "source": "rag",
            "document": source,
            "page": page,
            "chunk_id": chunk_id,
            "chunk_index": chunk_index,
            "text": text,
        }

        # Remove fields that have no value.
        rag_evidence = {
            key: value
            for key, value in rag_evidence.items()
            if value is not None and value != ""
        }

        evidence.append(rag_evidence)

    # ---------------------------------------------------------
    # Calculator evidence
    # ---------------------------------------------------------
    calculations = state.get("calculations", {})

    if calculations:
        evidence.append(
            {
                "source": "calculator",
                "results": calculations,
            }
        )

    # ---------------------------------------------------------
    # Data analysis evidence
    # ---------------------------------------------------------
    tool_results = state.get("tool_results", {})
    data_analysis = tool_results.get("data_analysis")

    if data_analysis:
        evidence.append(
            {
                "source": "data_analysis",
                "results": data_analysis,
            }
        )

    # Store evidence back into state.
    state["evidence"] = evidence

    return evidence