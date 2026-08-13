"""FastAPI application for Enterprise AI Operations Agent."""

from fastapi import FastAPI

app = FastAPI(title="Enterprise AI Operations Agent API")


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}