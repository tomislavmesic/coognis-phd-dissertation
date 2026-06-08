import json
from pathlib import Path

import joblib

from app.core.config import settings
from app.services.synapse.artifact_fetcher import ensure_synapse_artifacts


class SynapseModelRegistryError(RuntimeError):
    """Base error for SYNAPSE model registry failures."""


class SynapseModelArtifactMissingError(FileNotFoundError, SynapseModelRegistryError):
    """Raised when a required SYNAPSE model artifact is missing."""


class SynapseModelRegistry:
    REQUIRED_MODEL_FILES = {
        "EI": "ei_model.joblib",
        "SN": "sn_model.joblib",
        "TF": "tf_model.joblib",
        "JP": "jp_model.joblib",
    }
    REQUIRED_PIPELINE_FILES = {
        "vectorizer": "vectorizer.joblib",
        "tfidf_transformer": "tfidf_transformer.joblib",
        "feature_names": "feature_names.joblib",
    }

    def __init__(self, model_dir: str):
        self.model_dir = Path(model_dir)
        self.manifest_path = self.model_dir / "manifest.json"
        self.models = {}
        self.vectorizer = None
        self.tfidf_transformer = None
        self.feature_names = None
        self.model_version = "unknown"

    def load(self) -> None:
        if settings.synapse_model_auto_download and settings.synapse_model_download_base_url:
            ensure_synapse_artifacts(
                model_dir=self.model_dir,
                base_url=settings.synapse_model_download_base_url,
            )

        self._validate_required_files()
        manifest = self._load_manifest()
        self.model_version = manifest.get("version", "unknown")

        self.vectorizer = joblib.load(self.model_dir / self.REQUIRED_PIPELINE_FILES["vectorizer"])
        self.tfidf_transformer = joblib.load(
            self.model_dir / self.REQUIRED_PIPELINE_FILES["tfidf_transformer"]
        )
        self.feature_names = joblib.load(self.model_dir / self.REQUIRED_PIPELINE_FILES["feature_names"])

        for key, filename in self.REQUIRED_MODEL_FILES.items():
            path = self.model_dir / filename
            self.models[key] = joblib.load(path)

    def get_model(self, key: str):
        if key not in self.REQUIRED_MODEL_FILES:
            raise KeyError(f"Unknown SYNAPSE model key: {key}")
        if key not in self.models:
            raise SynapseModelRegistryError(
                f"SYNAPSE model '{key}' has not been loaded yet."
            )
        return self.models[key]

    def get_vectorizer(self):
        if self.vectorizer is None:
            raise SynapseModelRegistryError("SYNAPSE vectorizer has not been loaded yet.")
        return self.vectorizer

    def get_tfidf_transformer(self):
        if self.tfidf_transformer is None:
            raise SynapseModelRegistryError("SYNAPSE TF-IDF transformer has not been loaded yet.")
        return self.tfidf_transformer

    def get_feature_names(self):
        if self.feature_names is None:
            raise SynapseModelRegistryError("SYNAPSE feature names have not been loaded yet.")
        return self.feature_names

    def _load_manifest(self) -> dict:
        try:
            return json.loads(self.manifest_path.read_text())
        except json.JSONDecodeError as exc:
            raise SynapseModelRegistryError(
                f"Invalid SYNAPSE manifest JSON: {self.manifest_path}"
            ) from exc

    def _validate_required_files(self) -> None:
        if not self.model_dir.exists():
            raise SynapseModelArtifactMissingError(
                f"SYNAPSE model directory does not exist: {self.model_dir}"
            )

        missing_files = [
            str(path)
            for path in (
                [self.manifest_path]
                + [
                    self.model_dir / filename
                    for filename in self.REQUIRED_PIPELINE_FILES.values()
                ]
                + [
                    self.model_dir / filename
                    for filename in self.REQUIRED_MODEL_FILES.values()
                ]
            )
            if not path.exists()
        ]

        if missing_files:
            missing_list = ", ".join(missing_files)
            raise SynapseModelArtifactMissingError(
                f"Missing required SYNAPSE model artifacts: {missing_list}"
            )
