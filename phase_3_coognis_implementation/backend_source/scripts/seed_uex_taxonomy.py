import argparse
from dataclasses import dataclass

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Expert, ExpertDomain, KnowledgeItem


@dataclass(frozen=True)
class DomainDefinition:
    code: str
    label: str
    keywords: tuple[str, ...]
    sample_title: str
    sample_content: str


DOMAIN_TAXONOMY: tuple[DomainDefinition, ...] = (
    DomainDefinition(
        code="adaptive-systems",
        label="Adaptive Systems",
        keywords=("adaptive", "adaptation", "personalization", "profile"),
        sample_title="Adaptive guidance baseline",
        sample_content=(
            "Adaptive systems should adjust guidance using user profile signals, recent interaction history, "
            "and explicit consent boundaries. Recommendations should stay transparent and traceable."
        ),
    ),
    DomainDefinition(
        code="expert-guidance",
        label="Expert Guidance",
        keywords=("expert", "consult", "advisor", "specialist", "guidance"),
        sample_title="Expert follow-up workflow",
        sample_content=(
            "Expert guidance should extend the system response with human review, explicit reasoning, "
            "and a clear next-step recommendation when the automated answer is not sufficient."
        ),
    ),
    DomainDefinition(
        code="ml-modeling",
        label="ML Modeling",
        keywords=("model", "ml", "machine", "learning", "prediction", "classification"),
        sample_title="Modeling review checklist",
        sample_content=(
            "Modeling guidance should cover feature quality, validation discipline, calibration, "
            "and whether the selected model is appropriate for the expected decision context."
        ),
    ),
    DomainDefinition(
        code="ethics-gdpr",
        label="Ethics and GDPR",
        keywords=("gdpr", "privacy", "consent", "ethic", "deletion", "profiling"),
        sample_title="Privacy and consent handling",
        sample_content=(
            "Privacy-sensitive workflows must record consent explicitly, support profiling opt-out, "
            "and provide a clear path for deletion and audit of personal-data actions."
        ),
    ),
    DomainDefinition(
        code="education-guidance",
        label="Education Guidance",
        keywords=("education", "learning", "student", "course", "training", "teaching"),
        sample_title="Learning pathway recommendation",
        sample_content=(
            "Education-oriented recommendations should balance learner context, progress, and motivation, "
            "while keeping the next action concrete and easy to follow."
        ),
    ),
)

DEFAULT_DOMAIN_CODE = "expert-guidance"


def normalize_text(*parts: str | None) -> str:
    return " ".join(part.strip().lower() for part in parts if part and part.strip())


def infer_domain_codes_for_expert(expert: Expert, existing_item_codes: set[str]) -> list[str]:
    if existing_item_codes:
        return sorted(existing_item_codes)

    text = normalize_text(expert.name, expert.email)
    matched_codes: list[str] = []

    for definition in DOMAIN_TAXONOMY:
        if any(keyword in text for keyword in definition.keywords):
            matched_codes.append(definition.code)

    if not matched_codes:
        matched_codes.append(DEFAULT_DOMAIN_CODE)

    return sorted(set(matched_codes))


def find_definition(domain_code: str) -> DomainDefinition:
    for definition in DOMAIN_TAXONOMY:
        if definition.code == domain_code:
            return definition
    for definition in DOMAIN_TAXONOMY:
        if definition.code == DEFAULT_DOMAIN_CODE:
            return definition
    return DOMAIN_TAXONOMY[0]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Backfill expert domains and optionally seed starter UEX knowledge items."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist the suggested changes. Without this flag the script runs in dry-run mode.",
    )
    parser.add_argument(
        "--seed-knowledge",
        action="store_true",
        help="Create one published starter knowledge item for experts who currently have no knowledge items.",
    )
    args = parser.parse_args()

    db = SessionLocal()

    try:
        experts = db.execute(
            select(Expert).order_by(Expert.id.asc())
        ).scalars().all()

        print(f"mode={'apply' if args.apply else 'dry-run'}")
        print(f"experts={len(experts)}")
        print("taxonomy=" + ", ".join(definition.code for definition in DOMAIN_TAXONOMY))

        created_domains = 0
        created_knowledge_items = 0

        for expert in experts:
            existing_domains = {
                row.domain_code
                for row in db.execute(
                    select(ExpertDomain).where(ExpertDomain.expert_id == expert.id)
                ).scalars().all()
            }
            knowledge_items = db.execute(
                select(KnowledgeItem).where(KnowledgeItem.source_expert_id == expert.id)
            ).scalars().all()
            knowledge_domain_codes = {
                item.domain_code for item in knowledge_items if item.domain_code
            }

            target_domains = infer_domain_codes_for_expert(expert, knowledge_domain_codes)
            missing_domains = [code for code in target_domains if code not in existing_domains]

            for domain_code in missing_domains:
                print(
                    {
                        "expert_id": expert.id,
                        "expert_name": expert.name,
                        "action": "add_domain",
                        "domain_code": domain_code,
                    }
                )
                if args.apply:
                    db.add(ExpertDomain(expert_id=expert.id, domain_code=domain_code))
                    created_domains += 1

            if args.seed_knowledge and not knowledge_items:
                seed_domain_code = target_domains[0] if target_domains else DEFAULT_DOMAIN_CODE
                definition = find_definition(seed_domain_code)
                print(
                    {
                        "expert_id": expert.id,
                        "expert_name": expert.name,
                        "action": "seed_knowledge",
                        "domain_code": seed_domain_code,
                        "title": definition.sample_title,
                    }
                )
                if args.apply:
                    db.add(
                        KnowledgeItem(
                            title=definition.sample_title,
                            content=definition.sample_content,
                            domain_code=seed_domain_code,
                            status="published",
                            source_expert_id=expert.id,
                        )
                    )
                    created_knowledge_items += 1

        if args.apply:
            db.commit()

        print(
            {
                "created_domains": created_domains,
                "created_knowledge_items": created_knowledge_items,
                "applied": args.apply,
            }
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
