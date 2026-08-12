import uuid

from sqlalchemy.orm import Session

from app.db.models import Material, User
from app.db.session import get_session_factory
from app.security import hash_password

DEMO_PASSWORD = "Learning123!"
DEMO_PASSWORD_HASH = hash_password(DEMO_PASSWORD)

USERS = (
    {
        "id": uuid.UUID("10000000-0000-4000-8000-000000000001"),
        "email": "member@example.com",
        "role": "MEMBER",
        "is_active": True,
    },
    {
        "id": uuid.UUID("10000000-0000-4000-8000-000000000002"),
        "email": "premium@example.com",
        "role": "PREMIUM",
        "is_active": True,
    },
    {
        "id": uuid.UUID("10000000-0000-4000-8000-000000000003"),
        "email": "admin@example.com",
        "role": "ADMIN",
        "is_active": True,
    },
    {
        "id": uuid.UUID("10000000-0000-4000-8000-000000000004"),
        "email": "inactive@example.com",
        "role": "MEMBER",
        "is_active": False,
    },
)

MATERIALS = (
    {
        "id": uuid.UUID("20000000-0000-4000-8000-000000000001"),
        "title": "シャンプーの基本",
        "description": "お客様への声掛けと基本的なシャンプー手順を学びます。",
        "required_role": "MEMBER",
        "video_path": "/media/demo-hair-technique.mp4",
        "duration_ms": 6000,
        "transcript_status": "NOT_IMPORTED",
        "is_active": True,
    },
    {
        "id": uuid.UUID("20000000-0000-4000-8000-000000000002"),
        "title": "応用カウンセリング",
        "description": "PREMIUM会員向けに施術前の要望整理を学びます。",
        "required_role": "PREMIUM",
        "video_path": "/media/demo-hair-technique.mp4",
        "duration_ms": 6000,
        "transcript_status": "NOT_IMPORTED",
        "is_active": True,
    },
    {
        "id": uuid.UUID("20000000-0000-4000-8000-000000000003"),
        "title": "公開準備中の教材",
        "description": "管理者だけが状態を確認する非公開教材です。",
        "required_role": "MEMBER",
        "video_path": "/media/demo-hair-technique.mp4",
        "duration_ms": 6000,
        "transcript_status": "NOT_IMPORTED",
        "is_active": False,
    },
)


def seed_database(db: Session) -> None:
    for data in USERS:
        user = db.get(User, data["id"])
        if user is None:
            db.add(User(password_hash=DEMO_PASSWORD_HASH, **data))
        else:
            user.email = data["email"]
            user.role = data["role"]
            user.is_active = data["is_active"]

    for data in MATERIALS:
        material = db.get(Material, data["id"])
        if material is None:
            db.add(Material(**data))
        else:
            for key, value in data.items():
                if key != "id":
                    setattr(material, key, value)
    db.commit()


def main() -> None:
    with get_session_factory()() as db:
        seed_database(db)
    print("Demo users and local materials are ready.")


if __name__ == "__main__":
    main()
