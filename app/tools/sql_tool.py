from __future__ import annotations
import os
import re
import sqlite3
from typing import Any, Dict, List

FORBIDDEN = re.compile(r"\b(insert|update|delete|drop|alter|truncate|attach|detach|replace)\b", flags=re.IGNORECASE)


def _get_sqlite_path(database_url: str | None) -> str:
    if not database_url:
        database_url = os.environ.get("DATABASE_URL") or "sqlite:////app/data/operations.db"
    if database_url == "sqlite:///:memory:":
        return ":memory:"
    if database_url.startswith("sqlite:///"):
        return database_url.replace("sqlite:///", "", 1)
    # fallback: treat as file path
    return database_url


def execute_select(query: str, database_url: str | None = None) -> Dict[str, Any]:
    # Basic validations
    if not isinstance(query, str) or not query.strip():
        return {"success": False, "error": "Query must be a non-empty string"}

    if ";" in query:
        return {"success": False, "error": "Multiple statements are not allowed"}

    if FORBIDDEN.search(query):
        return {"success": False, "error": "Destructive or mutating SQL statements are not allowed"}

    ql = query.lstrip().lower()
    if not (ql.startswith("select") or ql.startswith("with")):
        return {"success": False, "error": "Only SELECT queries are allowed"}

    db_path = _get_sqlite_path(database_url)
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(query)
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchall()
        row_count = len(rows)
        # Close connection promptly
        cur.close()
        conn.close()
        return {"success": True, "columns": cols, "rows": rows, "row_count": row_count}
    except sqlite3.Error as e:
        # sanitize error message
        return {"success": False, "error": str(e)}
    except Exception:
        return {"success": False, "error": "Unexpected error during query execution"}
