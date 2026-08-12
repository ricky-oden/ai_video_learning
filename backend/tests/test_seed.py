from sqlalchemy import func, select

from app.db.models import Material, User
from app.db.session import get_session_factory
from app.seed import seed_database


def test_seed_is_idempotent() -> None:
    with get_session_factory()() as db:
        seed_database(db)
        seed_database(db)
        assert db.scalar(select(func.count()).select_from(User)) == 4
        assert db.scalar(select(func.count()).select_from(Material)) == 3
