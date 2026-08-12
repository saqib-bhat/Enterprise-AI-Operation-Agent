from app.tools.data_analysis_tool import groupby_aggregate, compare_periods, trend_by_period


def test_groupby_aggregate():
    res = groupby_aggregate('sales', ['category'], {'revenue': 'sum'})
    assert res['success'] is True
    assert isinstance(res['data'], list)


def test_compare_periods():
    # compare June 2026 vs July 2026 revenue
    res = compare_periods('sales', 'date', '2026-06-01', '2026-06-30', '2026-07-01', '2026-07-31', 'revenue')
    assert res['success'] is True
    assert 'period_a' in res and 'period_b' in res


def test_trend_by_period():
    res = trend_by_period('sales', 'date', 'revenue', freq='M')
    assert res['success'] is True
    assert isinstance(res['data'], list)
