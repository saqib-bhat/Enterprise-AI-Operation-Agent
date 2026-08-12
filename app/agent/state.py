from typing import TypedDict, List, Dict, Any, Optional


class AgentState(TypedDict, total=False):
    user_query: str

    # Planning and routing
    plan: List[str]
    selected_tools: List[str]

    # Tool execution
    tool_results: Dict[str, Any]
    sql_query: Optional[str]
    sql_results: Any
    calc_ops: List[Dict[str, Any]]
    calculations: Dict[str, Any]
    analysis_params: Dict[str, Any]
    retrieved_documents: List[Dict[str, Any]]

    # Evidence and verification
    evidence: List[Dict[str, Any]]
    verification_result: Dict[str, Any]

    # Final response
    final_answer: Optional[str]
    final_response: Optional[Dict[str, Any]]

    # Operational information
    errors: List[str]
    latency: Dict[str, float]


def make_initial_state(query: str) -> AgentState:
    return AgentState(
        user_query=query,
        plan=[],
        selected_tools=[],

        # Tool state
        tool_results={},
        sql_query=None,
        sql_results=None,
        calc_ops=[],
        calculations={},
        analysis_params={},
        retrieved_documents=[],

        # Verification
        evidence=[],
        verification_result={},

        # Response
        final_answer=None,
        final_response=None,

        # Operational state
        errors=[],
        latency={},
    )