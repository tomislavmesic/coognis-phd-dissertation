from functools import lru_cache

from app.core.config import settings
from app.schemas.synapse import SynapseInferenceResult
from app.services.synapse.inference import SynapseInferenceService
from app.services.synapse.model_loader import SynapseModelRegistry
from app.services.synapse.preprocessing import SynapsePreprocessor


class SynapseService:
    """Service boundary for the SYNAPSE inference pipeline."""

    def __init__(self, model_dir: str) -> None:
        registry = SynapseModelRegistry(model_dir)
        registry.load()
        self.inference_service = SynapseInferenceService(
            registry=registry,
            preprocessor=SynapsePreprocessor(),
        )

    def infer(self, content: str) -> SynapseInferenceResult:
        return self.inference_service.infer(content)


@lru_cache
def get_synapse_service() -> SynapseService:
    return SynapseService(model_dir=settings.synapse_model_dir)


def get_synapse_inference_service() -> SynapseInferenceService:
    return get_synapse_service().inference_service
