from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.models import AuthSession, User
from app.db.session import get_session_factory
from app.security import hash_token
from app.seed import DEMO_PASSWORD


def login(client: TestClient, email: str = "member@example.com") -> dict[str, object]:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": DEMO_PASSWORD})
    assert response.status_code == 200
    return response.json()


def test_login_stores_only_sha256_token_hash_and_expires_in_eight_hours(
    client: TestClient,
) -> None:
    before = datetime.now(UTC)
    payload = login(client)
    raw_token = str(payload["access_token"])

    with get_session_factory()() as db:
        session = db.scalar(select(AuthSession))
        user = db.scalar(select(User).where(User.email == "member@example.com"))
        assert session is not None
        assert user is not None
        assert session.token_hash == hash_token(raw_token)
        assert session.token_hash != raw_token
        assert len(session.token_hash) == 64
        assert before + timedelta(hours=7, minutes=59) <= session.expires_at
        assert session.expires_at <= before + timedelta(hours=8, minutes=1)
        assert user.password_hash.startswith("$argon2id$")


def test_login_failure_and_inactive_user_are_rejected(client: TestClient) -> None:
    wrong = client.post(
        "/api/v1/auth/login",
        json={"email": "member@example.com", "password": "wrong-password"},
    )
    inactive = client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@example.com", "password": DEMO_PASSWORD},
    )
    assert wrong.status_code == 401
    assert inactive.status_code == 401


def test_relogin_revokes_old_session_and_keeps_one_active_session(client: TestClient) -> None:
    first = login(client)
    second = login(client)
    assert first["access_token"] != second["access_token"]

    with get_session_factory()() as db:
        sessions = db.scalars(select(AuthSession).order_by(AuthSession.created_at)).all()
        active_count = db.scalar(
            select(func.count()).select_from(AuthSession).where(AuthSession.revoked_at.is_(None))
        )
        assert len(sessions) == 2
        assert sessions[0].revoked_at is not None
        assert active_count == 1

    old_me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {first['access_token']}"},
    )
    assert old_me.status_code == 401


def test_me_logout_and_expired_session(client: TestClient) -> None:
    payload = login(client)
    headers = {"Authorization": f"Bearer {payload['access_token']}"}
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200
    assert client.post("/api/v1/auth/logout", headers=headers).json() == {"status": "revoked"}
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401

    expired = login(client)
    with get_session_factory()() as db:
        session = db.scalar(
            select(AuthSession).where(
                AuthSession.token_hash == hash_token(str(expired["access_token"]))
            )
        )
        assert session is not None
        session.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        db.commit()
    expired_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired['access_token']}"},
    )
    assert expired_response.status_code == 401
