# """FastAPI application for Enterprise AI Operations Agent."""

from fastapi import FastAPI

from app.api.routes import chat

app = FastAPI(title="Enterprise AI Operations Agent")

app.include_router(chat.router)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
