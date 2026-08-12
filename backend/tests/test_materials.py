from fastapi.testclient import TestClient

from app.seed import DEMO_PASSWORD

MEMBER_ID = "20000000-0000-4000-8000-000000000001"
PREMIUM_ID = "20000000-0000-4000-8000-000000000002"
INACTIVE_ID = "20000000-0000-4000-8000-000000000003"


def auth_headers(client: TestClient, email: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": DEMO_PASSWORD})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_material_list_role_matrix_and_inactive_exclusion(client: TestClient) -> None:
    member = client.get("/api/v1/materials", headers=auth_headers(client, "member@example.com"))
    premium = client.get("/api/v1/materials", headers=auth_headers(client, "premium@example.com"))
    admin = client.get("/api/v1/materials", headers=auth_headers(client, "admin@example.com"))

    assert [item["required_role"] for item in member.json()] == ["MEMBER"]
    assert {item["required_role"] for item in premium.json()} == {"MEMBER", "PREMIUM"}
    assert len(admin.json()) == 2
    assert all(item["is_active"] for item in member.json() + premium.json() + admin.json())


def test_material_list_and_detail_require_auth_and_role(client: TestClient) -> None:
    assert client.get("/api/v1/materials").status_code == 401
    assert client.get(f"/api/v1/materials/{MEMBER_ID}").status_code == 401

    member_headers = auth_headers(client, "member@example.com")
    assert client.get(f"/api/v1/materials/{MEMBER_ID}", headers=member_headers).status_code == 200
    assert client.get(f"/api/v1/materials/{PREMIUM_ID}", headers=member_headers).status_code == 403
    assert client.get(f"/api/v1/materials/{INACTIVE_ID}", headers=member_headers).status_code == 404
    assert (
        client.get(
            "/api/v1/materials/99999999-0000-4000-8000-000000000999",
            headers=member_headers,
        ).status_code
        == 404
    )


def test_admin_status_lists_all_local_fixtures_and_rejects_non_admin(
    client: TestClient,
) -> None:
    member = client.get(
        "/api/v1/admin/materials", headers=auth_headers(client, "member@example.com")
    )
    admin = client.get("/api/v1/admin/materials", headers=auth_headers(client, "admin@example.com"))
    assert member.status_code == 403
    assert admin.status_code == 200
    assert len(admin.json()) == 3
    assert {item["transcript_status"] for item in admin.json()} == {"NOT_IMPORTED"}
    assert any(not item["is_active"] for item in admin.json())
    assert all(item["video_path"].startswith("/media/") for item in admin.json())
    assert all("http" not in item["video_path"] for item in admin.json())
