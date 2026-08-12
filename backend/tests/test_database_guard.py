import os
from collections.abc import Generator
from typing import Annotated

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.settings import get_settings, reset_settings
from app.db.session import get_db, get_engine, reset_database_state
from app.db.test_guard import UnsafeTestDatabaseError, validate_test_database_url
from app.main import create_app


@pytest.fixture
def restore_database_environment() -> Generator[None, None, None]:
    original_database_url = os.environ.get("DATABASE_URL")
    original_test_database_url = os.environ.get("TEST_DATABASE_URL")
    yield
    for key, value in {
        "DATABASE_URL": original_database_url,
        "TEST_DATABASE_URL": original_test_database_url,
    }.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    reset_settings()
    reset_database_state()


def test_valid_test_database_url_is_accepted() -> None:
    url = validate_test_database_url(
        "postgresql+psycopg://ai_learning_test:test-only@test-db:5432/ai_video_learning_test"
    )
    assert (url.host, url.port, url.database) == (
        "test-db",
        5432,
        "ai_video_learning_test",
    )


@pytest.mark.parametrize(
    ("raw_url", "message"),
    [
        (None, "is required"),
        ("://", "must be a valid database URL"),
        ("sqlite:///ai_video_learning_test", "must use PostgreSQL"),
        (
            "postgresql+psycopg://ai_learning_test:test-only@db:5432/ai_video_learning_test",
            "must target test-db:5432",
        ),
        (
            "postgresql+psycopg://ai_learning_test:test-only@test-db:5432/ai_video_learning",
            "must target ai_video_learning_test exactly",
        ),
    ],
)
def test_unsafe_test_database_url_is_rejected(raw_url: str | None, message: str) -> None:
    with pytest.raises(UnsafeTestDatabaseError, match=message):
        validate_test_database_url(raw_url)


def test_depends_get_db_uses_real_test_database() -> None:
    application = create_app()

    @application.get("/api/v1/test-db-identity")
    def database_identity(
        session: Annotated[Session, Depends(get_db)],
    ) -> dict[str, str | int | None]:
        row = session.execute(
            text(
                "SELECT current_database() AS database_name, "
                "inet_server_addr()::text AS server_address, "
                "inet_server_port() AS server_port"
            )
        ).one()
        return {
            "configured_host": get_engine().url.host,
            "configured_port": get_engine().url.port,
            "database_name": row.database_name,
            "server_address": row.server_address,
            "server_port": row.server_port,
        }

    response = TestClient(application).get("/api/v1/test-db-identity")
    assert response.status_code == 200
    assert response.json()["configured_host"] == "test-db"
    assert response.json()["database_name"] == "ai_video_learning_test"


def test_unavailable_test_database_never_falls_back_to_development_database(
    restore_database_environment: None,
) -> None:
    os.environ["DATABASE_URL"] = (
        "postgresql+psycopg://ai_learning_app:development-only@db:5432/ai_video_learning"
    )
    unavailable_url = (
        "postgresql+psycopg://ai_learning_test:test-only@test-db:5432/ai_video_learning_test"
    )
    os.environ["TEST_DATABASE_URL"] = unavailable_url
    os.environ["DATABASE_URL"] = validate_test_database_url(unavailable_url).render_as_string(
        hide_password=False
    )
    reset_settings()
    reset_database_state()

    configured_url = make_url(get_settings().database_url)
    assert configured_url.host == "test-db"
    assert configured_url.database == "ai_video_learning_test"
    assert configured_url.database != "ai_video_learning"
