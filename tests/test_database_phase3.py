import tempfile
import os
from pathlib import Path
import sqlite3
import pytest


def test_database_initialization_creates_db(tmp_path, monkeypatch):
    db_file = tmp_path / 'ops.db'
    # ensure DATABASE_URL uses this file
    monkeypatch.setenv('DATABASE_URL', f'sqlite:///{db_file}')
    # run initializer
    from scripts import initialize_database

    rc = initialize_database.initialize(database_url=None, data_dir=Path('data/raw'))
    assert rc == 0
    assert db_file.exists()


def test_tables_and_counts(tmp_path, monkeypatch):
    db_file = tmp_path / 'ops2.db'
    monkeypatch.setenv('DATABASE_URL', f'sqlite:///{db_file}')
    from scripts import initialize_database
    initialize_database.initialize(database_url=None, data_dir=Path('data/raw'))

    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    # check tables exist
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {r[0] for r in cur.fetchall()}
    assert 'vendors' in tables
    assert 'sales' in tables
    assert 'inventory' in tables

    # check row counts roughly match CSV
    cur.execute('SELECT COUNT(*) FROM vendors')
    vcount = cur.fetchone()[0]
    assert vcount == 500
    cur.execute('SELECT COUNT(*) FROM sales')
    scount = cur.fetchone()[0]
    assert scount == 5000
    cur.execute('SELECT COUNT(*) FROM inventory')
    icount = cur.fetchone()[0]
    assert icount == 2000

    conn.close()
