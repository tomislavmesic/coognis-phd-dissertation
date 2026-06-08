from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger, log_event
from app.models.synapse_inference_run import SynapseInferenceRun
from app.schemas.synapse import (
    SynapseInferRequest,
    SynapseProfileUpdateRequest,
    SynapseRunResponse,
)

logger = get_logger(__name__)


class SynapseProfileService:
    """Persistence layer for SYNAPSE inference runs and latest profiles."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_inference_run(
        self,
        payload: SynapseInferRequest | SynapseProfileUpdateRequest,
        inference_result,
    ) -> SynapseRunResponse:
        run = SynapseInferenceRun(
            subject_type=payload.subject_type,
            subject_id=payload.subject_id,
            mode=payload.mode,
            content=payload.content,
            mbti_type=inference_result.mbti_type,
            dimensions={
                key: value.model_dump()
                for key, value in inference_result.dimensions.items()
            },
            confidence=inference_result.confidence,
            model_version=inference_result.model_version,
            profile_status=inference_result.profile_status,
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        log_event(
            logger,
            "synapse_inference_run_persisted",
            run_id=run.id,
            subject_type=run.subject_type,
            subject_id=run.subject_id,
            mode=run.mode,
            mbti_type=run.mbti_type,
            confidence=run.confidence,
            model_version=run.model_version,
        )
        return SynapseRunResponse.model_validate(run)

    def get_latest_profile(self, subject_type: str, subject_id: int) -> SynapseRunResponse | None:
        statement = (
            select(SynapseInferenceRun)
            .where(SynapseInferenceRun.subject_type == subject_type)
            .where(SynapseInferenceRun.subject_id == subject_id)
            .order_by(SynapseInferenceRun.created_at.desc(), SynapseInferenceRun.id.desc())
            .limit(1)
        )
        run = self.db.execute(statement).scalar_one_or_none()
        if run is None:
            return None
        return SynapseRunResponse.model_validate(run)

    def get_run(self, run_id: int) -> SynapseRunResponse | None:
        run = self.db.get(SynapseInferenceRun, run_id)
        if run is None:
            return None
        return SynapseRunResponse.model_validate(run)
