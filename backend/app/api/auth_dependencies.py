from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import AuthSession, User
from app.db.session import get_db
from app.security import hash_token


@dataclass(frozen=True)
class AuthContext:
    user: User
    session: AuthSession


def get_auth_context(request: Request, db: Annotated[Session, Depends(get_db)]) -> AuthContext:
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    auth_session = db.scalar(
        select(AuthSession)
        .options(joinedload(AuthSession.user))
        .where(AuthSession.token_hash == hash_token(token))
    )
    now = datetime.now(UTC)
    if (
        auth_session is None
        or auth_session.revoked_at is not None
        or auth_session.expires_at <= now
        or not auth_session.user.is_active
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return AuthContext(user=auth_session.user, session=auth_session)


CurrentAuth = Annotated[AuthContext, Depends(get_auth_context)]


def require_admin(auth: CurrentAuth) -> AuthContext:
    if auth.user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return auth


AdminAuth = Annotated[AuthContext, Depends(require_admin)]


def require_premium(auth: CurrentAuth) -> AuthContext:
    if auth.user.role not in {"PREMIUM", "ADMIN"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return auth


PremiumAuth = Annotated[AuthContext, Depends(require_premium)]
