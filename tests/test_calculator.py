from app.tools.calculator_tool import (
    percentage_change,
    percentage_difference,
    total,
    average,
    ratio,
    growth_rate,
)


def test_percentage_change():
    r = percentage_change(100000, 118000)
    assert r['success'] and abs(r['value'] - 18.0) < 1e-6


def test_percentage_difference():
    r = percentage_difference(100, 120)
    assert r['success'] and r['value'] > 0


def test_total_average():
    r = total([1, 2, 3, 4])
    assert r['success'] and r['value'] == 10
    a = average([1, 2, 3, 4])
    assert a['success'] and a['value'] == 2.5


def test_ratio_and_growth():
    r = ratio(10, 2)
    assert r['success'] and r['value'] == 5
    g = growth_rate(100, 121, periods=2)
    assert g['success'] and abs(g['value'] - 0.1) < 1e-6


def test_division_by_zero_and_invalid_input():
    assert not ratio(1, 0)['success']
    assert not percentage_change(0, 10)['success']
    assert not average([])['success']
