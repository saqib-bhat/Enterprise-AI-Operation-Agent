from __future__ import annotations

from typing import List

from app.llm.factory import get_provider
from app.llm.providers import MockProvider


def determine_plan(user_query: str) -> List[str]:
    """Determine which tools are required for the user query.

    Future/prediction questions are rejected because the current agent
    does not have a forecasting model. This guard applies to both
    MockProvider and production LLM providers.
    """

    provider = get_provider()
    q = user_query.lower()

    # ---------------------------------------------------------
    # Future / prediction questions
    # ---------------------------------------------------------
    # The agent has no forecasting model. Never answer a future
    # question by incorrectly reusing historical SQL data.
    has_future_intent = any(
        phrase in q
        for phrase in (
            "next year",
            "next month",
            "next quarter",
            "future",
            "forecast",
            "predict",
            "prediction",
            "will be",
            "expected revenue",
            "expected sales",
        )
    )

    if has_future_intent:
        return []

    # ---------------------------------------------------------
    # MockProvider mode
    # ---------------------------------------------------------
    if isinstance(provider, MockProvider):
        plan = []

        # SQL is required for structured business/data questions.
        # Avoid SQL for pure policy/document questions.
        has_policy_words = any(
            word in q
            for word in (
                "policy",
                "sop",
                "procedure",
                "rule",
                "ceo",
                "chief executive",
                "leadership",
                "executive",
                "management",
                "company information",
                "company background",
                "minimum stock",
                "reorder",
                "approval",
                "emergency restock",
                "receiving",
                "inspection",
                "reconciliation",
                "vendor evaluation",
                "vendor contract",
                "procurement",
            )
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

        has_inventory = "inventory" in q
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

        has_numeric_data_intent = any(
            word in q
            for word in (
                "revenue",
                "sales",
                "compare",
                "percentage",
                "cost",
                "increase",
                "decrease",
            )
        )

        if (
            (has_data_words and not has_policy_words and not has_analysis_intent)
            or (has_inventory and not has_policy_words)
            or (has_numeric_data_intent and "cost" in q)
        ):
            plan.append("sql")

        if any(
            word in q
            for word in (
                "policy",
                "sop",
                "procedure",
                "rule",
                "process",
                "evaluation",
                "violate",
                "violation",
                "why",
                "explain",
                "reason",
                "minimum stock",
                "reorder",
                "approval",
                "emergency restock",
                "receiving",
                "inspection",
                "reconciliation",
                "vendor evaluation",
                "vendor contract",
                "procurement",
            )
        ):
            plan.append("rag")

        # Calculator is required for explicit mathematical
        # calculations that are not simple SQL aggregates.
        if any(
            word in q
            for word in (
                "percentage",
                "percent",
                "calculate",
                "calculation",
                "divide",
                "divided",
                "multiply",
                "multiplied",
                "ratio",
            )
        ) or any(symbol in q for symbol in ("%", "*", "/", "+", "-")):
            if "sql" not in plan:
                plan.append("sql")

            plan.append("calculator")

        # Data analysis for explicit analysis/trend questions.
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

    # ---------------------------------------------------------
    # Production / LLM mode
    # ---------------------------------------------------------
    # The LLM proposes tools, but deterministic business rules
    # validate the proposal before execution.

    prompt = (
        f"Produce a comma-separated list of tools to answer: "
        f"{user_query}. "
        "Allowed: sql, rag, calculator, data_analysis. "
        "Rules: "
        "Use sql for structured business data retrieval. "
        "Use rag for policies, SOPs, procedures, rules, and documents. "
        "Use calculator only when an actual mathematical calculation "
        "or derived numerical result is required. "
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

    tools = [
        tool
        for tool in tools
        if tool in allowed
    ]

    # ---------------------------------------------------------
    # Deterministic routing constraints
    # ---------------------------------------------------------

    has_policy_words = any(
        word in q
        for word in (
            "policy",
            "sop",
            "procedure",
            "rule",
            "minimum stock",
            "reorder",
            "approval",
            "emergency restock",
            "receiving",
            "inspection",
            "reconciliation",
            "vendor evaluation",
            "vendor contract",
            "procurement",
        )
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
            "ceo",
            "chief executive",
            "leadership",
            "executive",
            "management",
            "company information",
            "company background",
            "minimum stock",
            "reorder",
            "approval",
            "emergency restock",
            "receiving",
            "inspection",
            "reconciliation",
            "vendor evaluation",
            "vendor contract",
            "procurement",
        )
    )

        # ---------------------------------------------------------
    # Company/document questions must not use SQL.
    # ---------------------------------------------------------
    has_company_info_intent = any(
        phrase in q
        for phrase in (
            "ceo",
            "chief executive",
            "leadership",
            "executive",
            "management",
            "company information",
            "company background",
        )
    )

    if has_company_info_intent:
        tools = [
            tool
            for tool in tools
            if tool not in {"sql", "calculator", "data_analysis"}
        ]

        if "rag" not in tools:
            tools.append("rag")

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
        for symbol in (
            "%",
            "*",
            "/",
            "+",
            "-",
        )
    )

    # ---------------------------------------------------------
    # Policy/document routing
    # ---------------------------------------------------------

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
            if tool not in {
                "sql",
                "calculator",
            }
        ]

        if "rag" not in tools:
            tools.append("rag")

    # RAG should only be used when the query has RAG intent.
    if not has_rag_intent:
        tools = [
            tool
            for tool in tools
            if tool != "rag"
        ]

    # ---------------------------------------------------------
    # Calculator routing
    # ---------------------------------------------------------

    # SQL can directly calculate standard aggregates.
    has_sql_aggregate = any(
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

    if (
        not has_calculation_words
        or has_sql_aggregate
    ):
        tools = [
            tool
            for tool in tools
            if tool != "calculator"
        ]

    # ---------------------------------------------------------
    # Data analysis routing
    # ---------------------------------------------------------

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
    elif "data_analysis" not in tools:
        tools.append("data_analysis")

    # ---------------------------------------------------------
    # Ensure SQL for calculations requiring business data
    # ---------------------------------------------------------

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

        if (
            not sql_aggregate_question
            and "calculator" not in tools
        ):
            tools.append("calculator")

    # ---------------------------------------------------------
    # Remove duplicates while preserving order
    # ---------------------------------------------------------

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
