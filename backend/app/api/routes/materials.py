import uuid
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.auth_dependencies import AdminAuth, CurrentAuth
from app.application.transcripts import TranscriptImportError, import_transcript
from app.db.models import (
    ChunkEmbedding,
    Material,
    TranscriptChunk,
    TranscriptSegment,
    TranscriptVersion,
)
from app.db.session import get_db
from app.providers.deterministic_embedding import DeterministicEmbeddingProvider

router = APIRouter(tags=["materials"])


class MaterialResponse(BaseModel):
    id: str
    title: str
    description: str
    required_role: Literal["MEMBER", "PREMIUM"]
    video_path: str
    duration_ms: int
    transcript_status: Literal["NOT_IMPORTED", "PROCESSING", "READY", "FAILED"]
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


class TranscriptImportRequest(BaseModel):
    fixture_id: str = Field(min_length=1, max_length=120)


class TranscriptVersionResponse(BaseModel):
    id: str
    material_id: str
    version: int
    source_fixture: str
    normalization_version: str
    chunking_version: str
    status: Literal["PROCESSING", "READY", "FAILED"]
    failure_code: str | None
    failure_message: str | None
    is_current: bool
    created_at: datetime
    published_at: datetime | None
    segment_count: int
    chunk_count: int
    embedding_count: int
    provider_name: str | None
    provider_version: str | None
    dimensions: int | None


class AdminMaterialResponse(MaterialResponse):
    current_version: int | None
    latest_version: int | None
    segment_count: int
    chunk_count: int
    embedding_count: int
    provider_name: str | None
    provider_version: str | None
    dimensions: int | None


def _version_response(db: Session, version: TranscriptVersion) -> TranscriptVersionResponse:
    segment_count = (
        db.scalar(
            select(func.count())
            .select_from(TranscriptSegment)
            .where(TranscriptSegment.transcript_version_id == version.id)
        )
        or 0
    )
    chunk_count = (
        db.scalar(
            select(func.count())
            .select_from(TranscriptChunk)
            .where(TranscriptChunk.transcript_version_id == version.id)
        )
        or 0
    )
    embedding_row = db.execute(
        select(
            func.count(ChunkEmbedding.id),
            func.min(ChunkEmbedding.provider_name),
            func.min(ChunkEmbedding.provider_version),
            func.min(ChunkEmbedding.dimensions),
        )
        .join(TranscriptChunk, ChunkEmbedding.chunk_id == TranscriptChunk.id)
        .where(TranscriptChunk.transcript_version_id == version.id)
    ).one()
    return TranscriptVersionResponse(
        id=str(version.id),
        material_id=str(version.material_id),
        version=version.version,
        source_fixture=version.source_fixture,
        normalization_version=version.normalization_version,
        chunking_version=version.chunking_version,
        status=version.status,
        failure_code=version.failure_code,
        failure_message=version.failure_message,
        is_current=version.is_current,
        created_at=version.created_at,
        published_at=version.published_at,
        segment_count=segment_count,
        chunk_count=chunk_count,
        embedding_count=embedding_row[0],
        provider_name=embedding_row[1],
        provider_version=embedding_row[2],
        dimensions=embedding_row[3],
    )


def _admin_material_response(db: Session, material: Material) -> AdminMaterialResponse:
    latest = db.scalar(
        select(TranscriptVersion)
        .where(TranscriptVersion.material_id == material.id)
        .order_by(TranscriptVersion.version.desc())
        .limit(1)
    )
    current = db.scalar(
        select(TranscriptVersion).where(
            TranscriptVersion.material_id == material.id,
            TranscriptVersion.is_current.is_(True),
        )
    )
    summary = _version_response(db, current) if current is not None else None
    return AdminMaterialResponse(
        **MaterialResponse.from_material(material).model_dump(),
        current_version=current.version if current else None,
        latest_version=latest.version if latest else None,
        segment_count=summary.segment_count if summary else 0,
        chunk_count=summary.chunk_count if summary else 0,
        embedding_count=summary.embedding_count if summary else 0,
        provider_name=summary.provider_name if summary else None,
        provider_version=summary.provider_version if summary else None,
        dimensions=summary.dimensions if summary else None,
    )


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


@router.get("/admin/materials", response_model=list[AdminMaterialResponse])
def list_admin_materials(
    _auth: AdminAuth, db: Annotated[Session, Depends(get_db)]
) -> list[AdminMaterialResponse]:
    materials = db.scalars(select(Material).order_by(Material.title)).all()
    return [_admin_material_response(db, item) for item in materials]


@router.post(
    "/admin/materials/{material_id}/transcript-imports",
    response_model=TranscriptVersionResponse,
)
def create_transcript_import(
    material_id: uuid.UUID,
    payload: TranscriptImportRequest,
    auth: AdminAuth,
    db: Annotated[Session, Depends(get_db)],
) -> TranscriptVersionResponse:
    try:
        version = import_transcript(
            db,
            material_id,
            payload.fixture_id,
            auth.user.id,
            DeterministicEmbeddingProvider(),
        )
    except TranscriptImportError as exception:
        status_code = (
            status.HTTP_404_NOT_FOUND
            if exception.code == "MATERIAL_NOT_FOUND"
            else status.HTTP_422_UNPROCESSABLE_CONTENT
        )
        raise HTTPException(status_code=status_code, detail=exception.safe_message) from None
    return _version_response(db, version)


@router.get(
    "/admin/materials/{material_id}/transcript-versions",
    response_model=list[TranscriptVersionResponse],
)
def list_transcript_versions(
    material_id: uuid.UUID,
    _auth: AdminAuth,
    db: Annotated[Session, Depends(get_db)],
) -> list[TranscriptVersionResponse]:
    if db.get(Material, material_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    versions = db.scalars(
        select(TranscriptVersion)
        .where(TranscriptVersion.material_id == material_id)
        .order_by(TranscriptVersion.version.desc())
    ).all()
    return [_version_response(db, version) for version in versions]


@router.get("/admin/transcript-versions/{version_id}", response_model=TranscriptVersionResponse)
def get_transcript_version(
    version_id: uuid.UUID,
    _auth: AdminAuth,
    db: Annotated[Session, Depends(get_db)],
) -> TranscriptVersionResponse:
    version = db.get(TranscriptVersion, version_id)
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return _version_response(db, version)
