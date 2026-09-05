from __future__ import annotations

import re
from typing import Dict, Any, List


def _build_excerpt(text: Any, query: str = "", limit: int = 220) -> str:
    """Return a short, readable evidence excerpt without exposing full pages."""
    excerpt = " ".join(str(text or "").split())
    if len(excerpt) <= limit:
        return excerpt

    query_terms = sorted(
        {
            term.lower()
            for term in re.findall(r"[A-Za-z0-9]+", query)
            if len(term) >= 6
            and term.lower() not in {
                "inventory",
                "document",
                "policy",
                "question",
                "process",
                "procedures",
            }
        },
        key=len,
        reverse=True,
    )

    start = 0
    lowered = excerpt.lower()
    for term in query_terms:
        position = lowered.find(term)
        if position >= 0:
            start = max(0, position - 60)
            break

    snippet = excerpt[start : start + limit]
    if start > 0:
        snippet = "..." + snippet.lstrip()
    if start + limit < len(excerpt):
        snippet = snippet.rstrip() + "..."
    return snippet


def collect_evidence(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Collect structured evidence produced by the agent tools."""

    evidence: List[Dict[str, Any]] = []
    query = state.get("user_query", "")

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

        # -----------------------------------------------------
        # RAG result wrapper
        #
        # Example:
        # {
        #     "success": True,
        #     "results": [...]
        # }
        # -----------------------------------------------------
        if "results" in doc:

            if doc.get("success") is False:
                evidence.append(
                    {
                        "source": "rag",
                        "summary": "RAG retrieval failed",
                        "error": doc.get(
                            "error",
                            "Unknown RAG error",
                        ),
                    }
                )
                continue

            rag_results = doc.get("results", [])

            if not isinstance(rag_results, list):
                continue

            # Empty retrieval means NO evidence.
            for result in rag_results:

                if not isinstance(result, dict):
                    continue

                source = result.get("source")
                page = result.get("page")
                text = result.get("text")

                # Do not create fake "Unknown document" evidence.
                if not source and not text:
                    continue

                rag_evidence = {
                    "source": "rag",
                    "document": source,
                    "page": page,
                    "excerpt": _build_excerpt(text, query),
                }

                rag_evidence = {
                    key: value
                    for key, value in rag_evidence.items()
                    if value is not None and value != ""
                }

                evidence.append(rag_evidence)

            continue

        # -----------------------------------------------------
        # Direct RAG document
        # -----------------------------------------------------
        metadata = doc.get("metadata", {})

        if not isinstance(metadata, dict):
            metadata = {}

        source = (
            doc.get("source")
            or metadata.get("source")
        )

        page = (
            doc.get("page")
            or metadata.get("page")
        )

        text = (
            doc.get("text")
            or metadata.get("text")
            or ""
        )

        # Do not create evidence for an empty/invalid document.
        if not source and not text:
            continue

        rag_evidence = {
            "source": "rag",
            "document": source,
            "page": page,
            "excerpt": _build_excerpt(text, query),
        }

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

    # ---------------------------------------------------------
    # Store evidence back into state
    # ---------------------------------------------------------
    state["evidence"] = evidence

    return evidence