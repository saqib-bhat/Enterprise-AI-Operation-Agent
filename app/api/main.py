# """FastAPI application for Enterprise AI Operations Agent."""

# from fastapi import FastAPI

# from app.api.routes import chat

# app = FastAPI(title="Enterprise AI Operations Agent")

# app.include_router(chat.router)


# @app.get("/health")
# def health_check():
#     """Health check endpoint."""
#     return {"status": "ok"}


"""FastAPI application for Enterprise AI Operations Agent."""

import os
import sqlite3

from fastapi import FastAPI

from app.api.routes import chat

app = FastAPI(title="Enterprise AI Operations Agent")

app.include_router(chat.router)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/debug/database")
def debug_database():
    """Temporary database diagnostic endpoint."""

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        database_url = "sqlite:///./data/operations.db"

    if database_url.startswith("sqlite:///"):
        db_path = database_url.replace("sqlite:///", "", 1)
    else:
        return {
            "database_url": database_url,
            "error": "Database is not SQLite",
        }

    if not os.path.isabs(db_path):
        db_path = os.path.abspath(db_path)

    result = {
        "database_url": database_url,
        "database_path": db_path,
        "database_exists": os.path.exists(db_path),
    }

    if not os.path.exists(db_path):
        return result

    try:
        db = sqlite3.connect(db_path)

        sales_count = db.execute(
            "SELECT COUNT(*) FROM sales"
        ).fetchone()[0]

        july_revenue = db.execute(
            """
            SELECT SUM(quantity * unit_price)
            FROM sales
            WHERE date LIKE '2026-07-%'
            """
        ).fetchone()[0]

        min_date, max_date = db.execute(
            "SELECT MIN(date), MAX(date) FROM sales"
        ).fetchone()

        db.close()

        result.update(
            {
                "sales_count": sales_count,
                "july_revenue": july_revenue,
                "min_date": min_date,
                "max_date": max_date,
            }
        )

        return result

    except Exception as exc:
        result["error"] = str(exc)
        return result

@app.get("/debug/rag")
def debug_rag():
    """Temporary RAG diagnostic endpoint."""

    import json

    result = {
        "cwd": os.getcwd(),
        "index_exists": False,
        "metadata_exists": False,
        "index_size": None,
        "metadata_size": None,
        "index_vectors": None,
        "index_dimension": None,
        "metadata_type": None,
        "metadata_count": None,
        "metadata_preview": None,
        "errors": [],
    }

    index_path = "/app/vector_store/index.faiss"
    metadata_path = "/app/vector_store/metadata.json"

    # --------------------------------------------------
    # Check FAISS and metadata files
    # --------------------------------------------------

    result["index_exists"] = os.path.exists(index_path)
    result["metadata_exists"] = os.path.exists(metadata_path)

    if result["index_exists"]:
        result["index_size"] = os.path.getsize(index_path)

    if result["metadata_exists"]:
        result["metadata_size"] = os.path.getsize(metadata_path)

    # --------------------------------------------------
    # Try loading FAISS
    # --------------------------------------------------

    try:
        import faiss

        index = faiss.read_index(index_path)

        result["index_vectors"] = index.ntotal
        result["index_dimension"] = index.d

    except Exception as exc:
        result["errors"].append(
            f"FAISS: {type(exc).__name__}: {exc}"
        )

    # --------------------------------------------------
    # Try loading metadata
    # --------------------------------------------------

    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        result["metadata_type"] = type(metadata).__name__

        if isinstance(metadata, list):
            result["metadata_count"] = len(metadata)
            result["metadata_preview"] = metadata[:2]

        elif isinstance(metadata, dict):
            result["metadata_count"] = len(metadata)
            result["metadata_preview"] = str(metadata)[:1000]

        else:
            result["metadata_preview"] = str(metadata)[:1000]

    except Exception as exc:
        result["errors"].append(
            f"Metadata: {type(exc).__name__}: {exc}"
        )

    return result