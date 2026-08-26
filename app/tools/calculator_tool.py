from __future__ import annotations
from typing import Any, Dict


def _as_float(value):
    try:
        return float(value)
    except Exception:
        raise ValueError("Invalid numeric input")


def percentage_change(old: Any, new: Any) -> Dict[str, Any]:
    old_f = _as_float(old)
    new_f = _as_float(new)
    if old_f == 0:
        return {"success": False, "error": "Division by zero (old value is zero)"}
    change = ((new_f - old_f) / abs(old_f)) * 100.0
    return {"success": True, "value": change}


def percentage_difference(a: Any, b: Any) -> Dict[str, Any]:
    a_f = _as_float(a)
    b_f = _as_float(b)
    denom = (abs(a_f) + abs(b_f)) / 2.0
    if denom == 0:
        return {"success": False, "error": "Division by zero (both values zero)"}
    diff = (abs(a_f - b_f) / denom) * 100.0
    return {"success": True, "value": diff}


def total(values) -> Dict[str, Any]:
    try:
        s = sum(float(v) for v in values)
        return {"success": True, "value": s}
    except Exception:
        return {"success": False, "error": "Invalid values for total"}


def average(values) -> Dict[str, Any]:
    try:
        nums = [float(v) for v in values]
        if not nums:
            return {"success": False, "error": "Empty collection"}
        return {"success": True, "value": sum(nums) / len(nums)}
    except Exception:
        return {"success": False, "error": "Invalid values for average"}


def ratio(numerator: Any, denominator: Any) -> Dict[str, Any]:
    num = _as_float(numerator)
    den = _as_float(denominator)
    if den == 0:
        return {"success": False, "error": "Division by zero"}
    return {"success": True, "value": num / den}


def growth_rate(start: Any, end: Any, periods: int = 1) -> Dict[str, Any]:
    s = _as_float(start)
    e = _as_float(end)
    if periods <= 0:
        return {"success": False, "error": "Periods must be positive"}
    if s <= 0:
        return {"success": False, "error": "Start value must be positive for growth rate"}
    try:
        rate = (e / s) ** (1.0 / periods) - 1.0
        return {"success": True, "value": rate}
    except Exception:
        return {"success": False, "error": "Error computing growth rate"}

def percentage_of(percentage: Any, value: Any) -> Dict[str, Any]:
    """Calculate a percentage of a value.

    Example:
        percentage_of(15, 470884.04)
        -> 70632.606
    """
    try:
        percentage_f = _as_float(percentage)
        value_f = _as_float(value)

        result = (percentage_f / 100.0) * value_f

        return {
            "success": True,
            "value": result,
        }

    except Exception:
        return {
            "success": False,
            "error": "Invalid percentage or value",
        }