from sqlalchemy import text

from app.db.session import get_engine


def test_pgvector_extension_and_vector_type_are_available() -> None:
    with get_engine().connect() as connection:
        extension_version = connection.execute(
            text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        ).scalar_one()
        vector_value = connection.execute(text("SELECT '[1,2,3]'::vector::text")).scalar_one()

    assert extension_version == "0.8.1"
    assert vector_value == "[1,2,3]"
