import os

from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError


class UnsafeTestDatabaseError(RuntimeError):
    """Raised before tests when the configured database is not safely isolated."""


def validate_test_database_url(raw_url: str | None) -> URL:
    if not raw_url:
        raise UnsafeTestDatabaseError("TEST_DATABASE_URL is required for backend tests.")

    try:
        url = make_url(raw_url)
    except ArgumentError as exception:
        raise UnsafeTestDatabaseError(
            "TEST_DATABASE_URL must be a valid database URL."
        ) from exception

    if not url.drivername.startswith("postgresql"):
        raise UnsafeTestDatabaseError("TEST_DATABASE_URL must use PostgreSQL.")
    if url.host != "test-db" or url.port != 5432:
        raise UnsafeTestDatabaseError("TEST_DATABASE_URL must target test-db:5432 explicitly.")
    if url.database != "ai_video_learning_test":
        raise UnsafeTestDatabaseError(
            "TEST_DATABASE_URL must target ai_video_learning_test exactly."
        )

    return url


def apply_test_database_url() -> URL:
    url = validate_test_database_url(os.environ.get("TEST_DATABASE_URL"))
    os.environ["DATABASE_URL"] = url.render_as_string(hide_password=False)
    return url
