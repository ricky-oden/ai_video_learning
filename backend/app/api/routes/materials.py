import uuid
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth_dependencies import AdminAuth, CurrentAuth
from app.db.models import Material
from app.db.session import get_db

router = APIRouter(tags=["materials"])


class MaterialResponse(BaseModel):
    id: str
    title: str
    description: str
    required_role: Literal["MEMBER", "PREMIUM"]
    video_path: str
    duration_ms: int
    transcript_status: Literal["NOT_IMPORTED"]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_material(cls, material: Material) -> "MaterialResponse":
        return cls(
            id=str(material.id),
            title=material.title,
            description=material.description,
            required_role=material.required_role,
            video_path=material.video_path,
            duration_ms=material.duration_ms,
            transcript_status=material.transcript_status,
            is_active=material.is_active,
            created_at=material.created_at,
            updated_at=material.updated_at,
        )


def _can_access(role: str, required_role: str) -> bool:
    if role == "ADMIN":
        return True
    if role == "PREMIUM":
        return required_role in {"MEMBER", "PREMIUM"}
    return required_role == "MEMBER"


@router.get("/materials", response_model=list[MaterialResponse])
def list_materials(
    auth: CurrentAuth, db: Annotated[Session, Depends(get_db)]
) -> list[MaterialResponse]:
    materials = db.scalars(
        select(Material).where(Material.is_active.is_(True)).order_by(Material.title)
    ).all()
    return [
        MaterialResponse.from_material(item)
        for item in materials
        if _can_access(auth.user.role, item.required_role)
    ]


@router.get("/materials/{material_id}", response_model=MaterialResponse)
def get_material(
    material_id: uuid.UUID,
    auth: CurrentAuth,
    db: Annotated[Session, Depends(get_db)],
) -> MaterialResponse:
    material = db.get(Material, material_id)
    if material is None or not material.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if not _can_access(auth.user.role, material.required_role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return MaterialResponse.from_material(material)


@router.get("/admin/materials", response_model=list[MaterialResponse])
def list_admin_materials(
    _auth: AdminAuth, db: Annotated[Session, Depends(get_db)]
) -> list[MaterialResponse]:
    materials = db.scalars(select(Material).order_by(Material.title)).all()
    return [MaterialResponse.from_material(item) for item in materials]
