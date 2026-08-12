from __future__ import annotations
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DEFAULT_DATABASE_URL = "sqlite:///data/operations.db"


# Create engine and session factory lazily so tests can override DATABASE_URL
def get_engine(database_url: str | None = None):
    # prefer explicit argument, then environment, then default
    url = database_url or os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL
    # echo can be enabled via env for debugging
    engine = create_engine(url, future=True)
    return engine


def get_session_factory(engine=None, database_url: str | None = None):
    eng = engine or get_engine(database_url)
    return sessionmaker(bind=eng, expire_on_commit=False, future=True)


def get_session(engine=None, database_url: str | None = None):
    Session = get_session_factory(engine=engine, database_url=database_url)
    return Session()
