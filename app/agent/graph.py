from __future__ import annotations

from typing import Any, Callable

from langgraph.graph import StateGraph, END

from app.agent.state import AgentState, make_initial_state
from app.agent import (
    planner,
    router,
    tool_executor,
    evidence,
    verifier,
    response,
)


def build_graph() -> StateGraph:
    """Build the Enterprise AI Operations LangGraph workflow.

    Workflow:

        START
          ↓
        Planner
          ↓
        Router
          ↓
      ToolExecution
          ↓
    EvidenceCollection
          ↓
       Verifier
        ↙     ↘
      END   ResponseGenerator
                ↓
               END
    """

    graph = StateGraph(AgentState)

    # ---------------------------------------------------------
    # Planner
    # ---------------------------------------------------------
    def node_planner(state: AgentState) -> AgentState:
        query = state.get("user_query", "")

        state["plan"] = planner.determine_plan(query)

        # Generate SQL when SQL is part of the plan.
        if "sql" in state["plan"]:
            sql_query = planner.generate_sql_query(query)

            if sql_query:
                state["sql_query"] = sql_query
            else:
                state.setdefault("errors", []).append(
                    "Unable to generate SQL query"
                )

        if "data_analysis" in state["plan"] and not state.get("analysis_params"):
            state["analysis_params"] = {
                "operation": "trend" if any(
                    word in query.lower()
                    for word in ("trend", "over time", "by month", "monthly")
                ) else "groupby",
                "source": "inventory" if "inventory" in query.lower() else "sales",
                "group_by": ["category"],
                "aggregations": {
                    "total_cost" if "inventory" in query.lower() else "revenue": "sum",
                },
                "date_column": "date",
                "metric": "total_cost" if "inventory" in query.lower() else "revenue",
                "freq": "ME",
            }

        return state

    # ---------------------------------------------------------
    # Router
    # ---------------------------------------------------------
    def node_router(state: AgentState) -> AgentState:
        plan = state.get("plan", [])

        try:
            selected_tools = router.route(plan)

            state["selected_tools"] = selected_tools

        except ValueError as exc:
            # Invalid planner output must not crash the entire graph.
            # Store the error in state so the caller can inspect it.
            state["selected_tools"] = []
            state.setdefault("errors", []).append(str(exc))

        return state

    # ---------------------------------------------------------
    # Tool execution
    # ---------------------------------------------------------
    def node_tool_execution(state: AgentState) -> AgentState:
        selected_tools = state.get("selected_tools", [])

        if selected_tools:
            tool_executor.execute_tools(
                selected_tools,
                state,
            )

        return state

    # ---------------------------------------------------------
    # Evidence collection
    # ---------------------------------------------------------
    def node_evidence_collection(state: AgentState) -> AgentState:
        evidence.collect_evidence(state)
        return state

    # ---------------------------------------------------------
    # Verification
    # ---------------------------------------------------------
    def node_verifier(state: AgentState) -> AgentState:
        result = verifier.verify(state)
        state["verification_result"] = result

        return state

    # ---------------------------------------------------------
    # Response generation
    # ---------------------------------------------------------
    def node_response_generator(state: AgentState) -> AgentState:
        result = response.generate_response(state)

        # Support either a returned response or a function that
        # mutates the state directly.
        if result is not None:
            if isinstance(result, dict):
                state["final_response"] = result

                # The response generator uses "Answer" as the
                # canonical human-readable answer.
                if result.get("Answer"):
                    state["final_answer"] = result["Answer"]

                elif result.get("text"):
                    state["final_answer"] = result["text"]

        # Ensure the state always has a usable final answer.
        if not state.get("final_answer"):
            state["final_answer"] = (
                "The request could not be completed."
            )

        return state

    # ---------------------------------------------------------
    # Register nodes
    # ---------------------------------------------------------
    graph.add_node(
        "Planner",
        node_planner,
    )

    graph.add_node(
        "Router",
        node_router,
    )

    graph.add_node(
        "ToolExecution",
        node_tool_execution,
    )

    graph.add_node(
        "EvidenceCollection",
        node_evidence_collection,
    )

    graph.add_node(
        "Verifier",
        node_verifier,
    )

    graph.add_node(
        "ResponseGenerator",
        node_response_generator,
    )

    # ---------------------------------------------------------
    # Entry point
    # ---------------------------------------------------------
    graph.set_entry_point("Planner")

    # ---------------------------------------------------------
    # Planner → Router
    # ---------------------------------------------------------
    graph.add_edge(
        "Planner",
        "Router",
    )

    # ---------------------------------------------------------
    # Router → ToolExecution / EvidenceCollection
    # ---------------------------------------------------------
    def router_path(state: AgentState) -> str:
        if state.get("selected_tools"):
            return "ToolExecution"

        return "EvidenceCollection"

    graph.add_conditional_edges(
        "Router",
        router_path,
        {
            "ToolExecution": "ToolExecution",
            "EvidenceCollection": "EvidenceCollection",
        },
    )

    # ---------------------------------------------------------
    # ToolExecution → EvidenceCollection
    # ---------------------------------------------------------
    graph.add_edge(
        "ToolExecution",
        "EvidenceCollection",
    )

    # ---------------------------------------------------------
    # EvidenceCollection → Verifier
    # ---------------------------------------------------------
    graph.add_edge(
        "EvidenceCollection",
        "Verifier",
    )

    def verifier_path(state: AgentState) -> str:
        verification = state.get(
            "verification_result",
            {},
        )

        if verification.get("ok", True):
            return "ResponseGenerator"

        state["final_answer"] = (
            "I do not have sufficient information to answer "
            "the question from the available evidence."
        )

        return "ResponseGenerator"

    graph.add_conditional_edges(
        "Verifier",
        verifier_path,
        {
            "ResponseGenerator": "ResponseGenerator",
            "END": END,
        },
    )

    # ---------------------------------------------------------
    # ResponseGenerator → END
    # ---------------------------------------------------------
    graph.set_finish_point("ResponseGenerator")

    return graph


def run_graph(query: str) -> AgentState:
    """Run the compiled LangGraph agent for a user query."""

    state = make_initial_state(query)

    graph = build_graph()
    compiled_graph = graph.compile()

    result = compiled_graph.invoke(state)

    return result