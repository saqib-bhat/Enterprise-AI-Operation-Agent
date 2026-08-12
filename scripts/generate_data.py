import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

PRODUCTS = [
    ("P001", "Steel Coil", "Raw Materials", 18.5, 12.0),
    ("P002", "Copper Wire", "Raw Materials", 22.0, 14.5),
    ("P003", "Aluminum Sheet", "Raw Materials", 15.5, 9.5),
    ("P004", "Resistor Pack", "Components", 8.5, 4.2),
    ("P005", "Capacitor Kit", "Components", 12.5, 6.8),
    ("P006", "Printed Circuit Board", "Components", 48.0, 30.5),
    ("P007", "Industrial Motor", "Finished Goods", 320.0, 190.0),
    ("P008", "Control Panel", "Finished Goods", 260.0, 160.0),
    ("P009", "Packaging Sleeve", "Packaging", 3.8, 1.7),
    ("P010", "Shipping Crate", "Packaging", 14.5, 8.5),
    ("P011", "Sensor Module", "Electronics", 92.0, 58.0),
    ("P012", "Power Converter", "Electronics", 76.0, 45.0),
    ("P013", "Quality Label", "Packaging", 1.5, 0.8),
    ("P014", "Wiring Bundle", "Components", 28.0, 16.0),
    ("P015", "Fastener Kit", "Components", 6.5, 3.4),
    ("P016", "Battery Pack", "Electronics", 138.0, 88.0),
    ("P017", "Cooling Fan", "Finished Goods", 42.0, 24.0),
    ("P018", "Inspection Tag", "Packaging", 0.9, 0.4),
    ("P019", "Protective Film", "Packaging", 2.4, 1.3),
    ("P020", "Insulation Tape", "Raw Materials", 5.0, 2.5),
    ("P021", "Drive Controller", "Electronics", 118.0, 72.0),
    ("P022", "Assembly Frame", "Finished Goods", 184.0, 110.0),
    ("P023", "Vendor Seal", "Packaging", 0.7, 0.3),
    ("P024", "Industrial Sensor", "Electronics", 150.0, 96.0),
    ("P025", "Bulk Resin", "Raw Materials", 32.0, 18.0),
]

REGIONS = ["North America", "Europe", "Asia Pacific", "Latin America", "EMEA"]
WAREHOUSES = ["WH-A", "WH-B", "WH-C", "WH-D"]
LOCATIONS = ["USA", "Germany", "China", "Brazil", "India", "Mexico", "Canada", "Spain", "Poland", "Vietnam"]
CONTRACT_TYPES = ["Fixed", "Variable", "Term"]
PAYMENT_TERMS = ["Net 30", "Net 45", "Net 60", "Prepaid"]

START_DATE = date(2025, 1, 1)
END_DATE = date(2026, 12, 31)

VENDOR_COUNT = 500
SALES_ROWS = 5000
INVENTORY_ROWS = 2000


def generate_vendors():
    vendors = []
    for idx in range(1, VENDOR_COUNT + 1):
        vendor_id = f"V{idx:04d}"
        category = PRODUCTS[(idx - 1) % len(PRODUCTS)][2]
        location = random.choice(LOCATIONS)
        contract_type = random.choices(CONTRACT_TYPES, weights=[0.4, 0.4, 0.2])[0]
        payment_terms = random.choice(PAYMENT_TERMS)
        rating = round(random.uniform(3.2, 5.0), 2)
        vendors.append(
            {
                "vendor_id": vendor_id,
                "vendor_name": f"{category} Supply Co. {idx}",
                "category": category,
                "location": location,
                "contract_type": contract_type,
                "payment_terms": payment_terms,
                "rating": rating,
            }
        )
    return vendors


def random_date(start: date, end: date) -> date:
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))


def month_index(row_date: date) -> int:
    return (row_date.year - START_DATE.year) * 12 + row_date.month


def generate_sales(vendors):
    rows = []
    product_lookup = {p[0]: p for p in PRODUCTS}
    for order_idx in range(1, SALES_ROWS + 1):
        order_date = random_date(START_DATE, END_DATE)
        product_id, product_name, category, base_price, base_cost = random.choice(PRODUCTS)
        region = random.choice(REGIONS)
        season_multiplier = 1.0
        if category == "Electronics" and order_date.month in (11, 12):
            season_multiplier = 1.15
        if category == "Packaging" and order_date.month in (6, 7, 8):
            season_multiplier = 1.08
        if order_date.year == 2026 and order_date.month == 7 and category in ("Finished Goods", "Electronics"):
            season_multiplier *= 0.85
        quantity = random.randint(1, 32)
        unit_price = round(base_price * season_multiplier * random.uniform(0.88, 1.12), 2)
        revenue = round(quantity * unit_price, 2)
        rows.append(
            {
                "order_id": f"SO{order_idx:06d}",
                "date": order_date.isoformat(),
                "product_id": product_id,
                "product_name": product_name,
                "category": category,
                "quantity": quantity,
                "unit_price": unit_price,
                "revenue": revenue,
                "region": region,
            }
        )
    return rows


def cost_trend(product_id: str, row_date: date) -> float:
    product = next(p for p in PRODUCTS if p[0] == product_id)
    base_cost = product[4]
    months_since_start = month_index(row_date)
    trend = 1.0 + 0.005 * months_since_start
    if product[2] == "Raw Materials" and row_date >= date(2026, 7, 1):
        trend += 0.18
    if product[2] == "Electronics" and row_date >= date(2026, 4, 1):
        trend += 0.08
    if product[2] == "Packaging" and row_date >= date(2025, 9, 1):
        trend += 0.06
    return round(base_cost * trend * random.uniform(0.95, 1.07), 2)


def generate_inventory(vendors):
    rows = []
    for idx in range(1, INVENTORY_ROWS + 1):
        inventory_date = random_date(START_DATE, END_DATE)
        product_id, product_name, category, base_price, base_cost = random.choice(PRODUCTS)
        vendor = random.choice([v for v in vendors if v["category"] == category])
        quantity = random.randint(14, 240)
        unit_cost = cost_trend(product_id, inventory_date)
        total_cost = round(quantity * unit_cost, 2)
        warehouse = random.choice(WAREHOUSES)
        rows.append(
            {
                "inventory_id": f"INV{idx:06d}",
                "date": inventory_date.isoformat(),
                "product_id": product_id,
                "product_name": product_name,
                "category": category,
                "quantity": quantity,
                "unit_cost": unit_cost,
                "total_cost": total_cost,
                "warehouse": warehouse,
                "vendor_id": vendor["vendor_id"],
            }
        )
    return rows


def write_csv(path: Path, rows, headers):
    with path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def main():
    random.seed(2026)
    vendors = generate_vendors()
    sales = generate_sales(vendors)
    inventory = generate_inventory(vendors)

    write_csv(RAW_DIR / "vendors.csv", vendors, ["vendor_id", "vendor_name", "category", "location", "contract_type", "payment_terms", "rating"])
    write_csv(RAW_DIR / "sales.csv", sales, ["order_id", "date", "product_id", "product_name", "category", "quantity", "unit_price", "revenue", "region"])
    write_csv(RAW_DIR / "inventory.csv", inventory, ["inventory_id", "date", "product_id", "product_name", "category", "quantity", "unit_cost", "total_cost", "warehouse", "vendor_id"])

    print(f"Generated {len(vendors)} vendors, {len(sales)} sales, {len(inventory)} inventory rows")


if __name__ == "__main__":
    main()
