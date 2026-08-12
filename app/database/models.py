from __future__ import annotations
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    MetaData,
)
from sqlalchemy.orm import declarative_base

# Use naming convention for easier migrations later
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)
Base = declarative_base(metadata=metadata)


class Vendor(Base):
    __tablename__ = "vendors"
    vendor_id = Column(String(32), primary_key=True, index=True)
    vendor_name = Column(String(255), nullable=False)
    category = Column(String(100))
    location = Column(String(100))
    contract_type = Column(String(50))
    payment_terms = Column(String(50))
    rating = Column(Float)


class Sale(Base):
    __tablename__ = "sales"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(32), unique=True, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    product_id = Column(String(32), nullable=False, index=True)
    product_name = Column(String(255))
    category = Column(String(100), index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    revenue = Column(Float, nullable=False)
    region = Column(String(100))


class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True, autoincrement=True)
    inventory_id = Column(String(32), unique=True, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    product_id = Column(String(32), nullable=False, index=True)
    product_name = Column(String(255))
    category = Column(String(100), index=True)
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    warehouse = Column(String(50))
    vendor_id = Column(String(32), nullable=False, index=True)
