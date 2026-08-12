import uuid

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.api.routes.questions import get_answer_provider, get_embedding_provider
from app.application.questions import (
    COSINE_DISTANCE_THRESHOLD,
    LEXICAL_OVERLAP_THRESHOLD,
    QuestionProcessingError,
    decide_evidence,
    lexical_overlap_ratio,
    process_question,
)
from app.application.retrieval import RetrievedChunk
from app.application.transcripts import MEMBER_MATERIAL_ID, import_transcript
from app.db.models import (
    Answer,
    AnswerCitation,
    Material,
    RetrievalResult,
    RetrievalRun,
    TranscriptVersion,
    User,
)
from app.db.session import get_session_factory
from app.main import create_app
from app.providers.base import EmbeddingMetadata, EvidenceInput, GeneratedAnswer
from app.providers.deterministic_embedding import DeterministicEmbeddingProvider
from app.providers.grounded_answer import GroundedExtractiveAnswerProvider
from app.seed import DEMO_PASSWORD


def auth_headers(client: TestClient, email: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": DEMO_PASSWORD})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def prepare_member_transcript() -> None:
    with get_session_factory()() as db:
        admin = db.scalar(select(User).where(User.role == "ADMIN"))
        assert admin is not None
        import_transcript(
            db,
            MEMBER_MATERIAL_ID,
            "hair-cut-basic-v1",
            admin.id,
            DeterministicEmbeddingProvider(),
        )


def ask(client: TestClient, question: str, email: str = "premium@example.com"):
    return client.post(
        "/api/v1/question-runs",
        headers=auth_headers(client, email),
        json={"question": question, "material_ids": [str(MEMBER_MATERIAL_ID)]},
    )


def test_answerable_question_saves_rank_distance_grounded_answer_and_snapshots(
    client: TestClient,
) -> None:
    prepare_member_transcript()
    response = ask(client, "シャンプー前に何を確認しますか？")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "COMPLETED"
    assert payload["answer"]["provider_name"] == "deterministic-local"
    assert payload["answer"]["provider_version"] == "grounded-extractive-v1"
    assert payload["answer"]["citations"]
    citation = payload["answer"]["citations"][0]
    assert citation["video_path"] == "/media/demo-hair-technique.mp4"
    assert citation["start_ms"] == 0
    assert citation["text_snapshot"] in payload["answer"]["body"]

    with get_session_factory()() as db:
        retrieval = db.scalar(select(RetrievalRun))
        results = db.scalars(select(RetrievalResult).order_by(RetrievalResult.rank)).all()
        stored = db.scalar(select(AnswerCitation))
        assert retrieval is not None
        assert retrieval.provider_version == "hash-char-ngram-v1"
        assert retrieval.dimensions == 32 and retrieval.top_k == 5
        assert retrieval.policy_version == "evidence-policy-v1"
        assert retrieval.lexical_overlap_threshold == LEXICAL_OVERLAP_THRESHOLD
        assert retrieval.cosine_distance_threshold == COSINE_DISTANCE_THRESHOLD
        assert [result.rank for result in results] == list(range(1, len(results) + 1))
        assert all(result.distance >= 0 for result in results)
        assert stored is not None and stored.text_snapshot == citation["text_snapshot"]


class CountingProvider:
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, question: str, evidence: list[EvidenceInput]) -> GeneratedAnswer:
        self.calls += 1
        return GroundedExtractiveAnswerProvider().generate(question, evidence)


def test_insufficient_and_out_of_scope_do_not_call_generator() -> None:
    prepare_member_transcript()
    with get_session_factory()() as db:
        premium = db.scalar(select(User).where(User.role == "PREMIUM"))
        assert premium is not None
        generator = CountingProvider()
        insufficient = process_question(
            db,
            premium.id,
            premium.role,
            "髪を洗う方法は？",
            [MEMBER_MATERIAL_ID],
            DeterministicEmbeddingProvider(),
            generator,
        )
        outside = process_question(
            db,
            premium.id,
            premium.role,
            "料理の作り方は？",
            [MEMBER_MATERIAL_ID],
            DeterministicEmbeddingProvider(),
            generator,
        )
        assert insufficient.status == "REFUSED_INSUFFICIENT_EVIDENCE"
        assert outside.status == "REFUSED_OUT_OF_SCOPE"
        assert generator.calls == 0
        assert db.scalar(select(func.count()).select_from(Answer)) == 0


def test_policy_boundary_values() -> None:
    chunks = [
        RetrievedChunk(uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), "/media/x.mp4", "ab", 0, 1, 0.55)
    ]
    assert lexical_overlap_ratio("abcde", "ab") == 0.25
    assert decide_evidence("abcde", chunks).status == "COMPLETED"
    farther = [
        RetrievedChunk(
            uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), "/media/x.mp4", "ab", 0, 1, 0.55001
        )
    ]
    assert decide_evidence("abcde", farther).status == "REFUSED_INSUFFICIENT_EVIDENCE"


def test_grounded_answer_provider_is_deterministic_and_uses_only_supplied_evidence() -> None:
    provider = GroundedExtractiveAnswerProvider()
    evidence = [
        EvidenceInput("citation-1", "提供された根拠だけを回答に使います。"),
        EvidenceInput("citation-2", "一般知識は補いません。"),
    ]
    first = provider.generate("質問", evidence)
    second = provider.generate("質問", evidence)
    assert first == second
    assert first.citation_ids == ("citation-1", "citation-2")
    assert first.body == "提供された根拠だけを回答に使います。\n一般知識は補いません。"


def test_member_and_material_access_are_rejected(client: TestClient) -> None:
    member = ask(client, "シャンプー前に何を確認しますか？", "member@example.com")
    assert member.status_code == 403
    with get_session_factory()() as db:
        member_user = db.scalar(select(User).where(User.role == "MEMBER"))
        assert member_user is not None
        premium_material = db.scalar(select(Material).where(Material.required_role == "PREMIUM"))
        assert premium_material is not None
        try:
            process_question(
                db,
                member_user.id,
                member_user.role,
                "質問",
                [premium_material.id],
                DeterministicEmbeddingProvider(),
                GroundedExtractiveAnswerProvider(),
            )
        except QuestionProcessingError as exception:
            assert exception.code == "MATERIAL_FORBIDDEN"
        else:
            raise AssertionError("inaccessible material was accepted")


class InvalidCitationProvider:
    def generate(self, question: str, evidence: list[EvidenceInput]) -> GeneratedAnswer:
        del question, evidence
        return GeneratedAnswer(
            body="invalid",
            citation_ids=("not-allowed",),
            provider_name="test",
            provider_version="bad",
        )


class MismatchedEmbeddingProvider(DeterministicEmbeddingProvider):
    @property
    def metadata(self) -> EmbeddingMetadata:
        return EmbeddingMetadata("deterministic-local", "wrong-version", 32)


def test_invalid_citation_and_embedding_mismatch_finish_failed() -> None:
    prepare_member_transcript()
    app = create_app()
    app.dependency_overrides[get_answer_provider] = InvalidCitationProvider
    with TestClient(app) as client:
        invalid = ask(client, "シャンプー前に何を確認しますか？")
        assert invalid.json()["status"] == "FAILED"
        assert invalid.json()["failure_code"] == "INVALID_PROVIDER_CITATION"
    app.dependency_overrides.clear()

    app = create_app()
    app.dependency_overrides[get_embedding_provider] = MismatchedEmbeddingProvider
    with TestClient(app) as client:
        mismatch = ask(client, "シャンプー前に何を確認しますか？")
        assert mismatch.json()["status"] == "FAILED"
        assert mismatch.json()["failure_code"] == "EMBEDDING_METADATA_MISMATCH"
    with get_session_factory()() as db:
        assert db.scalar(select(func.count()).select_from(Answer)) == 0


class ExplodingAnswerProvider:
    def generate(self, question: str, evidence: list[EvidenceInput]) -> GeneratedAnswer:
        del question, evidence
        raise RuntimeError("internal sensitive error")


def test_transaction_exception_rolls_back_retrieval_and_answer() -> None:
    prepare_member_transcript()
    with get_session_factory()() as db:
        premium = db.scalar(select(User).where(User.role == "PREMIUM"))
        assert premium is not None
        run = process_question(
            db,
            premium.id,
            premium.role,
            "シャンプー前に何を確認しますか？",
            [MEMBER_MATERIAL_ID],
            DeterministicEmbeddingProvider(),
            ExplodingAnswerProvider(),
        )
        assert run.status == "FAILED"
        assert run.failure_code == "QUESTION_PROCESSING_FAILED"
        assert db.scalar(select(func.count()).select_from(RetrievalRun)) == 0
        assert db.scalar(select(func.count()).select_from(Answer)) == 0


def test_old_citation_snapshot_survives_new_transcript_version(client: TestClient) -> None:
    prepare_member_transcript()
    response = ask(client, "シャンプー前に何を確認しますか？").json()
    citation = response["answer"]["citations"][0]
    old_version_id = citation["transcript_version_id"]
    with get_session_factory()() as db:
        admin = db.scalar(select(User).where(User.role == "ADMIN"))
        assert admin is not None
        import_transcript(
            db,
            MEMBER_MATERIAL_ID,
            "hair-cut-basic-v1",
            admin.id,
            DeterministicEmbeddingProvider(),
        )
        old_version = db.get(TranscriptVersion, uuid.UUID(old_version_id))
        stored = db.scalar(select(AnswerCitation))
        assert old_version is not None and not old_version.is_current
        assert stored is not None and stored.text_snapshot == citation["text_snapshot"]


def test_history_is_user_scoped_and_feedback_checks_ownership(client: TestClient) -> None:
    prepare_member_transcript()
    created = ask(client, "シャンプー前に何を確認しますか？").json()
    premium_headers = auth_headers(client, "premium@example.com")
    premium_history = client.get("/api/v1/questions/history", headers=premium_headers)
    admin_headers = auth_headers(client, "admin@example.com")
    admin_history = client.get("/api/v1/questions/history", headers=admin_headers)
    assert [item["run_id"] for item in premium_history.json()] == [created["run_id"]]
    assert admin_history.json() == []

    answer_id = created["answer"]["id"]
    feedback = client.post(
        f"/api/v1/answers/{answer_id}/feedback",
        headers=premium_headers,
        json={"rating": "UP", "comment": "根拠を確認できました"},
    )
    forbidden = client.post(
        f"/api/v1/answers/{answer_id}/feedback",
        headers=admin_headers,
        json={"rating": "DOWN"},
    )
    assert feedback.status_code == 200 and feedback.json()["rating"] == "UP"
    assert forbidden.status_code == 404


def test_question_request_constraints(client: TestClient) -> None:
    headers = auth_headers(client, "premium@example.com")
    duplicate = client.post(
        "/api/v1/question-runs",
        headers=headers,
        json={
            "question": "質問",
            "material_ids": [str(MEMBER_MATERIAL_ID), str(MEMBER_MATERIAL_ID)],
        },
    )
    blank = client.post(
        "/api/v1/question-runs",
        headers=headers,
        json={"question": "   ", "material_ids": [str(MEMBER_MATERIAL_ID)]},
    )
    assert duplicate.status_code == 422
    assert blank.status_code == 422
