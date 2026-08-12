import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.application.retrieval import search_chunks
from app.application.transcripts import MEMBER_MATERIAL_ID, PREMIUM_MATERIAL_ID, import_transcript
from app.db.models import (
    ChunkEmbedding,
    Material,
    TranscriptChunk,
    TranscriptSegment,
    TranscriptVersion,
    User,
)
from app.db.session import get_session_factory
from app.providers.base import EmbeddingMetadata
from app.providers.deterministic_embedding import DeterministicEmbeddingProvider
from app.seed import DEMO_PASSWORD


def auth_headers(client: TestClient, email: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": DEMO_PASSWORD})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def import_url(material_id: uuid.UUID) -> str:
    return f"/api/v1/admin/materials/{material_id}/transcript-imports"


def test_admin_imports_ready_transcript_with_pgvector_and_metadata(client: TestClient) -> None:
    headers = auth_headers(client, "admin@example.com")
    response = client.post(
        import_url(MEMBER_MATERIAL_ID),
        headers=headers,
        json={"fixture_id": "hair-cut-basic-v1"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "READY"
    assert payload["is_current"] is True
    assert payload["segment_count"] == 5
    assert payload["chunk_count"] == 2
    assert payload["embedding_count"] == 2
    assert payload["provider_name"] == "deterministic-local"
    assert payload["provider_version"] == "hash-char-ngram-v1"
    assert payload["dimensions"] == 32

    with get_session_factory()() as db:
        original = db.scalar(
            select(TranscriptSegment.original_text).order_by(TranscriptSegment.sequence)
        )
        vector = db.scalar(select(ChunkEmbedding.embedding))
        assert original == "  シャンプー前に\t髪の状態を確認します。  "
        assert vector is not None and len(vector) == 32


def test_invalid_fixture_fails_without_partial_content(client: TestClient) -> None:
    headers = auth_headers(client, "admin@example.com")
    response = client.post(
        import_url(MEMBER_MATERIAL_ID),
        headers=headers,
        json={"fixture_id": "invalid-sequence-v1"},
    )
    assert response.status_code == 422
    with get_session_factory()() as db:
        failed = db.scalar(select(TranscriptVersion))
        assert failed is not None
        assert failed.status == "FAILED"
        assert failed.failure_code == "INVALID_TRANSCRIPT"
        assert db.scalar(select(func.count()).select_from(TranscriptSegment)) == 0
        assert db.scalar(select(func.count()).select_from(TranscriptChunk)) == 0
        assert db.scalar(select(func.count()).select_from(ChunkEmbedding)) == 0


def test_fixture_material_mismatch_and_non_admin_are_rejected(client: TestClient) -> None:
    admin_headers = auth_headers(client, "admin@example.com")
    mismatch = client.post(
        import_url(PREMIUM_MATERIAL_ID),
        headers=admin_headers,
        json={"fixture_id": "hair-cut-basic-v1"},
    )
    assert mismatch.status_code == 422
    for email in ("member@example.com", "premium@example.com"):
        forbidden = client.post(
            import_url(MEMBER_MATERIAL_ID),
            headers=auth_headers(client, email),
            json={"fixture_id": "hair-cut-basic-v1"},
        )
        assert forbidden.status_code == 403


def test_reimport_keeps_old_version_and_moves_current(client: TestClient) -> None:
    headers = auth_headers(client, "admin@example.com")
    first = client.post(
        import_url(MEMBER_MATERIAL_ID),
        headers=headers,
        json={"fixture_id": "hair-cut-basic-v1"},
    ).json()
    second = client.post(
        import_url(MEMBER_MATERIAL_ID),
        headers=headers,
        json={"fixture_id": "hair-cut-basic-v1"},
    ).json()
    assert first["id"] != second["id"]
    assert (first["version"], second["version"]) == (1, 2)

    versions = client.get(
        f"/api/v1/admin/materials/{MEMBER_MATERIAL_ID}/transcript-versions",
        headers=headers,
    ).json()
    assert [item["version"] for item in versions] == [2, 1]
    assert [item["is_current"] for item in versions] == [True, False]
    assert versions[1]["segment_count"] == 5


class ExplodingProvider:
    @property
    def metadata(self) -> EmbeddingMetadata:
        return EmbeddingMetadata("exploding-local", "failure-v1", 32)

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        del texts
        raise RuntimeError("sensitive internal failure")


def test_failed_reimport_preserves_old_current_and_safe_failure() -> None:
    with get_session_factory()() as db:
        admin = db.scalar(select(User).where(User.role == "ADMIN"))
        assert admin is not None
        ready = import_transcript(
            db,
            MEMBER_MATERIAL_ID,
            "hair-cut-basic-v1",
            admin.id,
            DeterministicEmbeddingProvider(),
        )
        try:
            import_transcript(
                db,
                MEMBER_MATERIAL_ID,
                "hair-cut-basic-v1",
                admin.id,
                ExplodingProvider(),
            )
        except Exception as exception:
            assert str(exception) == "Transcript import failed."
        versions = db.scalars(select(TranscriptVersion).order_by(TranscriptVersion.version)).all()
        assert versions[0].id == ready.id and versions[0].is_current
        assert versions[1].status == "FAILED" and not versions[1].is_current
        assert versions[1].failure_message == "Transcript import failed."
        assert "sensitive" not in versions[1].failure_message
        assert db.scalar(select(func.count()).select_from(TranscriptSegment)) == 5
        material = db.get(Material, MEMBER_MATERIAL_ID)
        assert material is not None and material.transcript_status == "READY"


def test_retrieval_uses_only_current_ready_and_role_access() -> None:
    provider = DeterministicEmbeddingProvider()
    with get_session_factory()() as db:
        admin = db.scalar(select(User).where(User.role == "ADMIN"))
        assert admin is not None
        import_transcript(db, MEMBER_MATERIAL_ID, "hair-cut-basic-v1", admin.id, provider)
        import_transcript(
            db,
            PREMIUM_MATERIAL_ID,
            "hair-consultation-premium-v1",
            admin.id,
            provider,
        )
        member_results = search_chunks(db, "カウンセリング", "MEMBER", provider)
        premium_results = search_chunks(db, "カウンセリング", "PREMIUM", provider)
        assert member_results
        assert {item.material_id for item in member_results} == {MEMBER_MATERIAL_ID}
        assert {item.material_id for item in premium_results} == {
            MEMBER_MATERIAL_ID,
            PREMIUM_MATERIAL_ID,
        }
        assert (
            search_chunks(
                db,
                "カウンセリング",
                "MEMBER",
                provider,
                material_ids=[PREMIUM_MATERIAL_ID],
            )
            == []
        )


def test_admin_material_summary_and_version_detail(client: TestClient) -> None:
    headers = auth_headers(client, "admin@example.com")
    imported = client.post(
        import_url(MEMBER_MATERIAL_ID),
        headers=headers,
        json={"fixture_id": "hair-cut-basic-v1"},
    ).json()
    materials = client.get("/api/v1/admin/materials", headers=headers).json()
    target = next(item for item in materials if item["id"] == str(MEMBER_MATERIAL_ID))
    assert target["transcript_status"] == "READY"
    assert target["current_version"] == 1
    assert (target["segment_count"], target["chunk_count"], target["embedding_count"]) == (
        5,
        2,
        2,
    )
    detail = client.get(f"/api/v1/admin/transcript-versions/{imported['id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["provider_name"] == "deterministic-local"


def test_internal_import_error_is_not_exposed(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def explode(_provider: object, _texts: object) -> list[list[float]]:
        raise RuntimeError("sensitive filesystem detail")

    monkeypatch.setattr(DeterministicEmbeddingProvider, "embed_many", explode)
    response = client.post(
        import_url(MEMBER_MATERIAL_ID),
        headers=auth_headers(client, "admin@example.com"),
        json={"fixture_id": "hair-cut-basic-v1"},
    )
    assert response.status_code == 422
    assert "sensitive" not in response.text
    with get_session_factory()() as db:
        version = db.scalar(select(TranscriptVersion))
        assert version is not None
        assert version.status == "FAILED"
        assert version.failure_code == "IMPORT_FAILED"
