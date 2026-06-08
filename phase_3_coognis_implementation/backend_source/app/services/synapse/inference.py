from app.core.logging import get_logger, log_event
from app.schemas.synapse import SynapseInferenceResult
from app.services.synapse.predictor import SynapsePredictor

logger = get_logger(__name__)


class SynapseInferenceService:
    """Application service for SYNAPSE inference."""

    def __init__(self, registry, preprocessor) -> None:
        self.predictor = SynapsePredictor(registry, preprocessor)

    def infer(self, raw_text: str) -> SynapseInferenceResult:
        result = self.predictor.predict(raw_text)
        validated = SynapseInferenceResult.model_validate(result)
        log_event(
            logger,
            "synapse_inference_completed",
            model_version=validated.model_version,
            mbti_type=validated.mbti_type,
            confidence=validated.confidence,
            profile_status=validated.profile_status,
            dimensions=validated.dimensions,
            raw_text_length=len(raw_text),
        )
        return validated
