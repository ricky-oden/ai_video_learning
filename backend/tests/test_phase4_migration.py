from sqlalchemy import inspect

from app.db.session import get_engine


def test_phase4_question_answer_tables_exist() -> None:
    tables = set(inspect(get_engine()).get_table_names())
    assert {
        "question_runs",
        "question_run_materials",
        "retrieval_runs",
        "retrieval_results",
        "answers",
        "answer_citations",
        "answer_feedback",
    }.issubset(tables)
