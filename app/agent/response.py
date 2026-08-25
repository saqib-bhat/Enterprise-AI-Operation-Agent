from __future__ import annotations

from typing import Dict, Any, Optional
from app.llm.factory import get_provider


def _build_sql_summary(sql_results: Dict[str, Any]) -> str:
    """Build a human-readable summary from SQL results."""
    if not sql_results or not sql_results.get("success"):
        return "SQL query did not succeed"

    columns = sql_results.get("columns", [])
    rows = sql_results.get("rows", [])

    summaries = []
    for row in rows:
        for col, val in zip(columns, row):
            if val is not None:
                summaries.append(f"{col}: {val}")

    return "; ".join(summaries) if summaries else "No data returned"


def _build_calculator_summary(calculations: Dict[str, Any]) -> str:
    """Build a summary from calculator results."""
    if not calculations:
        return ""

    parts = []
    for op, result in calculations.items():
        if isinstance(result, dict) and result.get("success"):
            value = result.get("result")
            if value is not None:
                parts.append(f"{op}: {value}")

    return "; ".join(parts) if parts else ""


def _build_rag_summary(retrieved_documents: list) -> str:
    """Build a summary from RAG retrieved documents."""
    if not retrieved_documents:
        return "No documents retrieved"

    texts = []
    for doc in retrieved_documents:
        if isinstance(doc, dict):
            if doc.get("success") is False:
                return f"RAG retrieval failed: {doc.get('error', 'unknown error')}"
            text = doc.get("text", "")
            if text:
                texts.append(text)

    return " ".join(texts) if texts else "No document content available"


def _build_grounding_prompt(
    query: str,
    selected_tools: list,
    sql_results: Optional[Dict],
    calculations: Optional[Dict],
    retrieved_documents: Optional[list],
    evidence: Optional[list],
) -> str:
    """Build a grounded prompt for the LLM with strict instructions."""

    parts = []
    parts.append(f"Question: {query}")
    parts.append("")
    parts.append("TOOL RESULTS:")

    if sql_results and sql_results.get("success"):
        sql_summary = _build_sql_summary(sql_results)
        parts.append(f"  SQL Data: {sql_summary}")

    if calculations:
        calc_summary = _build_calculator_summary(calculations)
        if calc_summary:
            parts.append(f"  Calculations: {calc_summary}")

    if retrieved_documents:
        rag_summary = _build_rag_summary(retrieved_documents)
        parts.append(f"  Retrieved Documents: {rag_summary}")

    parts.append("")
    parts.append("TOOLS USED: " + ", ".join(selected_tools) if selected_tools else "None")
    parts.append("")

    parts.append("INSTRUCTIONS:")
    parts.append("- Use ONLY the tool results above to answer the question.")
    parts.append("- Do NOT invent numbers, facts, or policy statements.")
    parts.append("- If the tool results are insufficient to answer, explicitly say so.")
    parts.append("- Give a concise, factual, business-oriented answer.")
    parts.append("- Do NOT mention internal implementation details.")
    parts.append("")
    parts.append("Answer:")

    return "\n".join(parts)


def generate_response(state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Generate a grounded response based on verified tool results.

    This function:
    1. Checks verification status - does not fabricate answers if verification failed
    2. Builds a factual payload from tool results (SQL, calculations, RAG)
    3. Uses the LLM provider to generate a concise, grounded answer
    4. Falls back to deterministic answers if the provider fails
    """
    query = state.get("user_query", "")
    selected_tools = state.get("selected_tools", [])
    sql_results = state.get("sql_results")
    calculations = state.get("calculations")
    retrieved_documents = state.get("retrieved_documents", [])
    evidence = state.get("evidence", [])
    verification_result = state.get("verification_result", {})

    # If verification failed, do not fabricate an answer
    if not verification_result.get("ok", False):
        safe_answer = "A verified answer could not be generated based on the available tool results."
        return {
            "Answer": safe_answer,
            "Key Findings": [],
            "Evidence": evidence,
            "Sources": [e.get("source") for e in evidence if e.get("source")],
            "Tools Used": selected_tools,
            "Limitations": "Verification failed - answer could not be confirmed.",
        }

    # Build the grounding prompt from actual tool results
    prompt = _build_grounding_prompt(
        query=query,
        selected_tools=selected_tools,
        sql_results=sql_results,
        calculations=calculations,
        retrieved_documents=retrieved_documents,
        evidence=evidence,
    )

    # Try to generate a polished answer using the LLM provider
    llm_answer = None
    try:
        provider = get_provider()
        if provider:
            resp = provider.generate(prompt)
            text = (resp or {}).get("text")
            if text and isinstance(text, str):
                llm_answer = text
    except Exception:
        # Provider failed - we'll fall back to deterministic answer
        pass

    # Build key findings from evidence
    key_findings = []
    for e in evidence:
        if isinstance(e, dict):
            source = e.get("source")
            summary = e.get("summary") or e.get("results") or e.get("doc")
            if source or summary:
                key_findings.append({
                    "source": source,
                    "summary": summary if isinstance(summary, (str, dict)) else str(summary),
                })

    # Determine the final answer
    if llm_answer:
        final_answer = llm_answer
    else:
        # Fallback: construct a deterministic answer from tool results
        if sql_results and sql_results.get("success"):
            sql_summary = _build_sql_summary(sql_results)
            final_answer = f"Based on SQL data: {sql_summary}"
        elif retrieved_documents:
            rag_summary = _build_rag_summary(retrieved_documents)
            if rag_summary and not rag_summary.startswith("RAG retrieval failed"):
                final_answer = f"Based on retrieved documents: {rag_summary[:200]}..."
            else:
                final_answer = "Tool results were available but could not be synthesized into an answer."
        elif calculations:
            calc_summary = _build_calculator_summary(calculations)
            final_answer = f"Based on calculations: {calc_summary}" if calc_summary else "Calculations were performed but no result was produced."
        else:
            final_answer = "The query was processed but no specific data was available to provide a factual answer."

    return {
        "Answer": final_answer,
        "Key Findings": key_findings,
        "Evidence": evidence,
        "Sources": [e.get("source") for e in evidence if e.get("source")],
        "Tools Used": selected_tools,
        "Limitations": "Responses are based on tool outputs and may be incomplete.",
    }
