import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text

from alembic import command
from app.core.settings import reset_settings
from app.db.session import get_engine, get_session_factory, reset_database_state
from app.db.test_guard import UnsafeTestDatabaseError, apply_test_database_url
from app.main import create_app
from app.seed import seed_database


def pytest_sessionstart(session: pytest.Session) -> None:
    del session
    try:
        apply_test_database_url()
    except UnsafeTestDatabaseError as exception:
        raise pytest.UsageError(str(exception)) from None
    reset_settings()
    reset_database_state()
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture(autouse=True)
def reset_phase2_tables() -> None:
    with get_engine().begin() as connection:
        connection.execute(text("TRUNCATE auth_sessions, materials, users CASCADE"))
    with get_session_factory()() as db:
        seed_database(db)


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())
