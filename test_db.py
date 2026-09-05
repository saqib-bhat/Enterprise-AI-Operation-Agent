import sqlite3
from app.config import settings
from app.tools.sql_tool import _get_sqlite_path


def main() -> None:
    """Print a small database smoke check when run as a script."""
    db_path = _get_sqlite_path(settings.database_url)
    with sqlite3.connect(db_path) as db:
        print("SALES:", db.execute("SELECT COUNT(*) FROM sales").fetchone())
        print(
            "JULY REVENUE:",
            db.execute(
                "SELECT SUM(quantity * unit_price) "
                "FROM sales "
                "WHERE date LIKE '2026-07-%'"
            ).fetchone(),
        )


if __name__ == "__main__":
    main()
