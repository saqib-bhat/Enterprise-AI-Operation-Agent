from __future__ import annotations
from typing import Any, Dict, List
import pandas as pd
from pathlib import Path
from datetime import datetime


DATA_FILES = {
    "sales": Path("data/raw/sales.csv"),
    "inventory": Path("data/raw/inventory.csv"),
}


def _load_table(name: str) -> pd.DataFrame:
    if name not in DATA_FILES:
        raise ValueError("Unknown data source")
    path = DATA_FILES[name]
    df = pd.read_csv(path, parse_dates=["date"]) if path.exists() else pd.DataFrame()
    return df


def groupby_aggregate(source: str, group_by: List[str], aggregations: Dict[str, str]) -> Dict[str, Any]:
    """Group by columns and aggregate using allowed aggregation functions.

    aggregations: mapping column -> agg func e.g. {'revenue':'sum','quantity':'mean'}
    """
    try:
        df = _load_table(source)
        if df.empty:
            return {"success": False, "error": "Source data not found or empty"}
        # sanitize columns
        for c in group_by:
            if c not in df.columns:
                return {"success": False, "error": f"Group column {c} not in data"}
        for c in aggregations.keys():
            if c not in df.columns:
                return {"success": False, "error": f"Aggregate column {c} not in data"}
        res = df.groupby(group_by).agg(aggregations).reset_index()
        # convert to records
        return {"success": True, "data": res.to_dict(orient="records")}
    except Exception as e:
        return {"success": False, "error": str(e)}


def compare_periods(source: str, date_column: str, start_a: str, end_a: str, start_b: str, end_b: str, metric: str) -> Dict[str, Any]:
    """Compare aggregation of metric between two date ranges (inclusive). Dates are ISO strings."""
    try:
        df = _load_table(source)
        if df.empty:
            return {"success": False, "error": "Source data not found or empty"}
        if date_column not in df.columns:
            return {"success": False, "error": "Date column not found"}
        if metric not in df.columns:
            return {"success": False, "error": "Metric column not found"}
        a1 = pd.to_datetime(start_a)
        a2 = pd.to_datetime(end_a)
        b1 = pd.to_datetime(start_b)
        b2 = pd.to_datetime(end_b)
        df[date_column] = pd.to_datetime(df[date_column])
        val_a = df[(df[date_column] >= a1) & (df[date_column] <= a2)][metric].sum()
        val_b = df[(df[date_column] >= b1) & (df[date_column] <= b2)][metric].sum()
        return {"success": True, "period_a": val_a, "period_b": val_b}
    except Exception as e:
        return {"success": False, "error": str(e)}


def trend_by_period(source: str, date_column: str, metric: str, freq: str = "M") -> Dict[str, Any]:
    """Return time series aggregation by frequency (M=month) for the metric."""
    try:
        df = _load_table(source)
        if df.empty:
            return {"success": False, "error": "Source data not found or empty"}
        if date_column not in df.columns or metric not in df.columns:
            return {"success": False, "error": "Required columns not found"}
        df[date_column] = pd.to_datetime(df[date_column])
        ts = df.set_index(date_column).resample(freq)[metric].sum()
        # compute pct change
        pct = ts.pct_change().fillna(0)
        result = []
        for idx, val in ts.items():
            result.append({"period": idx.strftime('%Y-%m'), "value": float(val), "pct_change": float(pct.loc[idx])})
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
