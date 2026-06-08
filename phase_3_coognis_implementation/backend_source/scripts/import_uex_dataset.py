import argparse
import json
from pathlib import Path

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Expert, ExpertDomain, ExpertProfile, KnowledgeItem


def load_dataset(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Dataset root must be a JSON object.")

    for key in ("domains", "experts", "knowledge_items"):
        value = payload.get(key)
        if not isinstance(value, list):
            raise ValueError(f"Dataset field '{key}' must be a list.")

    return payload


def normalize_mbti(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip().upper()
    return normalized or None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import a prepared UEX dataset into experts, expert domains, expert profiles, and knowledge items."
    )
    parser.add_argument(
        "--path",
        default="docs/uex-dataset.json",
        help="Path to the dataset JSON file. Default: docs/uex-dataset.json",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist changes. Without this flag the script runs in dry-run mode.",
    )
    parser.add_argument(
        "--replace-knowledge",
        action="store_true",
        help="Replace existing expert-linked knowledge items for experts referenced in the dataset before importing.",
    )
    args = parser.parse_args()

    dataset_path = Path(args.path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

    dataset = load_dataset(dataset_path)
    domain_codes = {item["code"] for item in dataset["domains"] if isinstance(item, dict) and item.get("code")}

    db = SessionLocal()

    try:
        print(f"mode={'apply' if args.apply else 'dry-run'}")
        print(f"path={dataset_path}")
        print(f"domains={len(domain_codes)} experts={len(dataset['experts'])} knowledge_items={len(dataset['knowledge_items'])}")

        experts_by_email: dict[str, Expert] = {}
        created_experts = 0
        updated_experts = 0
        created_domains = 0
        created_profiles = 0
        updated_profiles = 0
        deleted_knowledge = 0
        created_knowledge = 0
        updated_knowledge = 0

        for item in dataset["experts"]:
            email = str(item["email"]).strip().lower()
            name = str(item["name"]).strip()
            is_active = bool(item.get("is_active", True))
            mbti = normalize_mbti(item.get("mbti"))
            requested_domain_codes = sorted(
                {
                    str(code).strip()
                    for code in item.get("domain_codes", [])
                    if str(code).strip()
                }
            )

            invalid_domain_codes = [code for code in requested_domain_codes if code not in domain_codes]
            if invalid_domain_codes:
                raise ValueError(f"Expert {email} references undefined domain codes: {invalid_domain_codes}")

            expert = db.execute(select(Expert).where(Expert.email == email)).scalar_one_or_none()
            action = "update"
            if expert is None:
                action = "create"
                expert = Expert(name=name, email=email, is_active=is_active)
                if args.apply:
                    db.add(expert)
                    db.flush()
                created_experts += 1
            else:
                expert.name = name
                expert.is_active = is_active
                updated_experts += 1

            print(
                {
                    "entity": "expert",
                    "action": action,
                    "email": email,
                    "name": name,
                    "domain_codes": requested_domain_codes,
                    "mbti": mbti,
                }
            )

            existing_domains = []
            if expert.id is not None:
                existing_domains = db.execute(
                    select(ExpertDomain).where(ExpertDomain.expert_id == expert.id)
                ).scalars().all()

            existing_domain_codes = {domain.domain_code for domain in existing_domains}
            missing_domain_codes = [code for code in requested_domain_codes if code not in existing_domain_codes]

            for domain_code in missing_domain_codes:
                print(
                    {
                        "entity": "expert_domain",
                        "action": "create",
                        "expert_email": email,
                        "domain_code": domain_code,
                    }
                )
                if args.apply:
                    db.add(ExpertDomain(expert_id=expert.id, domain_code=domain_code))
                created_domains += 1

            profile = None
            if expert.id is not None:
                profile = db.execute(
                    select(ExpertProfile).where(ExpertProfile.expert_id == expert.id)
                ).scalar_one_or_none()

            if profile is None:
                if args.apply:
                    profile = ExpertProfile(expert_id=expert.id)
                    db.add(profile)
                    db.flush()
                created_profiles += 1
                print(
                    {
                        "entity": "expert_profile",
                        "action": "create",
                        "expert_email": email,
                    }
                )

            if mbti:
                if profile is not None:
                    profile.manual_mbti = mbti
                    profile.effective_mbti = mbti
                updated_profiles += 1
                print(
                    {
                        "entity": "expert_profile",
                        "action": "set_mbti",
                        "expert_email": email,
                        "manual_mbti": mbti,
                    }
                )

            experts_by_email[email] = expert

        if args.apply:
            db.flush()

        if args.replace_knowledge:
            dataset_emails = set(experts_by_email.keys())
            for email in sorted(dataset_emails):
                expert = experts_by_email[email]
                if expert.id is None:
                    continue
                existing_items = db.execute(
                    select(KnowledgeItem).where(KnowledgeItem.source_expert_id == expert.id)
                ).scalars().all()
                for item in existing_items:
                    print(
                        {
                            "entity": "knowledge_item",
                            "action": "delete",
                            "expert_email": email,
                            "title": item.title,
                        }
                    )
                    if args.apply:
                        db.delete(item)
                    deleted_knowledge += 1

        for item in dataset["knowledge_items"]:
            title = str(item["title"]).strip()
            content = str(item["content"]).strip()
            domain_code = str(item["domain_code"]).strip()
            source_expert_email = str(item["source_expert_email"]).strip().lower()
            status = str(item.get("status", "published")).strip()

            if domain_code not in domain_codes:
                raise ValueError(f"Knowledge item '{title}' references undefined domain '{domain_code}'.")

            expert = experts_by_email.get(source_expert_email)
            if expert is None or expert.id is None:
                raise ValueError(f"Knowledge item '{title}' references unknown expert email '{source_expert_email}'.")

            existing_item = None
            if not args.replace_knowledge:
                existing_item = db.execute(
                    select(KnowledgeItem).where(
                        KnowledgeItem.source_expert_id == expert.id,
                        KnowledgeItem.title == title,
                    )
                ).scalar_one_or_none()

            action = "update" if existing_item is not None else "create"
            print(
                {
                    "entity": "knowledge_item",
                    "action": action,
                    "expert_email": source_expert_email,
                    "title": title,
                    "domain_code": domain_code,
                    "status": status,
                }
            )

            if existing_item is None:
                if args.apply:
                    db.add(
                        KnowledgeItem(
                            title=title,
                            content=content,
                            domain_code=domain_code,
                            status=status,
                            source_expert_id=expert.id,
                        )
                    )
                created_knowledge += 1
            else:
                existing_item.content = content
                existing_item.domain_code = domain_code
                existing_item.status = status
                updated_knowledge += 1

        if args.apply:
            db.commit()

        print(
            {
                "created_experts": created_experts,
                "updated_experts": updated_experts,
                "created_domains": created_domains,
                "created_profiles": created_profiles,
                "updated_profiles": updated_profiles,
                "deleted_knowledge": deleted_knowledge,
                "created_knowledge": created_knowledge,
                "updated_knowledge": updated_knowledge,
                "applied": args.apply,
            }
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
