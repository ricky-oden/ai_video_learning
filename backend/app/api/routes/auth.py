from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.api.auth_dependencies import CurrentAuth
from app.db.models import AuthSession, User
from app.db.session import get_db
from app.security import (
    generate_opaque_token,
    hash_token,
    session_expiry,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class UserResponse(BaseModel):
    id: str
    email: str
    role: Literal["MEMBER", "PREMIUM", "ADMIN"]

    @classmethod
    def from_user(cls, user: User) -> "UserResponse":
        return cls(id=str(user.id), email=user.email, role=user.role)


class LoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_at: datetime
    user: UserResponse


class LogoutResponse(BaseModel):
    status: Literal["revoked"] = "revoked"


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> LoginResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if (
        user is None
        or not user.is_active
        or not verify_password(user.password_hash, payload.password)
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    now = datetime.now(UTC)
    db.execute(
        update(AuthSession)
        .where(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None))
        .values(revoked_at=now)
    )
    raw_token = generate_opaque_token()
    auth_session = AuthSession(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=session_expiry(now),
    )
    db.add(auth_session)
    db.commit()
    return LoginResponse(
        access_token=raw_token,
        expires_at=auth_session.expires_at,
        user=UserResponse.from_user(user),
    )


@router.post("/logout", response_model=LogoutResponse)
def logout(auth: CurrentAuth, db: Annotated[Session, Depends(get_db)]) -> LogoutResponse:
    auth.session.revoked_at = datetime.now(UTC)
    db.commit()
    return LogoutResponse()


@router.get("/me", response_model=UserResponse)
def me(auth: CurrentAuth) -> UserResponse:
    return UserResponse.from_user(auth.user)
