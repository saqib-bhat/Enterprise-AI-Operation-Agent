from __future__ import annotations
import sys
import argparse
from pathlib import Path
# ensure workspace root is importable when running as script
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database.connection import get_engine, get_session
from app.database import repository


def initialize(database_url: str | None = None, data_dir: Path | None = None):
    data_dir = data_dir or Path('data/raw')
    db_url = database_url
    engine = repository.create_database_tables(database_url=db_url)
    session = get_session(engine)

    # load vendors
    vendors_csv = data_dir / 'vendors.csv'
    sales_csv = data_dir / 'sales.csv'
    inventory_csv = data_dir / 'inventory.csv'

    if not vendors_csv.exists() or not sales_csv.exists() or not inventory_csv.exists():
        print('ERROR: expected CSV files not found in', data_dir)
        return 2

    print('Loading vendors from', vendors_csv)
    v = repository.load_vendors_from_csv(vendors_csv, session=session)
    print(f'Loaded/merged {v} vendor rows')

    print('Loading sales from', sales_csv)
    s = repository.load_sales_from_csv(sales_csv, session=session)
    print(f'Loaded/merged {s} sales rows')

    print('Loading inventory from', inventory_csv)
    i = repository.load_inventory_from_csv(inventory_csv, session=session)
    print(f'Loaded/merged {i} inventory rows')

    print('Initialization complete')
    return 0


def main():
    parser = argparse.ArgumentParser(description='Initialize SQLite database from CSVs')
    parser.add_argument('--db', help='Database URL (overrides DATABASE_URL env)', default=None)
    parser.add_argument('--data', help='Path to CSV folder', default='data/raw')
    args = parser.parse_args()
    return initialize(database_url=args.db, data_dir=Path(args.data))


if __name__ == '__main__':
    raise SystemExit(main())
import sqlite3
from pathlib import Path

DB_PATH = Path("data/operations.db")
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sales (
    order_id TEXT PRIMARY KEY,
    date TEXT NOT NULL,
    product_id TEXT NOT NULL,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    revenue REAL NOT NULL,
    region TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS inventory (
    inventory_id TEXT PRIMARY KEY,
    date TEXT NOT NULL,
    product_id TEXT NOT NULL,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_cost REAL NOT NULL,
    total_cost REAL NOT NULL,
    warehouse TEXT NOT NULL,
    vendor_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS vendors (
    vendor_id TEXT PRIMARY KEY,
    vendor_name TEXT NOT NULL,
    category TEXT NOT NULL,
    location TEXT NOT NULL,
    contract_type TEXT NOT NULL,
    payment_terms TEXT NOT NULL,
    rating REAL NOT NULL
);
"""


def initialize_database() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA_SQL)


if __name__ == "__main__":
    initialize_database()
    print(f"Initialized database at {DB_PATH}")
