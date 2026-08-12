from sqlalchemy import inspect

from app.db.session import get_engine


def test_phase3_tables_and_vector_column_exist() -> None:
    inspector = inspect(get_engine())
    tables = set(inspector.get_table_names())
    assert {
        "transcript_versions",
        "transcript_segments",
        "transcript_chunks",
        "chunk_embeddings",
    }.issubset(tables)
    embedding = next(
        column
        for column in inspector.get_columns("chunk_embeddings")
        if column["name"] == "embedding"
    )
    assert str(embedding["type"]) == "VECTOR(32)"
