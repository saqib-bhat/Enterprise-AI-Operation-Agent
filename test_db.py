import sqlite3

db = sqlite3.connect("/app/data/operations.db")

print("SALES:", db.execute("SELECT COUNT(*) FROM sales").fetchone())
print(
    "JULY REVENUE:",
    db.execute(
        "SELECT SUM(quantity * unit_price) "
        "FROM sales "
        "WHERE date LIKE '2026-07-%'"
    ).fetchone()
)

db.close()
