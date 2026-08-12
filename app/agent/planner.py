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
        if any(
            word in q
            for word in (
                "revenue",
                "sales",
                "compare",
                "percentage",
                "increase",
                "decrease",
                "cost",
                "inventory",
                "vendor",
            )
        ):
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
    prompt = (
        f"Produce a comma-separated list of tools to answer: {user_query}. "
        "Allowed: sql, rag, calculator, data_analysis. "
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

    return [tool for tool in tools if tool in allowed]


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
    if (
        "inventory" in q
        and "cost" in q
        and "june" in q
        and "july" in q
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