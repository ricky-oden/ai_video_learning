import uuid
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.auth_dependencies import CurrentAuth, PremiumAuth
from app.application.questions import QuestionProcessingError, process_question
from app.db.models import Answer, AnswerFeedback, QuestionRun
from app.db.session import get_db
from app.providers.base import AnswerGenerationProvider, EmbeddingProvider
from app.providers.deterministic_embedding import DeterministicEmbeddingProvider
from app.providers.grounded_answer import GroundedExtractiveAnswerProvider

router = APIRouter(tags=["questions"])


def get_embedding_provider() -> EmbeddingProvider:
    return DeterministicEmbeddingProvider()


def get_answer_provider() -> AnswerGenerationProvider:
    return GroundedExtractiveAnswerProvider()


EmbeddingDependency = Annotated[EmbeddingProvider, Depends(get_embedding_provider)]
AnswerDependency = Annotated[AnswerGenerationProvider, Depends(get_answer_provider)]


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    material_ids: list[uuid.UUID] = Field(min_length=1, max_length=5)

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must not be blank")
        return value

    @field_validator("material_ids")
    @classmethod
    def material_ids_must_be_unique(cls, value: list[uuid.UUID]) -> list[uuid.UUID]:
        if len(value) != len(set(value)):
            raise ValueError("material_ids must not contain duplicates")
        return value


class CitationResponse(BaseModel):
    id: str
    material_id: str
    transcript_version_id: str
    chunk_id: str
    video_path: str
    start_ms: int
    end_ms: int
    text_snapshot: str
    display_order: int


class AnswerResponse(BaseModel):
    id: str
    body: str
    provider_name: str
    provider_version: str
    citations: list[CitationResponse]


class QuestionRunResponse(BaseModel):
    run_id: str
    question: str
    material_ids: list[str]
    status: Literal[
        "PROCESSING",
        "COMPLETED",
        "REFUSED_INSUFFICIENT_EVIDENCE",
        "REFUSED_OUT_OF_SCOPE",
        "FAILED",
    ]
    failure_code: str | None
    created_at: datetime
    completed_at: datetime | None
    answer: AnswerResponse | None


class FeedbackRequest(BaseModel):
    rating: Literal["UP", "DOWN"]
    comment: str | None = Field(default=None, max_length=500)


class FeedbackResponse(BaseModel):
    id: str
    answer_id: str
    rating: Literal["UP", "DOWN"]
    comment: str | None


def _load_run(db: Session, run_id: uuid.UUID) -> QuestionRun | None:
    return db.scalar(
        select(QuestionRun)
        .options(
            selectinload(QuestionRun.materials),
            selectinload(QuestionRun.answer).selectinload(Answer.citations),
        )
        .where(QuestionRun.id == run_id)
    )


def _response(run: QuestionRun) -> QuestionRunResponse:
    answer = None
    if run.answer is not None:
        citations = sorted(run.answer.citations, key=lambda item: item.display_order)
        answer = AnswerResponse(
            id=str(run.answer.id),
            body=run.answer.body,
            provider_name=run.answer.provider_name,
            provider_version=run.answer.provider_version,
            citations=[
                CitationResponse(
                    id=str(citation.id),
                    material_id=str(citation.material_id),
                    transcript_version_id=str(citation.transcript_version_id),
                    chunk_id=str(citation.chunk_id),
                    video_path=citation.video_path_snapshot,
                    start_ms=citation.start_ms,
                    end_ms=citation.end_ms,
                    text_snapshot=citation.text_snapshot,
                    display_order=citation.display_order,
                )
                for citation in citations
            ],
        )
    return QuestionRunResponse(
        run_id=str(run.id),
        question=run.question,
        material_ids=[str(item.material_id) for item in run.materials],
        status=run.status,
        failure_code=run.failure_code,
        created_at=run.created_at,
        completed_at=run.completed_at,
        answer=answer,
    )


@router.post("/question-runs", response_model=QuestionRunResponse)
def create_question_run(
    payload: QuestionRequest,
    auth: PremiumAuth,
    db: Annotated[Session, Depends(get_db)],
    embedding_provider: EmbeddingDependency,
    answer_provider: AnswerDependency,
) -> QuestionRunResponse:
    try:
        run = process_question(
            db,
            auth.user.id,
            auth.user.role,
            payload.question,
            payload.material_ids,
            embedding_provider,
            answer_provider,
        )
    except QuestionProcessingError as exception:
        code = (
            status.HTTP_403_FORBIDDEN
            if exception.code == "MATERIAL_FORBIDDEN"
            else status.HTTP_404_NOT_FOUND
        )
        raise HTTPException(status_code=code, detail=exception.safe_message) from None
    loaded = _load_run(db, run.id)
    if loaded is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return _response(loaded)


@router.get("/question-runs/{run_id}", response_model=QuestionRunResponse)
def get_question_run(
    run_id: uuid.UUID,
    auth: CurrentAuth,
    db: Annotated[Session, Depends(get_db)],
) -> QuestionRunResponse:
    run = _load_run(db, run_id)
    if run is None or (run.user_id != auth.user.id and auth.user.role != "ADMIN"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return _response(run)


@router.get("/questions/history", response_model=list[QuestionRunResponse])
def get_question_history(
    auth: CurrentAuth, db: Annotated[Session, Depends(get_db)]
) -> list[QuestionRunResponse]:
    runs = db.scalars(
        select(QuestionRun)
        .options(
            selectinload(QuestionRun.materials),
            selectinload(QuestionRun.answer).selectinload(Answer.citations),
        )
        .where(QuestionRun.user_id == auth.user.id)
        .order_by(QuestionRun.created_at.desc())
    ).all()
    return [_response(run) for run in runs]


@router.post("/answers/{answer_id}/feedback", response_model=FeedbackResponse)
def create_or_update_feedback(
    answer_id: uuid.UUID,
    payload: FeedbackRequest,
    auth: CurrentAuth,
    db: Annotated[Session, Depends(get_db)],
) -> FeedbackResponse:
    answer = db.scalar(
        select(Answer)
        .join(QuestionRun, Answer.question_run_id == QuestionRun.id)
        .where(Answer.id == answer_id, QuestionRun.user_id == auth.user.id)
    )
    if answer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    feedback = db.scalar(
        select(AnswerFeedback).where(
            AnswerFeedback.answer_id == answer_id,
            AnswerFeedback.user_id == auth.user.id,
        )
    )
    if feedback is None:
        feedback = AnswerFeedback(answer_id=answer_id, user_id=auth.user.id, rating=payload.rating)
        db.add(feedback)
    feedback.rating = payload.rating
    feedback.comment = payload.comment
    db.commit()
    db.refresh(feedback)
    return FeedbackResponse(
        id=str(feedback.id),
        answer_id=str(feedback.answer_id),
        rating=feedback.rating,
        comment=feedback.comment,
    )
