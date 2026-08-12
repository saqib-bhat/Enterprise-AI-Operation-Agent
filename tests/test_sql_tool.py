from app.tools.sql_tool import execute_select


def test_valid_select():
    res = execute_select('SELECT COUNT(*) as cnt FROM sales')
    assert res['success'] is True
    assert 'columns' in res and 'rows' in res


def test_select_aggregation():
    res = execute_select('SELECT category, SUM(quantity) as total_qty FROM sales GROUP BY category')
    assert res['success'] is True
    assert any('total_qty' in c or 'total_qty' for c in res['columns'])


def test_invalid_sql_handled():
    res = execute_select('SELEC * FROM sales')
    assert res['success'] is False


def test_reject_insert_update_delete_drop_alter():
    for stmt in ['INSERT INTO sales(order_id) VALUES(\'x\')', 'UPDATE sales SET quantity=1', 'DELETE FROM sales', 'DROP TABLE sales', 'ALTER TABLE sales RENAME TO s2']:
        res = execute_select(stmt)
        assert res['success'] is False


def test_reject_multiple_statements():
    res = execute_select('SELECT 1; SELECT 2')
    assert res['success'] is False
