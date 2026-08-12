from sqlalchemy import inspect

from app.db.session import get_engine


def test_phase2_tables_exist_in_postgresql() -> None:
    table_names = set(inspect(get_engine()).get_table_names())
    assert {"users", "auth_sessions", "materials"}.issubset(table_names)
