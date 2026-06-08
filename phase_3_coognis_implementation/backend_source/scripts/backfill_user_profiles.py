import argparse

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import SynapseInferenceRun, User, UserProfile
from app.services.user_profile import UserProfileService


def parse_args():
    parser = argparse.ArgumentParser(
        description="Backfill user_profiles from the latest stored SYNAPSE user inference runs."
    )
    parser.add_argument(
        "--overwrite-inferred",
        action="store_true",
        help="Overwrite existing inferred profile fields from the latest SYNAPSE run.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    db = SessionLocal()

    try:
        profile_service = UserProfileService(db)
        users = db.execute(select(User).order_by(User.id.asc())).scalars().all()

        created_count = 0
        updated_count = 0
        skipped_count = 0

        print(f"users={len(users)}")

        for user in users:
            latest_run = (
                db.execute(
                    select(SynapseInferenceRun)
                    .where(SynapseInferenceRun.subject_type == "user")
                    .where(SynapseInferenceRun.subject_id == user.id)
                    .order_by(SynapseInferenceRun.created_at.desc(), SynapseInferenceRun.id.desc())
                    .limit(1)
                )
                .scalars()
                .first()
            )

            if latest_run is None:
                skipped_count += 1
                print(
                    {
                        "user_id": user.id,
                        "email": user.email,
                        "status": "skipped_no_run",
                    }
                )
                continue

            profile = db.execute(
                select(UserProfile).where(UserProfile.user_id == user.id).limit(1)
            ).scalar_one_or_none()

            if profile is None:
                profile = profile_service.get_or_create_profile(user.id)
                created_count += 1
                profile_created = True
            else:
                profile_created = False

            has_existing_inferred = bool(profile.inferred_mbti or profile.effective_mbti)
            should_backfill = args.overwrite_inferred or not has_existing_inferred

            if not should_backfill:
                skipped_count += 1
                print(
                    {
                        "user_id": user.id,
                        "email": user.email,
                        "status": "skipped_existing_profile",
                        "manual_mbti": profile.manual_mbti,
                        "inferred_mbti": profile.inferred_mbti,
                        "effective_mbti": profile.effective_mbti,
                    }
                )
                continue

            accumulated_text = profile_service._append_text("", latest_run.content)
            profile.inferred_mbti = latest_run.mbti_type
            profile.confidence = latest_run.confidence
            profile.accumulated_chat_text = accumulated_text
            profile.last_inference_text_length = len(accumulated_text)
            profile.last_inferred_at = latest_run.created_at
            profile.effective_mbti = profile.manual_mbti or latest_run.mbti_type

            db.commit()
            db.refresh(profile)

            if not profile_created:
                updated_count += 1

            print(
                {
                    "user_id": user.id,
                    "email": user.email,
                    "status": "backfilled" if profile_created else "updated",
                    "manual_mbti": profile.manual_mbti,
                    "inferred_mbti": profile.inferred_mbti,
                    "effective_mbti": profile.effective_mbti,
                    "confidence": profile.confidence,
                    "run_id": latest_run.id,
                }
            )

        print(
            {
                "created_profiles": created_count,
                "updated_profiles": updated_count,
                "skipped": skipped_count,
            }
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
