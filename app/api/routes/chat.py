"""Chat endpoint for the Enterprise AI Operations Agent API."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app.agent.graph import run_graph

router = APIRouter()


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    query: str = Field(..., description="User query")

    @field_validator("query")
    @classmethod
    def validate_query_not_empty(cls, v: str) -> str:
        """Validate that query is not empty or whitespace-only."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty or whitespace-only")
        return v


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    query: str
    answer: str
    tools_used: list[str]
    evidence: list[dict]
    verification: dict
    errors: list[str]
    latency: dict[str, float]


class ErrorResponse(BaseModel):
    """Error response model."""
    detail: str


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid query"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def chat(request: ChatRequest):
    """Process a user query through the LangGraph agent.
    
    Args:
        request: ChatRequest containing the user's query
        
    Returns:
        ChatResponse with the agent's answer and metadata
        
    Raises:
        HTTPException: On validation failure or agent errors
    """
    try:
        # Run the existing LangGraph agent
        state = run_graph(request.query)
        
        # Map AgentState fields to API response
        return ChatResponse(
            query=state.get("user_query", request.query),
            answer=state.get("final_response", {}).get(
            "Answer",
            "Unable to generate a verified answer from the available evidence."
            ) if state.get("final_response") else "Unable to generate a verified answer from the available evidence.",
            tools_used=state.get("selected_tools", []),
            evidence=state.get("evidence", []),
            verification=state.get("verification_result", {}),
            errors=state.get("errors", []),
            latency=state.get("latency", {}),
        )
        
    except HTTPException:
        # Re-raise HTTPException without exposing internal details
        raise
        
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )