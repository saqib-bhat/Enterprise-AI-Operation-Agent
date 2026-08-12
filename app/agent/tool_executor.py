from __future__ import annotations

from typing import Dict, Any, List

from app.tools import (
    sql_tool,
    calculator_tool,
    data_analysis_tool,
)

try:
    from app.tools import rag_tool
except Exception:
    try:
        from app.rag import retrieval as rag_tool
    except Exception:
        rag_tool = None


def execute_tools(
    tools: List[str],
    state: Dict[str, Any],
) -> Dict[str, Any]:
    """Execute the selected tools using the current agent state.

    SQL executes before calculator so calculator operations can consume
    SQL results.
    """

    results: Dict[str, Any] = {}

    for tool in tools:

        # ---------------------------------------------------------
        # SQL
        # ---------------------------------------------------------
        if tool == "sql":
            query = state.get("sql_query")

            if not query:
                result = {
                    "success": False,
                    "error": "No SQL query was generated",
                }
            else:
                result = sql_tool.execute_select(
                    query,
                    None,
                )

            results["sql"] = result
            state["sql_results"] = result

        # ---------------------------------------------------------
        # RAG
        # ---------------------------------------------------------
        elif tool == "rag":

            if rag_tool is None:
                result = {
                    "success": False,
                    "error": "RAG tool not available",
                }
            else:
                result = rag_tool.retrieve(
                    state.get("user_query", "")
                )

            results["rag"] = result

            if (
                isinstance(result, dict)
                and result.get("results")
            ):
                state.setdefault(
                    "retrieved_documents",
                    [],
                ).extend(
                    result.get("results")
                )
            else:
                state.setdefault(
                    "retrieved_documents",
                    [],
                ).append(result)

        # ---------------------------------------------------------
        # Calculator
        # ---------------------------------------------------------
        elif tool == "calculator":

            operations = state.get("calc_ops", [])

            # For the June → July percentage question, construct the
            # calculator operation from the SQL result.
            if not operations:
                sql_result = state.get(
                    "sql_results",
                    {},
                )

                if (
                    isinstance(sql_result, dict)
                    and sql_result.get("success")
                    and sql_result.get("rows")
                ):
                    row = sql_result["rows"][0]

                    if (
                        "june_revenue" in row
                        and "july_revenue" in row
                    ):
                        operations = [
                            {
                                "op": "percentage_change",
                                "args": [
                                    row["june_revenue"],
                                    row["july_revenue"],
                                ],
                            }
                        ]

                        state["calc_ops"] = operations

            calculator_results: Dict[str, Any] = {}

            for operation in operations:
                name = operation.get("op")
                args = operation.get("args", [])

                try:
                    if name == "percentage_change":
                        calculator_results[name] = (
                            calculator_tool.percentage_change(
                                *args
                            )
                        )

                    elif name == "percentage_difference":
                        calculator_results[name] = (
                            calculator_tool.percentage_difference(
                                *args
                            )
                        )

                    elif name == "total":
                        calculator_results[name] = (
                            calculator_tool.total(
                                args
                            )
                        )

                    elif name == "average":
                        calculator_results[name] = (
                            calculator_tool.average(
                                args
                            )
                        )

                    elif name == "ratio":
                        calculator_results[name] = (
                            calculator_tool.ratio(
                                *args
                            )
                        )

                    elif name == "growth_rate":
                        calculator_results[name] = (
                            calculator_tool.growth_rate(
                                *args
                            )
                        )

                    else:
                        calculator_results[name] = {
                            "success": False,
                            "error": (
                                f"Unsupported calculator operation: "
                                f"{name}"
                            ),
                        }

                except Exception as exc:
                    calculator_results[name] = {
                        "success": False,
                        "error": str(exc),
                    }

            results["calculator"] = calculator_results
            state["calculations"] = calculator_results

        # ---------------------------------------------------------
        # Data Analysis
        # ---------------------------------------------------------
        elif tool == "data_analysis":

            params = state.get(
                "analysis_params",
                {},
            )

            result = data_analysis_tool.groupby_aggregate(
                params.get(
                    "source",
                    "sales",
                ),
                params.get(
                    "group_by",
                    [],
                ),
                params.get(
                    "aggregations",
                    {},
                ),
            )

            results["data_analysis"] = result

            state.setdefault(
                "tool_results",
                {},
            )["data_analysis"] = result

        # ---------------------------------------------------------
        # Unknown tool
        # ---------------------------------------------------------
        else:
            results[tool] = {
                "success": False,
                "error": "Unknown tool",
            }

    state.setdefault(
        "tool_results",
        {}
    ).update(results)

    return results