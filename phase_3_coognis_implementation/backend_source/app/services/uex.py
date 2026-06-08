import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Expert, ExpertDomain, ExpertProfile, KnowledgeItem, User
from app.schemas.uex import (
    ExpertAnalysisResponse,
    ExpertCreateRequest,
    ExpertMatchRequest,
    ExpertMatchResponse,
    ExpertMatchResult,
    ExpertResponse,
    KnowledgeItemCreateRequest,
    UexKnowledgeContextResponse,
    KnowledgeItemListResponse,
    KnowledgeItemResponse,
    KnowledgeItemUpdateRequest,
)
from app.services.synapse.inference import SynapseInferenceService
from app.services.vector_retrieval import VectorRetrievalDocument, VectorRetrievalService


class UexService:
    """Persistence service for the UEX module."""

    GENERIC_QUERY_TOKENS = {
        "what",
        "which",
        "when",
        "where",
        "would",
        "could",
        "should",
        "need",
        "help",
        "about",
        "with",
        "that",
        "this",
        "have",
        "your",
        "from",
        "into",
        "will",
        "them",
        "they",
        "user",
        "users",
        "student",
        "students",
        "university",
        "credential",
        "credentials",
        "portal",
        "service",
        "services",
        "system",
        "official",
    }

    def __init__(self, db: Session) -> None:
        self.db = db
        self.vector_retrieval_service = VectorRetrievalService()

    def create_expert(self, payload: ExpertCreateRequest) -> ExpertResponse:
        expert = Expert(
            name=payload.name,
            email=payload.email,
            is_active=payload.is_active,
        )
        self.db.add(expert)
        self.db.flush()

        for domain_code in sorted(set(payload.domain_codes)):
            self.db.add(ExpertDomain(expert_id=expert.id, domain_code=domain_code))

        self.db.commit()
        return self.get_expert(expert.id)

    def get_expert(self, expert_id: int) -> ExpertResponse:
        statement = (
            select(Expert)
            .options(selectinload(Expert.domains))
            .where(Expert.id == expert_id)
        )
        expert = self.db.execute(statement).scalar_one_or_none()
        if expert is None:
            raise LookupError("Expert not found.")

        return ExpertResponse(
            id=expert.id,
            name=expert.name,
            email=expert.email,
            is_active=expert.is_active,
            domain_codes=sorted(domain.domain_code for domain in expert.domains),
            platform_user_id=self._resolve_platform_user_id(expert),
            is_contactable=self._is_expert_contactable(expert),
            created_at=expert.created_at,
        )

    def analyze_expert(
        self,
        expert_id: int,
        synapse_inference_service: SynapseInferenceService,
    ) -> ExpertAnalysisResponse:
        statement = (
            select(Expert)
            .options(
                selectinload(Expert.knowledge_items),
                selectinload(Expert.profile),
            )
            .where(Expert.id == expert_id)
        )
        expert = self.db.execute(statement).scalar_one_or_none()
        if expert is None:
            raise LookupError("Expert not found.")

        knowledge_items = sorted(expert.knowledge_items, key=lambda item: item.id)
        if not knowledge_items:
            raise ValueError("Expert has no knowledge items to analyze.")

        raw_text = "\n\n".join(item.content.strip() for item in knowledge_items if item.content.strip())
        if not raw_text:
            raise ValueError("Expert knowledge items do not contain analyzable text.")

        inference_result = synapse_inference_service.infer(raw_text)
        profile = expert.profile
        if profile is None:
            profile = ExpertProfile(expert_id=expert.id)
            self.db.add(profile)

        profile.inferred_mbti = inference_result.mbti_type
        profile.confidence = inference_result.confidence
        profile.effective_mbti = profile.manual_mbti or inference_result.mbti_type

        self.db.commit()
        self.db.refresh(profile)

        return ExpertAnalysisResponse(
            expert_id=expert.id,
            manual_mbti=profile.manual_mbti,
            inferred_mbti=profile.inferred_mbti,
            effective_mbti=profile.effective_mbti,
            confidence=profile.confidence or 0.0,
            model_version=inference_result.model_version,
        )

    def match_experts(self, payload: ExpertMatchRequest) -> ExpertMatchResponse:
        statement = select(Expert).options(
            selectinload(Expert.domains),
            selectinload(Expert.profile),
        )
        experts = self.db.execute(statement).scalars().all()

        requested_domains = {domain.strip() for domain in payload.domain_codes if domain.strip()}
        requested_mbti = payload.target_mbti.upper() if payload.target_mbti else None

        results: list[ExpertMatchResult] = []
        for expert in experts:
            expert_domains = {domain.domain_code for domain in expert.domains}
            profile = expert.profile
            effective_mbti = profile.effective_mbti if profile else None
            platform_user_id = self._resolve_platform_user_id(expert)

            domain_similarity_score = self._compute_domain_similarity_score(
                requested_domains=requested_domains,
                expert_domains=expert_domains,
            )
            profile_compatibility_score = self._compute_profile_compatibility_score(
                requested_mbti=requested_mbti,
                expert_mbti=effective_mbti,
            )
            availability_score = 1.0 if expert.is_active else 0.25
            historical_satisfaction_score = (
                profile.confidence if profile and profile.confidence is not None else 0.5
            )

            total_score = round(
                (0.4 * domain_similarity_score)
                + (0.3 * profile_compatibility_score)
                + (0.2 * availability_score)
                + (0.1 * historical_satisfaction_score),
                4,
            )

            results.append(
                ExpertMatchResult(
                    expert_id=expert.id,
                    name=expert.name,
                    domain_codes=sorted(expert_domains),
                    effective_mbti=effective_mbti,
                    is_contactable=platform_user_id is not None,
                    domain_similarity_score=round(domain_similarity_score, 4),
                    profile_compatibility_score=round(profile_compatibility_score, 4),
                    availability_score=round(availability_score, 4),
                    historical_satisfaction_score=round(historical_satisfaction_score, 4),
                    total_score=total_score,
                )
            )

        results.sort(key=lambda item: (-item.total_score, item.expert_id))
        limited_results = results[: payload.limit]
        return ExpertMatchResponse(items=limited_results, total=len(results))

    def suggest_domain_codes_for_text(self, text: str, *, limit: int = 3) -> list[str]:
        normalized_tokens = self._tokenize_text(text)
        if not normalized_tokens:
            return []

        domain_scores: dict[str, float] = {}

        knowledge_items = self.db.execute(
            select(KnowledgeItem).where(KnowledgeItem.status == "published")
        ).scalars().all()

        for item in knowledge_items:
            item_tokens = self._tokenize_text(f"{item.domain_code} {item.title} {item.content}")
            overlap = normalized_tokens & item_tokens
            if not overlap:
                continue
            domain_scores[item.domain_code] = domain_scores.get(item.domain_code, 0.0) + float(len(overlap))

        expert_domains = self.db.execute(select(ExpertDomain.domain_code)).scalars().all()
        for domain_code in expert_domains:
            code_tokens = self._tokenize_text(domain_code.replace("-", " ").replace("_", " "))
            overlap = normalized_tokens & code_tokens
            if not overlap:
                continue
            domain_scores[domain_code] = domain_scores.get(domain_code, 0.0) + (0.5 * float(len(overlap)))

        ranked_domain_codes = sorted(
            domain_scores.items(),
            key=lambda item: (-item[1], item[0]),
        )
        if not ranked_domain_codes:
            return []

        top_score = ranked_domain_codes[0][1]
        threshold = max(1.0, top_score * 0.6)
        return [
            domain_code
            for domain_code, score in ranked_domain_codes
            if score >= threshold
        ][:limit]

    @staticmethod
    def _compute_domain_similarity_score(
        *,
        requested_domains: set[str],
        expert_domains: set[str],
    ) -> float:
        if not requested_domains:
            return 1.0
        if not expert_domains:
            return 0.0
        overlap = requested_domains & expert_domains
        return len(overlap) / len(requested_domains)

    @staticmethod
    def _compute_profile_compatibility_score(
        *,
        requested_mbti: str | None,
        expert_mbti: str | None,
    ) -> float:
        if not requested_mbti:
            return 1.0
        if not expert_mbti or len(expert_mbti) != 4:
            return 0.0
        matches = sum(
            1 for requested_char, expert_char in zip(requested_mbti, expert_mbti, strict=False)
            if requested_char == expert_char
        )
        return matches / 4

    @staticmethod
    def _tokenize_text(value: str) -> set[str]:
        normalized = VectorRetrievalService.normalize_text(value)
        return {
            token
            for token in re.findall(r"[a-z0-9]{3,}", normalized)
            if len(token) >= 3 and token not in UexService.GENERIC_QUERY_TOKENS
        }

    def _resolve_platform_user_id(self, expert: Expert) -> int | None:
        if not expert.email:
            return None

        return self.db.execute(
            select(User.id).where(
                User.email == expert.email.lower(),
                User.role == "expert",
                User.is_active.is_(True),
                User.registration_status == "approved",
            )
        ).scalar_one_or_none()

    def _is_expert_contactable(self, expert: Expert) -> bool:
        return self._resolve_platform_user_id(expert) is not None

    def create_knowledge_item(
        self,
        payload: KnowledgeItemCreateRequest,
    ) -> KnowledgeItemResponse:
        item = KnowledgeItem(
            title=payload.title,
            content=payload.content,
            domain_code=payload.domain_code,
            status=payload.status,
            source_expert_id=payload.source_expert_id,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return KnowledgeItemResponse.model_validate(item)

    def get_knowledge_item(self, item_id: int) -> KnowledgeItemResponse:
        item = self.db.get(KnowledgeItem, item_id)
        if item is None:
            raise LookupError("Knowledge item not found.")
        return KnowledgeItemResponse.model_validate(item)

    def update_knowledge_item(
        self,
        item_id: int,
        payload: KnowledgeItemUpdateRequest,
    ) -> KnowledgeItemResponse:
        item = self.db.get(KnowledgeItem, item_id)
        if item is None:
            raise LookupError("Knowledge item not found.")

        updates = payload.model_dump(exclude_unset=True)
        for field_name, value in updates.items():
            setattr(item, field_name, value)

        self.db.commit()
        self.db.refresh(item)
        return KnowledgeItemResponse.model_validate(item)

    def delete_knowledge_item(self, item_id: int) -> None:
        item = self.db.get(KnowledgeItem, item_id)
        if item is None:
            raise LookupError("Knowledge item not found.")
        self.db.delete(item)
        self.db.commit()

    def list_knowledge_items(
        self,
        *,
        domain: str | None,
        status: str | None,
        skip: int,
        limit: int,
    ) -> KnowledgeItemListResponse:
        filters = []
        if domain:
            filters.append(KnowledgeItem.domain_code == domain)
        if status:
            filters.append(KnowledgeItem.status == status)

        count_statement = select(func.count()).select_from(KnowledgeItem)
        items_statement = select(KnowledgeItem).order_by(KnowledgeItem.id.asc())

        for criterion in filters:
            count_statement = count_statement.where(criterion)
            items_statement = items_statement.where(criterion)

        total = self.db.execute(count_statement).scalar_one()
        items = self.db.execute(items_statement.offset(skip).limit(limit)).scalars().all()

        return KnowledgeItemListResponse(
            items=[KnowledgeItemResponse.model_validate(item) for item in items],
            total=total,
            skip=skip,
            limit=limit,
        )

    def get_knowledge_context_for_query(
        self,
        *,
        query: str,
        domain_codes: list[str] | None = None,
        limit: int = 3,
    ) -> UexKnowledgeContextResponse:
        min_vector_score = 0.18
        requested_domains = {code.strip() for code in (domain_codes or []) if code and code.strip()}
        query_tokens = self._tokenize_text(query)

        items = self.db.execute(
            select(KnowledgeItem).where(KnowledgeItem.status == "published")
        ).scalars().all()

        vector_matches = self.vector_retrieval_service.rank_documents(
            query=query,
            documents=[
                VectorRetrievalDocument(
                    identifier=item.id,
                    content=" ".join(
                        part.strip()
                        for part in [item.domain_code or "", item.title or "", item.content or ""]
                        if part and part.strip()
                    ),
                )
                for item in items
            ],
            limit=max(limit * 4, limit),
        )
        vector_scores = {match.identifier: match.score for match in vector_matches}

        ranked_items: list[tuple[float, float, KnowledgeItem]] = []
        for item in items:
            score = 0.0
            vector_score = vector_scores.get(item.id, 0.0)
            domain_relevant = False
            has_overlap_signal = False
            has_strong_vector_signal = vector_score >= min_vector_score

            if requested_domains and item.domain_code in requested_domains and vector_score >= 0.08:
                score += 5.0
                domain_relevant = True

            score += 10.0 * vector_score

            item_tokens = self._tokenize_text(f"{item.domain_code} {item.title} {item.content}")
            overlap = query_tokens & item_tokens
            if overlap:
                score += float(len(overlap))
                has_overlap_signal = True

            if not domain_relevant and not has_overlap_signal and not has_strong_vector_signal:
                continue

            if domain_relevant or has_overlap_signal:
                content_length_bonus = min(len((item.content or "").strip()) / 1600.0, 0.15)
                score += content_length_bonus

            ranked_items.append((score, vector_score, item))

        ranked_items.sort(key=lambda row: (-row[0], -row[1], row[2].id))
        selected_items: list[KnowledgeItem] = []
        for score, vector_score, item in ranked_items:
            item_tokens = self._tokenize_text(f"{item.domain_code} {item.title} {item.content}")
            overlap = query_tokens & item_tokens
            has_explicit_signal = bool(overlap) or bool(
                requested_domains and item.domain_code in requested_domains and vector_score >= 0.14
            )
            has_strong_vector_only_signal = not has_explicit_signal and vector_score >= 0.24

            if requested_domains and item.domain_code not in requested_domains:
                if len(overlap) < 2:
                    continue
                if vector_score < 0.22:
                    continue

            if requested_domains and item.domain_code not in requested_domains and not overlap:
                continue

            if has_explicit_signal and score >= 1.4:
                selected_items.append(item)
            elif has_strong_vector_only_signal and score >= 2.4:
                selected_items.append(item)

            if len(selected_items) >= limit:
                break

        if not selected_items:
            return UexKnowledgeContextResponse(content="", items=[])

        content_blocks = []
        for item in selected_items:
            title = (item.title or "").strip()
            content = (item.content or "").strip()
            if not content:
                continue
            if title:
                content_blocks.append(f"{title}: {content}")
            else:
                content_blocks.append(content)

        return UexKnowledgeContextResponse(
            content="\n\n".join(content_blocks),
            items=[KnowledgeItemResponse.model_validate(item) for item in selected_items],
        )

    def get_knowledge_context(self, *, limit: int = 3) -> UexKnowledgeContextResponse:
        statement = (
            select(KnowledgeItem)
            .where(KnowledgeItem.status == "published")
            .order_by(KnowledgeItem.id.asc())
            .limit(limit)
        )
        items = self.db.execute(statement).scalars().all()
        content = "\n\n".join(item.content.strip() for item in items if item.content.strip())
        return UexKnowledgeContextResponse(
            content=content,
            items=[KnowledgeItemResponse.model_validate(item) for item in items],
        )
