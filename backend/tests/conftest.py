import pytest

from app.core.settings import reset_settings
from app.db.session import reset_database_state
from app.db.test_guard import UnsafeTestDatabaseError, apply_test_database_url


def pytest_sessionstart(session: pytest.Session) -> None:
    del session
    try:
        apply_test_database_url()
    except UnsafeTestDatabaseError as exception:
        raise pytest.UsageError(str(exception)) from None
    reset_settings()
    reset_database_state()
