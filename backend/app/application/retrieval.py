import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.transcripts import normalize_text
from app.db.models import ChunkEmbedding, Material, TranscriptChunk, TranscriptVersion
from app.providers.base import EmbeddingProvider


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: uuid.UUID
    material_id: uuid.UUID
    transcript_version_id: uuid.UUID
    video_path: str
    text: str
    start_ms: int
    end_ms: int
    distance: float


def search_chunks(
    db: Session,
    question: str,
    role: str,
    provider: EmbeddingProvider,
    material_ids: list[uuid.UUID] | None = None,
    limit: int = 5,
) -> list[RetrievedChunk]:
    query_vector = provider.embed_many([normalize_text(question)])[0]
    distance = ChunkEmbedding.embedding.cosine_distance(query_vector)
    statement = (
        select(
            TranscriptChunk,
            TranscriptVersion.material_id,
            TranscriptVersion.id,
            Material.video_path,
            distance.label("distance"),
        )
        .join(TranscriptVersion, TranscriptChunk.transcript_version_id == TranscriptVersion.id)
        .join(Material, TranscriptVersion.material_id == Material.id)
        .join(ChunkEmbedding, ChunkEmbedding.chunk_id == TranscriptChunk.id)
        .where(
            TranscriptVersion.status == "READY",
            TranscriptVersion.is_current.is_(True),
            Material.is_active.is_(True),
            ChunkEmbedding.provider_name == provider.metadata.provider_name,
            ChunkEmbedding.provider_version == provider.metadata.provider_version,
            ChunkEmbedding.dimensions == provider.metadata.dimensions,
        )
        .order_by(distance)
        .limit(limit)
    )
    if role == "MEMBER":
        statement = statement.where(Material.required_role == "MEMBER")
    elif role not in {"PREMIUM", "ADMIN"}:
        return []
    if material_ids is not None:
        statement = statement.where(Material.id.in_(material_ids))
    return [
        RetrievedChunk(
            chunk_id=chunk.id,
            material_id=material_id,
            transcript_version_id=transcript_version_id,
            video_path=video_path,
            text=chunk.text,
            start_ms=chunk.start_ms,
            end_ms=chunk.end_ms,
            distance=float(chunk_distance),
        )
        for chunk, material_id, transcript_version_id, video_path, chunk_distance in db.execute(
            statement
        ).all()
    ]
