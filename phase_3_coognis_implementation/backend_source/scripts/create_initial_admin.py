import argparse

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import User
from app.schemas.admin import UserCreateRequest
from app.services.admin import AdminService


def parse_args():
    parser = argparse.ArgumentParser(description="Create or update the initial SYNEXIS admin account.")
    parser.add_argument("--email", required=True, help="Admin email address.")
    parser.add_argument("--password", required=True, help="Admin password.")
    parser.add_argument("--first-name", default="Admin", help="Admin first name.")
    parser.add_argument("--last-name", default="User", help="Admin last name.")
    return parser.parse_args()


def main():
    args = parse_args()
    db = SessionLocal()

    try:
        existing = db.execute(select(User).where(User.email == args.email.lower())).scalar_one_or_none()

        if existing is None:
            response = AdminService(db).create_user(
                payload=UserCreateRequest(
                    first_name=args.first_name,
                    last_name=args.last_name,
                    email=args.email.lower(),
                    role="admin",
                    is_active=True,
                    temporary_password=args.password,
                    auto_generate_password=False,
                    ai_profiling_consent_recorded=True,
                    gdpr_consent_recorded=True,
                    send_credentials_email=False,
                )
            )
            print(f"Created admin account: {response.email}")
            print("2FA is enabled by default for admin accounts.")
            return

        existing.name = f"{args.first_name} {args.last_name}".strip()
        existing.first_name = args.first_name.strip()
        existing.last_name = args.last_name.strip()
        existing.role = "admin"
        existing.is_active = True
        existing.registration_status = "approved"
        existing.two_factor_enabled = True
        existing.ai_profiling_consent = True
        existing.gdpr_consent = True
        existing.password_hash = AdminService(db)._hash_password(args.password)
        db.commit()
        print(f"Updated existing admin account: {existing.email}")
        print("2FA remains enabled. Use AUTH_MOCK_2FA_CODE for local verification.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
