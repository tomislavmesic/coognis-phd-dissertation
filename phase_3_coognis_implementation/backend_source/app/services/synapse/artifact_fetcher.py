from __future__ import annotations

from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen


class SynapseArtifactDownloadError(RuntimeError):
    """Raised when required SYNAPSE artifacts cannot be downloaded."""


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


def required_synapse_artifact_names() -> list[str]:
    return [
        "manifest.json",
        *REQUIRED_PIPELINE_FILES.values(),
        *REQUIRED_MODEL_FILES.values(),
    ]


def ensure_synapse_artifacts(
    *,
    model_dir: str | Path,
    base_url: str | None,
    force: bool = False,
) -> list[str]:
    if not base_url:
        raise SynapseArtifactDownloadError("SYNAPSE_MODEL_DOWNLOAD_BASE_URL is not configured.")

    target_dir = Path(model_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    normalized_base_url = base_url.rstrip("/")
    downloaded_files: list[str] = []

    for filename in required_synapse_artifact_names():
        destination = target_dir / filename
        if destination.exists() and not force:
            continue

        source_url = f"{normalized_base_url}/{quote(filename)}"
        try:
            with urlopen(source_url) as response:
                payload = response.read()
        except Exception as exc:  # pragma: no cover - depends on external storage
            raise SynapseArtifactDownloadError(
                f"Unable to download SYNAPSE artifact '{filename}' from {source_url}."
            ) from exc

        tmp_destination = destination.with_suffix(f"{destination.suffix}.tmp")
        tmp_destination.write_bytes(payload)
        tmp_destination.replace(destination)
        downloaded_files.append(filename)

    return downloaded_files
