from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"]
    database: Literal["ok"]


@router.get("/health", response_model=HealthResponse)
def health(session: Annotated[Session, Depends(get_db)]) -> HealthResponse:
    session.execute(text("SELECT 1"))
    return HealthResponse(status="ok", database="ok")
