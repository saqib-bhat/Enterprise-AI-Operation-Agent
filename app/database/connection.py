from __future__ import annotations

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DEFAULT_DATABASE_URL = "sqlite:////app/data/operations.db"


def get_engine(database_url: str | None = None):
    url = database_url or os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL
    return create_engine(url, future=True)


def get_session_factory(engine=None, database_url: str | None = None):
    eng = engine or get_engine(database_url)
    return sessionmaker(bind=eng, expire_on_commit=False, future=True)


def get_session(engine=None, database_url: str | None = None):
    Session = get_session_factory(engine=engine, database_url=database_url)
    return Session()