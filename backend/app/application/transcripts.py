import json
import re
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.db.models import (
    ChunkEmbedding,
    Material,
    TranscriptChunk,
    TranscriptSegment,
    TranscriptVersion,
)
from app.providers.base import EmbeddingProvider

NORMALIZATION_VERSION = "nfkc-whitespace-v1"
CHUNKING_VERSION = "segment-window-3-overlap-1-v1"

MEMBER_MATERIAL_ID = uuid.UUID("20000000-0000-4000-8000-000000000001")
PREMIUM_MATERIAL_ID = uuid.UUID("20000000-0000-4000-8000-000000000002")
FIXTURE_ROOT = Path(__file__).resolve().parents[2] / "fixtures" / "transcripts"
FIXTURE_REGISTRY = {
    "hair-cut-basic-v1": (MEMBER_MATERIAL_ID, FIXTURE_ROOT / "hair-cut-basic-v1.json"),
    "hair-consultation-premium-v1": (
        PREMIUM_MATERIAL_ID,
        FIXTURE_ROOT / "hair-consultation-premium-v1.json",
    ),
    "invalid-sequence-v1": (MEMBER_MATERIAL_ID, FIXTURE_ROOT / "invalid-sequence-v1.json"),
}


class FixtureSegment(BaseModel):
    model_config = ConfigDict(strict=True)
    sequence: int
    start_ms: int
    end_ms: int
    text: str


class TranscriptFixture(BaseModel):
    model_config = ConfigDict(strict=True)
    fixture_id: str
    segments: list[FixtureSegment]


class TranscriptImportError(Exception):
    def __init__(self, code: str, message: str, version_id: uuid.UUID | None = None):
        super().__init__(message)
        self.code = code
        self.safe_message = message
        self.version_id = version_id


@dataclass(frozen=True)
class NormalizedSegment:
    sequence: int
    start_ms: int
    end_ms: int
    original_text: str
    normalized_text: str


@dataclass(frozen=True)
class ChunkData:
    sequence: int
    text: str
    first_segment_sequence: int
    last_segment_sequence: int
    start_ms: int
    end_ms: int


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text)).strip()


def validate_and_normalize(fixture: TranscriptFixture) -> list[NormalizedSegment]:
    if not fixture.segments:
        raise TranscriptImportError("EMPTY_TRANSCRIPT", "Transcript must contain segments.")
    result: list[NormalizedSegment] = []
    errors: list[str] = []
    previous_end = 0
    for expected, segment in enumerate(fixture.segments, start=1):
        normalized = normalize_text(segment.text)
        if segment.sequence != expected:
            errors.append("sequence must start at 1 and be continuous")
        if segment.start_ms < 0 or segment.end_ms <= segment.start_ms:
            errors.append("segment time range is invalid")
        if expected > 1 and segment.start_ms < previous_end:
            errors.append("segment time ranges overlap")
        if not normalized:
            errors.append("segment text must not be blank")
        previous_end = segment.end_ms
        result.append(
            NormalizedSegment(
                sequence=segment.sequence,
                start_ms=segment.start_ms,
                end_ms=segment.end_ms,
                original_text=segment.text,
                normalized_text=normalized,
            )
        )
    if errors:
        raise TranscriptImportError("INVALID_TRANSCRIPT", "; ".join(dict.fromkeys(errors)))
    return result


def build_chunks(segments: list[NormalizedSegment]) -> list[ChunkData]:
    chunks: list[ChunkData] = []
    start = 0
    while start < len(segments):
        window = segments[start : start + 3]
        chunks.append(
            ChunkData(
                sequence=len(chunks) + 1,
                text=" ".join(segment.normalized_text for segment in window),
                first_segment_sequence=window[0].sequence,
                last_segment_sequence=window[-1].sequence,
                start_ms=window[0].start_ms,
                end_ms=window[-1].end_ms,
            )
        )
        if start + len(window) >= len(segments):
            break
        start += 2
    return chunks


def load_fixture(fixture_id: str, material_id: uuid.UUID) -> TranscriptFixture:
    registered = FIXTURE_REGISTRY.get(fixture_id)
    if registered is None:
        raise TranscriptImportError("FIXTURE_NOT_ALLOWED", "Transcript fixture is not allowed.")
    expected_material_id, path = registered
    if expected_material_id != material_id:
        raise TranscriptImportError(
            "FIXTURE_MATERIAL_MISMATCH", "Transcript fixture does not match the material."
        )
    try:
        fixture = TranscriptFixture.model_validate(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ValidationError):
        raise TranscriptImportError("INVALID_FIXTURE", "Transcript fixture is invalid.") from None
    if fixture.fixture_id != fixture_id:
        raise TranscriptImportError("FIXTURE_ID_MISMATCH", "Transcript fixture ID is invalid.")
    return fixture


def import_transcript(
    db: Session,
    material_id: uuid.UUID,
    fixture_id: str,
    created_by: uuid.UUID,
    provider: EmbeddingProvider,
) -> TranscriptVersion:
    material = db.get(Material, material_id)
    if material is None:
        raise TranscriptImportError("MATERIAL_NOT_FOUND", "Material was not found.")
    next_version = (
        db.scalar(
            select(func.coalesce(func.max(TranscriptVersion.version), 0)).where(
                TranscriptVersion.material_id == material_id
            )
        )
        or 0
    ) + 1
    version = TranscriptVersion(
        material_id=material_id,
        version=next_version,
        source_fixture=fixture_id,
        normalization_version=NORMALIZATION_VERSION,
        chunking_version=CHUNKING_VERSION,
        status="PROCESSING",
        created_by=created_by,
        is_current=False,
    )
    material.transcript_status = "PROCESSING"
    db.add(version)
    db.commit()
    version_id = version.id

    try:
        fixture = load_fixture(fixture_id, material_id)
        segments = validate_and_normalize(fixture)
        chunks = build_chunks(segments)
        vectors = provider.embed_many([chunk.text for chunk in chunks])
        if len(vectors) != len(chunks) or any(
            len(vector) != provider.metadata.dimensions for vector in vectors
        ):
            raise TranscriptImportError("PROVIDER_CONTRACT_ERROR", "Embedding output is invalid.")

        version = db.get(TranscriptVersion, version_id)
        material = db.get(Material, material_id)
        if version is None or material is None:
            raise TranscriptImportError(
                "IMPORT_STATE_MISSING", "Transcript import state is missing."
            )
        db.execute(
            update(TranscriptVersion)
            .where(
                TranscriptVersion.material_id == material_id,
                TranscriptVersion.is_current.is_(True),
            )
            .values(is_current=False)
        )
        for segment in segments:
            db.add(
                TranscriptSegment(
                    transcript_version_id=version_id,
                    sequence=segment.sequence,
                    original_text=segment.original_text,
                    normalized_text=segment.normalized_text,
                    start_ms=segment.start_ms,
                    end_ms=segment.end_ms,
                )
            )
        for chunk, vector in zip(chunks, vectors, strict=True):
            chunk_id = uuid.uuid4()
            db.add(
                TranscriptChunk(
                    id=chunk_id,
                    transcript_version_id=version_id,
                    sequence=chunk.sequence,
                    text=chunk.text,
                    first_segment_sequence=chunk.first_segment_sequence,
                    last_segment_sequence=chunk.last_segment_sequence,
                    start_ms=chunk.start_ms,
                    end_ms=chunk.end_ms,
                )
            )
            db.add(
                ChunkEmbedding(
                    chunk_id=chunk_id,
                    provider_name=provider.metadata.provider_name,
                    provider_version=provider.metadata.provider_version,
                    dimensions=provider.metadata.dimensions,
                    embedding=vector,
                )
            )
        version.status = "READY"
        version.is_current = True
        version.published_at = datetime.now(UTC)
        material.transcript_status = "READY"
        db.commit()
        db.refresh(version)
        return version
    except Exception as exception:
        db.rollback()
        failed = db.get(TranscriptVersion, version_id)
        material = db.get(Material, material_id)
        if failed is not None:
            failed.status = "FAILED"
            failed.is_current = False
            if isinstance(exception, TranscriptImportError):
                failed.failure_code = exception.code
                failed.failure_message = exception.safe_message[:240]
            else:
                failed.failure_code = "IMPORT_FAILED"
                failed.failure_message = "Transcript import failed."
        has_current = db.scalar(
            select(TranscriptVersion.id).where(
                TranscriptVersion.material_id == material_id,
                TranscriptVersion.status == "READY",
                TranscriptVersion.is_current.is_(True),
            )
        )
        if material is not None:
            material.transcript_status = "READY" if has_current else "FAILED"
        db.commit()
        if isinstance(exception, TranscriptImportError):
            exception.version_id = version_id
            raise
        raise TranscriptImportError(
            "IMPORT_FAILED", "Transcript import failed.", version_id
        ) from None
