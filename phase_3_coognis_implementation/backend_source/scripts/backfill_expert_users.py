from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import User
from app.services.admin import AdminService


def main() -> None:
    db = SessionLocal()

    try:
        service = AdminService(db)
        expert_users = db.execute(select(User).where(User.role == "expert").order_by(User.id.asc())).scalars().all()

        print(f"expert_users={len(expert_users)}")

        for user in expert_users:
            service._sync_expert_record_for_user(user)
            print(
                {
                    "user_id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "is_active": user.is_active,
                    "status": "synced",
                }
            )
    finally:
        db.close()


if __name__ == "__main__":
    main()
