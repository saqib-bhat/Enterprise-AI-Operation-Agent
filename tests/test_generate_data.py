import csv
from pathlib import Path


def test_generated_data_files_exist():
    raw_dir = Path("data/raw")
    assert raw_dir.exists(), "data/raw directory should exist"
    for filename in ["sales.csv", "inventory.csv", "vendors.csv"]:
        assert (raw_dir / filename).exists(), f"{filename} should exist"


def test_sales_row_count():
    with open("data/raw/sales.csv", newline="", encoding="utf-8") as fo:
        rows = list(csv.DictReader(fo))
    assert len(rows) == 5000


def test_inventory_row_count():
    with open("data/raw/inventory.csv", newline="", encoding="utf-8") as fo:
        rows = list(csv.DictReader(fo))
    assert len(rows) == 2000


def test_vendors_row_count():
    with open("data/raw/vendors.csv", newline="", encoding="utf-8") as fo:
        rows = list(csv.DictReader(fo))
    assert len(rows) == 500
