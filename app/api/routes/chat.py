"""Chat endpoint for the Enterprise AI Operations Agent API."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agent.graph import run_graph

router = APIRouter()


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    query: str = Field(..., min_length=1, description="User query")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    query: str
    answer: str
    tools_used: list[str]
    evidence: list[dict]
    verification: dict
    errors: list[str]
    latency: dict[str, float]


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Process a user query through the LangGraph agent.
    
    Args:
        request: ChatRequest containing the user's query
        
    Returns:
        ChatResponse with the agent's answer and metadata
    """
    try:
        # Run the existing LangGraph agent
        state = run_graph(request.query)
        
        # Map AgentState fields to API response
        return ChatResponse(
            query=state.get("user_query", request.query),
            answer=state.get("final_answer", "Unable to process query"),
            tools_used=state.get("selected_tools", []),
            evidence=state.get("evidence", []),
            verification=state.get("verification_result", {}),
            errors=state.get("errors", []),
            latency=state.get("latency", {}),
        )
        
    except Exception as e:
        # Log the error internally but return a safe response
        # Never expose internal errors, API keys, or stack traces
        raise HTTPException(
            status_code=500,
            detail="Internal server error",
        ) from e