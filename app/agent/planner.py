from __future__ import annotations

from typing import List

from app.llm.factory import get_provider
from app.llm.providers import MockProvider


def determine_plan(user_query: str) -> List[str]:
    """Determine which tools are required for the user query.

    MockProvider mode uses deterministic heuristics so tests do not require
    network access or an LLM API.
    """
    provider = get_provider()

    if isinstance(provider, MockProvider):
        q = user_query.lower()
        plan = []

        # SQL is required for structured business/data questions.
        # But avoid SQL for pure policy/document questions that only need RAG.
        has_policy_words = any(
            word in q
            for word in ("policy", "sop", "procedure", "rule")
        )
        has_data_words = any(
            word in q
            for word in (
                "revenue",
                "sales",
                "compare",
                "percentage",
                "increase",
                "decrease",
                "cost",
                "vendor",
            )
        )
        # "inventory" alone should not trigger SQL if it's a policy question
        has_inventory = "inventory" in q

        if (has_data_words or (has_inventory and not has_policy_words)):
            plan.append("sql")

        # RAG is required for document/policy questions.
        if any(
            word in q
            for word in (
                "policy",
                "sop",
                "procedure",
                "rule",
                "violate",
                "violation",
                "why",
                "explain",
                "reason",
            )
        ):
            plan.append("rag")

        # Calculator is required for numerical calculations.
        if any(
            word in q
            for word in (
                "percentage",
                "percent",
                "growth",
                "increase",
                "decrease",
                "change",
            )
        ):
            if "sql" not in plan:
                plan.append("sql")

            plan.append("calculator")

        # Data analysis for explicit trend/analysis questions.
        if any(
            word in q
            for word in (
                "trend",
                "analysis",
                "analyze",
            )
        ):
            plan.append("data_analysis")

        # Remove duplicates while preserving order.
        seen = set()

        return [
            tool
            for tool in plan
            if not (tool in seen or seen.add(tool))
        ]

        # Production/non-mock mode.
    # The LLM proposes tools, but deterministic business rules validate
    # the proposal before execution. This prevents unnecessary tools
    # from being selected for simple retrieval questions.

    prompt = (
        f"Produce a comma-separated list of tools to answer: {user_query}. "
        "Allowed: sql, rag, calculator, data_analysis. "
        "Rules: "
        "Use sql for structured business data retrieval. "
        "Use rag for policies, SOPs, procedures, rules, and documents. "
        "Use calculator only when an actual mathematical calculation or "
        "derived numerical result is required. "
        "Use multiple tools only when each tool performs a necessary task. "
        "Respond with tools only."
    )

    response = provider.generate(prompt)
    text = (response or {}).get("text", "")

    tools = [
        tool.strip().lower()
        for tool in text.split(",")
        if tool.strip()
    ]

    allowed = {
        "sql",
        "rag",
        "calculator",
        "data_analysis",
    }

    tools = [tool for tool in tools if tool in allowed]

    # ---------------------------------------------------------
    # Deterministic routing constraints
    # ---------------------------------------------------------
    q = user_query.lower()

    has_policy_words = any(
        word in q
        for word in ("policy", "sop", "procedure", "rule")
    )

    has_data_words = any(
        word in q
        for word in (
            "revenue",
            "sales",
            "cost",
            "vendor",
            "inventory",
            "profit",
            "expense",
        )
    )

    has_rag_intent = any(
        word in q
        for word in (
            "policy",
            "sop",
            "procedure",
            "rule",
            "violate",
            "violation",
            "why",
            "explain",
            "reason",
            "document",
        )
    )

    has_calculation_words = any(
        word in q
        for word in (
            "percentage",
            "percent",
            "calculate",
            "calculation",
            "divide",
            "divided",
            "multiplied",
            "multiply",
            "times",
            "ratio",
            "average",
            "difference",
            "subtract",
            "add",
            "sum",
        )
    ) or any(
        symbol in q
        for symbol in ("%", "*", "/", "+", "-")
    )

    # Policy/document questions should not use SQL or calculator
    # unless the query explicitly asks for business data as well.
    if has_policy_words and not any(
        word in q
        for word in (
            "revenue",
            "sales",
            "cost",
            "profit",
            "expense",
        )
    ):
        tools = [
            tool
            for tool in tools
            if tool not in {"sql", "calculator"}
        ]

        if "rag" not in tools:
            tools.append("rag")

            # RAG is only valid when the query has document/policy/explanation
    # intent. This prevents the LLM from adding RAG to simple SQL queries.
    if not has_rag_intent:
        tools = [
            tool
            for tool in tools
            if tool != "rag"
        ]

    # Calculator is required for calculations that cannot be directly
    # answered by SQL.
    #
    # SQL can directly calculate aggregates such as AVG, SUM, COUNT,
    # MIN, and MAX, so "average revenue" does not require the calculator.
    has_sql_aggregate = any(
        word in q
        for word in (
            "average",
            "avg",
            "total",
            "sum",
            "count",
            "minimum",
            "maximum",
            "min",
            "max",
        )
    )

    if not has_calculation_words or has_sql_aggregate:
        tools = [
            tool
            for tool in tools
            if tool != "calculator"
        ]
    # Data analysis is only valid for explicit trend/analysis requests.
    # Prevent the LLM from adding it to ordinary calculations.
    has_analysis_intent = any(
        word in q
        for word in (
            "trend",
            "analysis",
            "analyze",
            "breakdown",
            "group by",
            "segment",
        )
    )

    if not has_analysis_intent:
        tools = [
            tool
            for tool in tools
            if tool != "data_analysis"
        ]

    # If a calculation is explicitly requested and SQL data is required,
    # ensure SQL is included.
    #
    # SQL handles native aggregates such as AVG/SUM/COUNT directly.
    # Calculator is only added when a separate mathematical operation
    # is actually required after retrieving the data.
    if has_calculation_words and has_data_words:
        if "sql" not in tools:
            tools.insert(0, "sql")

        sql_aggregate_question = any(
            word in q
            for word in (
                "average",
                "avg",
                "mean",
                "total",
                "sum",
                "count",
                "minimum",
                "maximum",
                "min",
                "max",
            )
        )

        if not sql_aggregate_question and "calculator" not in tools:
            tools.append("calculator")

    # Remove duplicates while preserving order.
    seen = set()

    return [
        tool
        for tool in tools
        if not (tool in seen or seen.add(tool))
    ]


def generate_sql_query(user_query: str) -> str | None:
    """Generate safe, read-only SQL for supported business questions."""

    q = user_query.lower()

    # ---------------------------------------------------------
    # June → July revenue comparison
    # ---------------------------------------------------------
    if (
        "june" in q
        and "july" in q
        and "revenue" in q
        and any(
            word in q
            for word in (
                "percentage",
                "percent",
                "increase",
                "growth",
                "compare",
                "change",
            )
        )
    ):
        return """
        SELECT
            SUM(
                CASE
                    WHEN strftime('%m', date) = '06'
                    THEN revenue
                    ELSE 0
                END
            ) AS june_revenue,
            SUM(
                CASE
                    WHEN strftime('%m', date) = '07'
                    THEN revenue
                    ELSE 0
                END
            ) AS july_revenue
        FROM sales
        """.strip()

    # ---------------------------------------------------------
    # July average revenue per sale
    # ---------------------------------------------------------
    if (
        "july" in q
        and "revenue" in q
        and any(
            word in q
            for word in (
                "average",
                "avg",
                "mean",
            )
        )
    ):
        return """
        SELECT
            AVG(revenue) AS average_revenue_per_sale
        FROM sales
        WHERE strftime('%m', date) = '07'
        """.strip()

    # ---------------------------------------------------------
    # July revenue
    # ---------------------------------------------------------
    if "july" in q and "revenue" in q:
        return """
        SELECT
            SUM(revenue) AS july_revenue
        FROM sales
        WHERE strftime('%m', date) = '07'
        """.strip()

    # ---------------------------------------------------------
    # June revenue
    # ---------------------------------------------------------
    if "june" in q and "revenue" in q:
        return """
        SELECT
            SUM(revenue) AS june_revenue
        FROM sales
        WHERE strftime('%m', date) = '06'
        """.strip()

    # ---------------------------------------------------------
    # June → July inventory cost comparison
    # ---------------------------------------------------------
    # ---------------------------------------------------------
# Inventory cost increase/comparison
# ---------------------------------------------------------
    if (
        "inventory" in q
        and "cost" in q
        and "july" in q
        and any(
            word in q
            for word in (
                "increase",
                "increased",
                "increase in",
                "growth",
                "change",
                "compare",
                "comparison",
                "why",
            )
        )
    ):
        return """
        SELECT
            SUM(
                CASE
                    WHEN strftime('%m', date) = '06'
                    THEN total_cost
                    ELSE 0
                END
            ) AS june_inventory_cost,
            SUM(
                CASE
                    WHEN strftime('%m', date) = '07'
                    THEN total_cost
                    ELSE 0
                END
            ) AS july_inventory_cost
        FROM inventory
        """.strip()

    # ---------------------------------------------------------
    # July inventory cost
    # ---------------------------------------------------------
    if (
        "inventory" in q
        and "cost" in q
        and "july" in q
    ):
        return """
        SELECT
            SUM(total_cost) AS july_inventory_cost
        FROM inventory
        WHERE strftime('%m', date) = '07'
        """.strip()

    # ---------------------------------------------------------
    # June inventory cost
    # ---------------------------------------------------------
    if (
        "inventory" in q
        and "cost" in q
        and "june" in q
    ):
        return """
        SELECT
            SUM(total_cost) AS june_inventory_cost
        FROM inventory
        WHERE strftime('%m', date) = '06'
        """.strip()

    return None
