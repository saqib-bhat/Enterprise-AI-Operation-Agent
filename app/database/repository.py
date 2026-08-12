from __future__ import annotations
from typing import Iterable, List
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from .connection import get_engine, get_session
from .models import Base, Vendor, Sale, Inventory
from pathlib import Path
from datetime import datetime


def create_database_tables(database_url: str | None = None):
    engine = get_engine(database_url)
    Base.metadata.create_all(engine)
    return engine


def load_vendors_from_csv(path: Path, session=None):
    created = 0
    sess = session or get_session()
    with path.open('r', encoding='utf-8', newline='') as fo:
        import csv

        reader = csv.DictReader(fo)
        for row in reader:
            v = Vendor(
                vendor_id=row['vendor_id'],
                vendor_name=row.get('vendor_name') or '',
                category=row.get('category'),
                location=row.get('location'),
                contract_type=row.get('contract_type'),
                payment_terms=row.get('payment_terms'),
                rating=float(row['rating']) if row.get('rating') not in (None, '') else None,
            )
            # merge to avoid duplicates on rerun
            sess.merge(v)
            created += 1
    sess.commit()
    return created


def load_sales_from_csv(path: Path, session=None):
    created = 0
    sess = session or get_session()
    import csv

    with path.open('r', encoding='utf-8', newline='') as fo:
        reader = csv.DictReader(fo)
        for row in reader:
            try:
                order_id = row['order_id']
                existing = sess.execute(select(Sale).filter_by(order_id=order_id)).scalars().first()
                if existing:
                    # update existing fields
                    existing.date = datetime.fromisoformat(row['date']).date()
                    existing.product_id = row['product_id']
                    existing.product_name = row.get('product_name')
                    existing.category = row.get('category')
                    existing.quantity = int(row.get('quantity') or 0)
                    existing.unit_price = float(row.get('unit_price') or 0.0)
                    existing.revenue = float(row.get('revenue') or 0.0)
                    existing.region = row.get('region')
                else:
                    s = Sale(
                        order_id=order_id,
                        date=datetime.fromisoformat(row['date']).date(),
                        product_id=row['product_id'],
                        product_name=row.get('product_name'),
                        category=row.get('category'),
                        quantity=int(row.get('quantity') or 0),
                        unit_price=float(row.get('unit_price') or 0.0),
                        revenue=float(row.get('revenue') or 0.0),
                        region=row.get('region'),
                    )
                    sess.add(s)
                    created += 1
            except Exception:
                sess.rollback()
                continue
    sess.commit()
    return created


def load_inventory_from_csv(path: Path, session=None):
    created = 0
    sess = session or get_session()
    import csv

    with path.open('r', encoding='utf-8', newline='') as fo:
        reader = csv.DictReader(fo)
        for row in reader:
            try:
                inv_id = row['inventory_id']
                existing = sess.execute(select(Inventory).filter_by(inventory_id=inv_id)).scalars().first()
                if existing:
                    existing.date = datetime.fromisoformat(row['date']).date()
                    existing.product_id = row['product_id']
                    existing.product_name = row.get('product_name')
                    existing.category = row.get('category')
                    existing.quantity = int(row.get('quantity') or 0)
                    existing.unit_cost = float(row.get('unit_cost') or 0.0)
                    existing.total_cost = float(row.get('total_cost') or 0.0)
                    existing.warehouse = row.get('warehouse')
                    existing.vendor_id = row.get('vendor_id')
                else:
                    inv = Inventory(
                        inventory_id=inv_id,
                        date=datetime.fromisoformat(row['date']).date(),
                        product_id=row['product_id'],
                        product_name=row.get('product_name'),
                        category=row.get('category'),
                        quantity=int(row.get('quantity') or 0),
                        unit_cost=float(row.get('unit_cost') or 0.0),
                        total_cost=float(row.get('total_cost') or 0.0),
                        warehouse=row.get('warehouse'),
                        vendor_id=row.get('vendor_id'),
                    )
                    sess.add(inv)
                    created += 1
            except Exception:
                sess.rollback()
                continue
    sess.commit()
    return created


def count_table(model, session=None):
    sess = session or get_session()
    return sess.execute(select(model)).scalars().all().__len__()


def simple_query_engine(database_url: str | None = None):
    return get_engine(database_url)
