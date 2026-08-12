import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.retrieval import RetrievedChunk, search_chunks
from app.application.transcripts import normalize_text
from app.db.models import (
    Answer,
    AnswerCitation,
    ChunkEmbedding,
    Material,
    QuestionRun,
    QuestionRunMaterial,
    RetrievalResult,
    RetrievalRun,
    TranscriptChunk,
    TranscriptVersion,
)
from app.providers.base import AnswerGenerationProvider, EmbeddingProvider, EvidenceInput

POLICY_VERSION = "evidence-policy-v1"
TOP_K = 5
MAX_SELECTED = 3
LEXICAL_OVERLAP_THRESHOLD = 0.20
COSINE_DISTANCE_THRESHOLD = 0.55


class QuestionProcessingError(Exception):
    def __init__(self, code: str, safe_message: str):
        super().__init__(safe_message)
        self.code = code
        self.safe_message = safe_message


@dataclass(frozen=True)
class EvidenceDecision:
    status: str
    selected_indexes: tuple[int, ...]
    overlap_ratios: tuple[float, ...]


def character_bigrams(text: str) -> set[str]:
    compact = normalize_text(text).replace(" ", "")
    return {compact[index : index + 2] for index in range(len(compact) - 1)}


def lexical_overlap_ratio(question: str, evidence: str) -> float:
    question_bigrams = character_bigrams(question)
    if not question_bigrams:
        return 0.0
    return len(question_bigrams & character_bigrams(evidence)) / len(question_bigrams)


def decide_evidence(question: str, chunks: list[RetrievedChunk]) -> EvidenceDecision:
    ratios = tuple(lexical_overlap_ratio(question, chunk.text) for chunk in chunks)
    if not ratios or max(ratios) == 0:
        return EvidenceDecision("REFUSED_OUT_OF_SCOPE", (), ratios)
    best_index = max(range(len(chunks)), key=lambda index: ratios[index])
    if (
        ratios[best_index] < LEXICAL_OVERLAP_THRESHOLD
        or chunks[best_index].distance > COSINE_DISTANCE_THRESHOLD
    ):
        return EvidenceDecision("REFUSED_INSUFFICIENT_EVIDENCE", (), ratios)
    selected = tuple(
        index
        for index, _chunk in sorted(
            enumerate(chunks), key=lambda item: (-ratios[item[0]], item[1].distance, item[0])
        )
        if ratios[index] > 0
    )[:MAX_SELECTED]
    return EvidenceDecision("COMPLETED", selected, ratios)


def _can_access(role: str, required_role: str) -> bool:
    return role == "ADMIN" or role == "PREMIUM" or required_role == "MEMBER"


def _validate_materials(db: Session, role: str, material_ids: list[uuid.UUID]) -> list[Material]:
    materials = db.scalars(select(Material).where(Material.id.in_(material_ids))).all()
    by_id = {material.id: material for material in materials}
    if len(by_id) != len(material_ids):
        raise QuestionProcessingError("MATERIAL_NOT_FOUND", "A material was not found.")
    ordered = [by_id[material_id] for material_id in material_ids]
    if any(not material.is_active for material in ordered):
        raise QuestionProcessingError("MATERIAL_NOT_FOUND", "A material was not found.")
    if any(not _can_access(role, material.required_role) for material in ordered):
        raise QuestionProcessingError("MATERIAL_FORBIDDEN", "A material is not accessible.")
    return ordered


def _assert_embedding_compatibility(
    db: Session, material_ids: list[uuid.UUID], provider: EmbeddingProvider
) -> None:
    metadata = db.execute(
        select(
            ChunkEmbedding.provider_name,
            ChunkEmbedding.provider_version,
            ChunkEmbedding.dimensions,
        )
        .join(TranscriptChunk, ChunkEmbedding.chunk_id == TranscriptChunk.id)
        .join(TranscriptVersion, TranscriptChunk.transcript_version_id == TranscriptVersion.id)
        .where(
            TranscriptVersion.material_id.in_(material_ids),
            TranscriptVersion.status == "READY",
            TranscriptVersion.is_current.is_(True),
        )
        .distinct()
    ).all()
    expected = (
        provider.metadata.provider_name,
        provider.metadata.provider_version,
        provider.metadata.dimensions,
    )
    if metadata and any(tuple(row) != expected for row in metadata):
        raise QuestionProcessingError(
            "EMBEDDING_METADATA_MISMATCH", "Embedding metadata does not match."
        )


def process_question(
    db: Session,
    user_id: uuid.UUID,
    role: str,
    question: str,
    material_ids: list[uuid.UUID],
    embedding_provider: EmbeddingProvider,
    answer_provider: AnswerGenerationProvider,
) -> QuestionRun:
    _validate_materials(db, role, material_ids)
    run = QuestionRun(user_id=user_id, question=question, status="PROCESSING")
    db.add(run)
    db.flush()
    for material_id in material_ids:
        db.add(QuestionRunMaterial(question_run_id=run.id, material_id=material_id))
    db.commit()
    run_id = run.id

    try:
        _assert_embedding_compatibility(db, material_ids, embedding_provider)
        chunks = search_chunks(
            db,
            question,
            role,
            embedding_provider,
            material_ids=material_ids,
            limit=TOP_K,
        )
        decision = decide_evidence(question, chunks)
        retrieval = RetrievalRun(
            question_run_id=run_id,
            provider_name=embedding_provider.metadata.provider_name,
            provider_version=embedding_provider.metadata.provider_version,
            dimensions=embedding_provider.metadata.dimensions,
            top_k=TOP_K,
            policy_version=POLICY_VERSION,
            lexical_overlap_threshold=LEXICAL_OVERLAP_THRESHOLD,
            cosine_distance_threshold=COSINE_DISTANCE_THRESHOLD,
        )
        db.add(retrieval)
        db.flush()
        results: list[RetrievalResult] = []
        for index, chunk in enumerate(chunks):
            result = RetrievalResult(
                retrieval_run_id=retrieval.id,
                chunk_id=chunk.chunk_id,
                rank=index + 1,
                distance=chunk.distance,
                lexical_overlap_ratio=decision.overlap_ratios[index],
                is_selected=index in decision.selected_indexes,
            )
            db.add(result)
            results.append(result)
        db.flush()

        run = db.get(QuestionRun, run_id)
        if run is None:
            raise QuestionProcessingError("RUN_MISSING", "Question run is missing.")
        if decision.status != "COMPLETED":
            run.status = decision.status
            run.completed_at = datetime.now(UTC)
            db.commit()
            return run

        selected = [(chunks[index], results[index]) for index in decision.selected_indexes]
        generated = answer_provider.generate(
            question,
            [
                EvidenceInput(citation_id=str(result.id), text=chunk.text)
                for chunk, result in selected
            ],
        )
        allowed = {str(result.id): (chunk, result) for chunk, result in selected}
        if not generated.citation_ids or any(
            citation_id not in allowed for citation_id in generated.citation_ids
        ):
            raise QuestionProcessingError(
                "INVALID_PROVIDER_CITATION", "Generated citations are invalid."
            )
        answer = Answer(
            question_run_id=run_id,
            body=generated.body,
            provider_name=generated.provider_name,
            provider_version=generated.provider_version,
        )
        db.add(answer)
        db.flush()
        for order, citation_id in enumerate(generated.citation_ids, start=1):
            chunk, result = allowed[citation_id]
            db.add(
                AnswerCitation(
                    answer_id=answer.id,
                    retrieval_result_id=result.id,
                    transcript_version_id=chunk.transcript_version_id,
                    chunk_id=chunk.chunk_id,
                    material_id=chunk.material_id,
                    video_path_snapshot=chunk.video_path,
                    start_ms=chunk.start_ms,
                    end_ms=chunk.end_ms,
                    text_snapshot=chunk.text,
                    display_order=order,
                )
            )
        run.status = "COMPLETED"
        run.completed_at = datetime.now(UTC)
        db.commit()
        db.refresh(run)
        return run
    except Exception as exception:
        db.rollback()
        failed = db.get(QuestionRun, run_id)
        if failed is not None:
            failed.status = "FAILED"
            failed.failure_code = (
                exception.code
                if isinstance(exception, QuestionProcessingError)
                else "QUESTION_PROCESSING_FAILED"
            )
            failed.completed_at = datetime.now(UTC)
            db.commit()
            return failed
        raise
